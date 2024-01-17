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
"""Implementation of Inspector abstraction for libvirt."""

from oslo_log import log as logging

from ceilometer.compute.virt import inspector as virt_inspector

LOG = logging.getLogger(__name__)


class NoneInspector(virt_inspector.Inspector):

    def __init__(self, conf):
        super(NoneInspector, self).__init__(conf)
        # NOTE(sileht): create a connection on startup
