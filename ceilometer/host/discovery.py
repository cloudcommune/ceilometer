#
# Copyright 2024 CloudCommune.
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

from oslo_config import cfg
from oslo_log import log
import subprocess

from ceilometer.agent import plugin_base


hostname = subprocess.Popen('hostname', shell=True,
                            stdout=subprocess.PIPE).stdout.read().strip()
my_ip = subprocess.Popen("grep -w %s /etc/hosts | awk '{print $1}'" % hostname,
                         shell=True, stdout=subprocess.PIPE
                         ).stdout.read().strip()

OPTS = [
    cfg.StrOpt('my_ip',
               default=my_ip,
               help="IP address of this node, used for host monitoring")
]

LOG = log.getLogger(__name__)


class HostDiscovery(plugin_base.DiscoveryBase):
    method = None

    def discover(self, manager, param=None):
        return [self.conf.host]

    @property
    def group_id(self):
        return self.conf.host
