# Copyright (C)  2024 CloudCommune.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_log import log
from six.moves.urllib import parse as urlparse

from ceilometer.network.statistics import driver
from ceilometer.network.statistics.cloudcommunesdn import client
from ceilometer import neutron_client

LOG = log.getLogger(__name__)


class CloudCommuneSDNDriver(driver.Driver):
    """Driver of network info collector from CloudCommuneSDN.

    This driver uses resources in "pipeline.yaml".
    Resource requires below conditions:

    * resource is url
    * scheme is "cloudcommunesdn"
    """
    def _get_cache_key(self, endpoint, meter_name):
        s = urlparse.urlparse(endpoint)
        keys = ['network.statistics.cloudcommunesdn']
        keys.extend(s.netloc.split(":"))
        keys.append(meter_name.split(".")[0])
        cache_key = '.'.join(keys)
        return cache_key

    def _prepare_cache(self, endpoint, params, cache, meter_name):
        ip6 = meter_name.startswith("ip6")
        cache_key = self._get_cache_key(endpoint, meter_name)

        if cache_key in cache:
            return cache[cache_key]

        nc = neutron_client.Client(self.conf)
        yc = client.Client(self.conf, endpoint)
        data = []

        cache[cache_key] = data

        addr_port_map = dict()
        ports = []
        if ip6:
            ports = nc.port_get_all()
        else:
            ext_networks = nc.get_external_networks()
            for ext_network in ext_networks:
                ext_ports = nc.get_network_ports(ext_network["id"])
                ports.extend(ext_ports)

        for port in ports:
            fixed_ips = port['fixed_ips']
            if fixed_ips is None:
                break
            addr_port_map.update(
                dict((fixed_ip['ip_address'], port) for fixed_ip in
                     fixed_ips if fixed_ip['ip_address'] is not None))

        path = '/ipv6/stat' if ip6 else '/statistics/floatingip'
        ip_statistics = yc.networks.get_ip_statistics(path=path)
        if ip_statistics is None:
            ip_statistics = []
        ip_key = 'ipaddr' if ip6 else 'fip_address'

        for ip_stat in ip_statistics:
            ip_stat[ip_key] = ip_stat[ip_key].lower()
            ip_addr = ip_stat[ip_key]
            if ip_addr is None:
                continue
            port_info = addr_port_map.get(ip_addr, None)
            if port_info is None:
                LOG.warning("no port found in neutron: %s , skipped.",
                            str(ip_addr))
                continue
            data.append((port_info, ip_stat))

        return cache[cache_key]

    def _get_sample_extractor(self, meter_name):
        if meter_name.startswith('ip'):
            return self._get_ip_sample_data
        else:
            return None

    def get_sample_data(self, meter_name, parse_url, params, cache):
        sample_extractor = self._get_sample_extractor(meter_name)
        if sample_extractor is None:
            # The extractor for this meter is no implemented or the API
            # doesn't have method to get this meter.
            return
        return sample_extractor(meter_name, parse_url, params, cache)

    def _get_extractor(self, meter_name):
        method_name = '_' + meter_name.replace('.', '_')
        return getattr(self, method_name, None)

    def _get_ip_sample_data(self, meter_name, parse_url, params, cache):
        """Functions to get sample data for meters:

        ip.floating.incoming.bytes
        ip.floating.incoming.packets
        ip.floating.outgoing.bytes
        ip.floating.outgoing.packets
        ip6.incoming.bytes
        ip6.incoming.packets
        ip6.outgoing.bytes
        ip6.outgoing.packets
        """

        parts = urlparse.ParseResult(params.get('scheme', ['http'])[0],
                                     parse_url.netloc,
                                     parse_url.path,
                                     None,
                                     None,
                                     None)
        endpoint = urlparse.urlunparse(parts)
        extractor = self._get_extractor(meter_name)
        if extractor is None:
            return
        data = self._prepare_cache(endpoint, params, cache, meter_name)
        for stat in data:
            sample = self._get_sample(meter_name, extractor, *stat)
            if sample is not None:
                yield sample

    def _get_sample(self, meter_name, extractor, port_info, ip_stat):
        if meter_name.startswith('ip6'):
            return self._get_ip6_sample(extractor, port_info, ip_stat)
        else:
            return self._get_fip_sample(extractor, port_info, ip_stat)

    def _get_fip_sample(self, extractor, port_info, fip_stat):
        # rid = port_info['id']
        rid = fip_stat['eip_address']
        resource_meta = (self._get_fip_resource_meta(port_info, fip_stat))
        return extractor(fip_stat, rid, resource_meta)

    @staticmethod
    def _get_fip_resource_meta(port_info, fip_stat):
        resource_meta = {}
        resource_meta.update(port_info)
        resource_meta['eip_address'] = fip_stat['eip_address']
        resource_meta['duration'] = fip_stat['duration']
        resource_meta['project_id'] = port_info['tenant_id']
        return resource_meta

    def _get_ip6_sample(self, extractor, port_info, ipaddr):
        # rid = port_info['id']
        ip = ipaddr['ipaddr']
        resource_meta = (self._get_ip6_resource_meta(port_info, ipaddr))
        return extractor(ipaddr, ip, resource_meta)

    @staticmethod
    def _get_ip6_resource_meta(port_info, ipstat):
        resource_meta = {}
        resource_meta.update(port_info)
        resource_meta['ipaddr'] = ipstat['ipaddr']
        resource_meta['duration'] = ipstat['duration']
        resource_meta['project_id'] = port_info['tenant_id']
        resource_meta['domain'] = ipstat['domain']
        return resource_meta

    @staticmethod
    def _ip_floating_incoming_packets(statistic, resource_id, resource_meta):
        """The VSR transmit_pkts is the vm incoming_packets."""
        return int(statistic['transmit_pkts']), resource_id, resource_meta

    @staticmethod
    def _ip_floating_outgoing_packets(statistic, resource_id, resource_meta):
        """The VSR receive_pkts is the vm outgoing_packets."""
        return int(statistic['receive_pkts']), resource_id, resource_meta

    @staticmethod
    def _ip_floating_incoming_bytes(statistic, resource_id, resource_meta):
        """The VSR transmit_bytes is the vm incoming_bytes."""
        return int(statistic['transmit_bytes']), resource_id, resource_meta

    @staticmethod
    def _ip_floating_outgoing_bytes(statistic, resource_id, resource_meta):
        """The VSR receive_bytes is the vm outgoing_bytes."""
        return int(statistic['receive_bytes']), resource_id, resource_meta

    # Because ip floating incomming and outgoing is reversed, and has many data
    # in our production environment, This issue is only fixed in ipv6
    _ip6_incoming_packets = _ip_floating_outgoing_packets
    _ip6_outgoing_packets = _ip_floating_incoming_packets
    _ip6_incoming_bytes = _ip_floating_outgoing_bytes
    _ip6_outgoing_bytes = _ip_floating_incoming_bytes
