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

import mock
from oslo_config import fixture as fixture_config
from oslotest import base
from six.moves.urllib import parse as urlparse

from ceilometer.network.statistics.cloudcommunesdn import driver
from ceilometer import service


class TestCloudCommuneSDNDriver(base.BaseTestCase):

    def setUp(self):
        super(TestCloudCommuneSDNDriver, self).setUp()

        mock.patch('ceilometer.neutron_client'
                   '.Client.get_external_networks',
                   return_value=self.fake_external_networks()).start()

        mock.patch('ceilometer.neutron_client'
                   '.Client.get_network_ports',
                   return_value=self.fake_network_ports("foo_network_id")
                   ).start()

        conf = service.prepare_service([], [])
        self.CONF = self.useFixture(fixture_config.Config(conf)).conf

        self.driver = driver.CloudCommuneSDNDriver(self.CONF)
        self.parse_url = urlparse.ParseResult('cloudcommunesdn',
                                              '127.0.0.1:8143',
                                              '/', None, None, None)
        self.params = {'password': ['admin'],
                       'scheme': ['http'],
                       'username': ['admin'],
                       'verify_ssl': ['false'],
                       'resource': ['if_stats_list']}

    @staticmethod
    def fake_external_networks():
        return [{"provider:physical_network": "public",
                 "ipv6_address_scope": None,
                 "revision_number": 6,
                 "port_security_enabled": None,
                 "mtu": 1500,
                 "id": "foo_network_id",
                 "router:external": True,
                 "availability_zone_hints": [],
                 "availability_zones": ["nova"],
                 "provider:segmentation_id": None,
                 "ipv4_address_scope": None,
                 "shared": True,
                 "project_id": "foo_project_id",
                 "status": "ACTIVE",
                 "subnets": ["foo_subnet_1", "foo_subnet_2"],
                 "description": "",
                 "updated_at": "2017-04-01T00:00:00Z",
                 "is_default": False,
                 "qos_policy_id": None,
                 "name": "external_network",
                 "admin_state_up": True,
                 "tenant_id": "foo_tenant_id",
                 "created_at": "2017-04-01T00:00:00Z",
                 "provider:network_type": "flat"}]

    @staticmethod
    def fake_network_ports(network_id):
        return [{"status": "ACTIVE",
                 "binding:host_id": "foo-compute-1",
                 "description": "",
                 "allowed_address_pairs": [],
                 "tags": [],
                 "extra_dhcp_opts": [],
                 "updated_at": "2017-04-01T09:00:00Z",
                 "device_owner": "compute:nova",
                 "revision_number": 9,
                 "port_security_enabled": True,
                 "binding:profile": {},
                 "fixed_ips": [{
                     "subnet_id": "foo_subnet_1",
                     "ip_address": "10.10.10.2"}],
                 "id": "foo_port_id_1",
                 "security_groups": ["foo_security_group_uuid"],
                 "device_id": "foo_device_id_1",
                 "name": "",
                 "admin_state_up": True,
                 "network_id": "foo_tenant_id",
                 "tenant_id": "foo_tenant_id",
                 "binding:vif_details": {
                     "port_filter": True,
                     "ovs_hybrid_plug": True},
                 "binding:vnic_type": "normal",
                 "binding:vif_type": "ovs",
                 "qos_policy_id": None,
                 "mac_address": "fa:16:3e:ee:dd:aa",
                 "project_id": "foo_project_id",
                 "created_at": "2017-04-01T09:00:00Z"
                 },
                {"status": "ACTIVE",
                 "binding:host_id": "foo-compute-2",
                 "description": "",
                 "allowed_address_pairs": [],
                 "tags": [],
                 "extra_dhcp_opts": [],
                 "updated_at": "2017-04-01T09:00:00Z",
                 "device_owner": "compute:nova",
                 "revision_number": 9,
                 "port_security_enabled": True,
                 "binding:profile": {},
                 "fixed_ips": [{
                     "subnet_id": "foo_subnet_2",
                     "ip_address": "10.10.10.3"}],
                 "id": "foo_port_id_2",
                 "security_groups": ["foo_security_group_uuid"],
                 "device_id": "foo_device_id_2",
                 "name": "",
                 "admin_state_up": True,
                 "network_id": "foo_tenant_id",
                 "tenant_id": "foo_tenant_id",
                 "binding:vif_details": {
                     "port_filter": True,
                     "ovs_hybrid_plug": True},
                 "binding:vnic_type": "normal",
                 "binding:vif_type": "ovs",
                 "qos_policy_id": None,
                 "mac_address": "fa:16:3e:ee:dd:bb",
                 "project_id": "foo_project_id",
                 "created_at": "2017-04-01T09:00:00Z"}]

    @staticmethod
    def fake_ip_statistics():
        return [{"fip_address": "10.10.10.2",
                 "eip_address": "100.100.100.2",
                 "receive_bytes": 100,
                 "receive_pkts": 2,
                 "transmit_bytes": 50,
                 "transmit_pkts": 1,
                 "timestamp": "2016-09-01 09:00:00",
                 "duration": 120
                 },
                {
                "fip_address": "10.10.10.3",
                "eip_address": "100.100.100.3",
                "receive_bytes": 200,
                "receive_pkts": 2,
                "transmit_bytes": 70,
                "transmit_pkts": 1,
                "timestamp": "2016-09-01 09:00:00",
                "duration": 120
                }]

    def _test_meter(self, meter_name, expected, fake_ip_statistics=None):
        if not fake_ip_statistics:
            fake_ip_statistics = self.fake_ip_statistics()
        with mock.patch('ceilometer.network.'
                        'statistics.cloudcommunesdn.'
                        'client.CloudCommuneSDNAPIClient.'
                        'get_ip_statistics',
                        return_value=fake_ip_statistics):
            samples = self.driver.get_sample_data(meter_name, self.parse_url,
                                                  self.params, {})
            self.assertEqual(expected, [s for s in samples])

    def test_ip_floating_incoming_packets(self):
        expected = [(1,
                     '100.100.100.2',
                     {'admin_state_up': True,
                      'allowed_address_pairs': [],
                      'binding:host_id': 'foo-compute-1',
                      'binding:profile': {},
                      'binding:vif_details': {
                          'ovs_hybrid_plug': True,
                          'port_filter': True},
                      'binding:vif_type': 'ovs',
                      'binding:vnic_type': 'normal',
                      'created_at': '2017-04-01T09:00:00Z',
                      'description': '',
                      'device_id': 'foo_device_id_1',
                      'device_owner': 'compute:nova',
                      'duration': 120,
                      'eip_address': '100.100.100.2',
                      'extra_dhcp_opts': [],
                      'fixed_ips': [{
                          'ip_address': '10.10.10.2',
                          'subnet_id': 'foo_subnet_1'}],
                      'id': 'foo_port_id_1',
                      'mac_address': 'fa:16:3e:ee:dd:aa',
                      'name': '',
                      'network_id': 'foo_tenant_id',
                      'port_security_enabled': True,
                      'project_id': 'foo_tenant_id',
                      'qos_policy_id': None,
                      'revision_number': 9,
                      'security_groups': ['foo_security_group_uuid'],
                      'status': 'ACTIVE',
                      'tags': [],
                      'tenant_id': 'foo_tenant_id',
                      'updated_at': '2017-04-01T09:00:00Z'}),
                    (1,
                     '100.100.100.3',
                     {'admin_state_up': True,
                      'allowed_address_pairs': [],
                      'binding:host_id': 'foo-compute-2',
                      'binding:profile': {},
                      'binding:vif_details': {
                          'ovs_hybrid_plug': True,
                          'port_filter': True},
                      'binding:vif_type': 'ovs',
                      'binding:vnic_type': 'normal',
                      'created_at': '2017-04-01T09:00:00Z',
                      'description': '',
                      'device_id': 'foo_device_id_2',
                      'device_owner': 'compute:nova',
                      'duration': 120,
                      'eip_address': '100.100.100.3',
                      'extra_dhcp_opts': [],
                      'fixed_ips': [{
                          'ip_address': '10.10.10.3',
                          'subnet_id': 'foo_subnet_2'}],
                      'id': 'foo_port_id_2',
                      'mac_address': 'fa:16:3e:ee:dd:bb',
                      'name': '',
                      'network_id': 'foo_tenant_id',
                      'port_security_enabled': True,
                      'project_id': 'foo_tenant_id',
                      'qos_policy_id': None,
                      'revision_number': 9,
                      'security_groups': ['foo_security_group_uuid'],
                      'status': 'ACTIVE',
                      'tags': [],
                      'tenant_id': 'foo_tenant_id',
                      'updated_at': '2017-04-01T09:00:00Z'})]
        self._test_meter('ip.floating.incoming.packets', expected)

    def test_ip_floating_outgoing_packets(self):
        expected = [(2,
                     '100.100.100.2',
                     {'admin_state_up': True,
                      'allowed_address_pairs': [],
                      'binding:host_id': 'foo-compute-1',
                      'binding:profile': {},
                      'binding:vif_details': {
                          'ovs_hybrid_plug': True,
                          'port_filter': True},
                      'binding:vif_type': 'ovs',
                      'binding:vnic_type': 'normal',
                      'created_at': '2017-04-01T09:00:00Z',
                      'description': '',
                      'device_id': 'foo_device_id_1',
                      'device_owner': 'compute:nova',
                      'duration': 120,
                      'eip_address': '100.100.100.2',
                      'extra_dhcp_opts': [],
                      'fixed_ips': [{
                          'ip_address': '10.10.10.2',
                          'subnet_id': 'foo_subnet_1'}],
                      'id': 'foo_port_id_1',
                      'mac_address': 'fa:16:3e:ee:dd:aa',
                      'name': '',
                      'network_id': 'foo_tenant_id',
                      'port_security_enabled': True,
                      'project_id': 'foo_tenant_id',
                      'qos_policy_id': None,
                      'revision_number': 9,
                      'security_groups': ['foo_security_group_uuid'],
                      'status': 'ACTIVE',
                      'tags': [],
                      'tenant_id': 'foo_tenant_id',
                      'updated_at': '2017-04-01T09:00:00Z'}),
                    (2,
                     '100.100.100.3',
                     {'admin_state_up': True,
                      'allowed_address_pairs': [],
                      'binding:host_id': 'foo-compute-2',
                      'binding:profile': {},
                      'binding:vif_details': {
                          'ovs_hybrid_plug': True,
                          'port_filter': True},
                      'binding:vif_type': 'ovs',
                      'binding:vnic_type': 'normal',
                      'created_at': '2017-04-01T09:00:00Z',
                      'description': '',
                      'device_id': 'foo_device_id_2',
                      'device_owner': 'compute:nova',
                      'duration': 120,
                      'eip_address': '100.100.100.3',
                      'extra_dhcp_opts': [],
                      'fixed_ips': [{
                          'ip_address': '10.10.10.3',
                          'subnet_id': 'foo_subnet_2'}],
                      'id': 'foo_port_id_2',
                      'mac_address': 'fa:16:3e:ee:dd:bb',
                      'name': '',
                      'network_id': 'foo_tenant_id',
                      'port_security_enabled': True,
                      'project_id': 'foo_tenant_id',
                      'qos_policy_id': None,
                      'revision_number': 9,
                      'security_groups': ['foo_security_group_uuid'],
                      'status': 'ACTIVE',
                      'tags': [],
                      'tenant_id': 'foo_tenant_id',
                      'updated_at': '2017-04-01T09:00:00Z'})]
        self._test_meter('ip.floating.outgoing.packets', expected)

    def test_ip_floating_incoming_bytes(self):
        expected = [(50,
                     '100.100.100.2',
                     {'admin_state_up': True,
                      'allowed_address_pairs': [],
                      'binding:host_id': 'foo-compute-1',
                      'binding:profile': {},
                      'binding:vif_details': {
                          'ovs_hybrid_plug': True,
                          'port_filter': True},
                      'binding:vif_type': 'ovs',
                      'binding:vnic_type': 'normal',
                      'created_at': '2017-04-01T09:00:00Z',
                      'description': '',
                      'device_id': 'foo_device_id_1',
                      'device_owner': 'compute:nova',
                      'duration': 120,
                      'eip_address': '100.100.100.2',
                      'extra_dhcp_opts': [],
                      'fixed_ips': [{
                          'ip_address': '10.10.10.2',
                          'subnet_id': 'foo_subnet_1'}],
                      'id': 'foo_port_id_1',
                      'mac_address': 'fa:16:3e:ee:dd:aa',
                      'name': '',
                      'network_id': 'foo_tenant_id',
                      'port_security_enabled': True,
                      'project_id': 'foo_tenant_id',
                      'qos_policy_id': None,
                      'revision_number': 9,
                      'security_groups': ['foo_security_group_uuid'],
                      'status': 'ACTIVE',
                      'tags': [],
                      'tenant_id': 'foo_tenant_id',
                      'updated_at': '2017-04-01T09:00:00Z'}),
                    (70,
                     '100.100.100.3',
                     {'admin_state_up': True,
                      'allowed_address_pairs': [],
                      'binding:host_id': 'foo-compute-2',
                      'binding:profile': {},
                      'binding:vif_details': {
                          'ovs_hybrid_plug': True,
                          'port_filter': True},
                      'binding:vif_type': 'ovs',
                      'binding:vnic_type': 'normal',
                      'created_at': '2017-04-01T09:00:00Z',
                      'description': '',
                      'device_id': 'foo_device_id_2',
                      'device_owner': 'compute:nova',
                      'duration': 120,
                      'eip_address': '100.100.100.3',
                      'extra_dhcp_opts': [],
                      'fixed_ips': [{
                          'ip_address': '10.10.10.3',
                          'subnet_id': 'foo_subnet_2'}],
                      'id': 'foo_port_id_2',
                      'mac_address': 'fa:16:3e:ee:dd:bb',
                      'name': '',
                      'network_id': 'foo_tenant_id',
                      'port_security_enabled': True,
                      'project_id': 'foo_tenant_id',
                      'qos_policy_id': None,
                      'revision_number': 9,
                      'security_groups': ['foo_security_group_uuid'],
                      'status': 'ACTIVE',
                      'tags': [],
                      'tenant_id': 'foo_tenant_id',
                      'updated_at': '2017-04-01T09:00:00Z'})]
        self._test_meter('ip.floating.incoming.bytes', expected)

    def test_ip_floating_outgoing_bytes(self):
        expected = [(100,
                     '100.100.100.2',
                     {'admin_state_up': True,
                      'allowed_address_pairs': [],
                      'binding:host_id': 'foo-compute-1',
                      'binding:profile': {},
                      'binding:vif_details': {
                          'ovs_hybrid_plug': True,
                          'port_filter': True},
                      'binding:vif_type': 'ovs',
                      'binding:vnic_type': 'normal',
                      'created_at': '2017-04-01T09:00:00Z',
                      'description': '',
                      'device_id': 'foo_device_id_1',
                      'device_owner': 'compute:nova',
                      'duration': 120,
                      'eip_address': '100.100.100.2',
                      'extra_dhcp_opts': [],
                      'fixed_ips': [{
                          'ip_address': '10.10.10.2',
                          'subnet_id': 'foo_subnet_1'}],
                      'id': 'foo_port_id_1',
                      'mac_address': 'fa:16:3e:ee:dd:aa',
                      'name': '',
                      'network_id': 'foo_tenant_id',
                      'port_security_enabled': True,
                      'project_id': 'foo_tenant_id',
                      'qos_policy_id': None,
                      'revision_number': 9,
                      'security_groups': ['foo_security_group_uuid'],
                      'status': 'ACTIVE',
                      'tags': [],
                      'tenant_id': 'foo_tenant_id',
                      'updated_at': '2017-04-01T09:00:00Z'}),
                    (200,
                     '100.100.100.3',
                     {'admin_state_up': True,
                      'allowed_address_pairs': [],
                      'binding:host_id': 'foo-compute-2',
                      'binding:profile': {},
                      'binding:vif_details': {
                          'ovs_hybrid_plug': True,
                          'port_filter': True},
                      'binding:vif_type': 'ovs',
                      'binding:vnic_type': 'normal',
                      'created_at': '2017-04-01T09:00:00Z',
                      'description': '',
                      'device_id': 'foo_device_id_2',
                      'device_owner': 'compute:nova',
                      'duration': 120,
                      'eip_address': '100.100.100.3',
                      'extra_dhcp_opts': [],
                      'fixed_ips': [{
                          'ip_address': '10.10.10.3',
                          'subnet_id': 'foo_subnet_2'}],
                      'id': 'foo_port_id_2',
                      'mac_address': 'fa:16:3e:ee:dd:bb',
                      'name': '',
                      'network_id': 'foo_tenant_id',
                      'port_security_enabled': True,
                      'project_id': 'foo_tenant_id',
                      'qos_policy_id': None,
                      'revision_number': 9,
                      'security_groups': ['foo_security_group_uuid'],
                      'status': 'ACTIVE',
                      'tags': [],
                      'tenant_id': 'foo_tenant_id',
                      'updated_at': '2017-04-01T09:00:00Z'})]
        self._test_meter('ip.floating.outgoing.bytes', expected)
