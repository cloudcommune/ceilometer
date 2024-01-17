#
# Copyright 2012 eNovance <licensing@enovance.com>
# Copyright 2012 Red Hat, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import psutil
import re
import subprocess

from ceilometer.agent import plugin_base
from ceilometer import sample
from oslo_log import log


LOG = log.getLogger(__name__)


class _Base(plugin_base.PollsterBase):

    keys = ['top']
    meter_type = sample.TYPE_GAUGE
    meter_unit = "load"

    @property
    def default_discovery(self):
        return 'host_discovery'

    def get_samples(self, manager, cache, resources):
        try:
            LOG.debug("in host: %s", self.meter_name)
            resource_metadata = {'name': self.conf.host,
                                 'hostname': self.conf.host}
            for resource in resources:
                cache_key = ".".join(['top', resource])
                if cache_key not in cache:
                    ret = {}
                    try:
                        load = psutil.getloadavg()
                    except Exception:
                        uptime = subprocess.Popen("uptime", shell=True,
                                                  stdout=subprocess.PIPE
                                                  ).stdout.read().strip()
                        load = [float(res.replace(',', '.')) for res in
                                re.findall(r'([0-9]+[\.,]\d+)', uptime)]
                    ret['host.load.1m'] = load[0]
                    ret['host.load.5m'] = load[1]
                    ret['host.load.15m'] = load[2]
                    ret['host.cpu.percent'] = psutil.cpu_percent()
                    cache[cache_key] = ret

                yield sample.Sample(
                    name=self.meter_name,
                    type=self.meter_type,
                    unit=self.meter_unit,
                    volume=cache[cache_key][self.meter_name],
                    resource_id=self.conf.my_ip,
                    user_id=None,
                    project_id=None,
                    resource_metadata=resource_metadata
                )
        except Exception as err:
            LOG.exception(
                _('could not get %(key)s: %(e)s'),
                {'key': self.meter_name, 'e': err}
            )


class Load1m(_Base):
    meter_name = "host.load.1m"


class Load5m(_Base):
    meter_name = "host.load.5m"


class Load15m(_Base):
    meter_name = "host.load.15m"
