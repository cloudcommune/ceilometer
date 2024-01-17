#
# Copyright 2014 Red Hat, Inc
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

from oslo_log import log

from ceilometer.agent import plugin_base

LOG = log.getLogger(__name__)


class InstanceDiscovery(plugin_base.DiscoveryBase):
    method = None

    def __init__(self, conf):
        super(InstanceDiscovery, self).__init__(conf)

        self.expiration_time = conf.compute.resource_update_interval
        self.cache_expiry = conf.compute.resource_cache_expiry

    def discover(self, manager, param=None):
        return ['localhost']

    @property
    def group_id(self):
        return self.conf.host
