#
# Copyright 2024 CloudCommune
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

from ceilometer import sample
import ConfigParser
from oslo_log import log
import socket

LOG = log.getLogger(__name__)

trove_file = '/etc/trove/conf.d/guest_info.conf'


def _get_metadata_from_object(conf):
    """Return a metadata dictionary for the instance."""
    src_metadata = {}
    metadata = {
        'display_name': instance_name(),
    }

    return sample.add_reserved_user_metadata(conf, src_metadata,
                                             metadata)


def make_sample_from_instance(conf,  name, type, unit, volume,
                              resource_id=None, additional_metadata=None,
                              monotonic_time=None):
    trove_env = get_guest_env()
    additional_metadata = additional_metadata or {}
    resource_metadata = _get_metadata_from_object(conf)
    resource_metadata.update(additional_metadata)
    return sample.Sample(
        name=name,
        type=type,
        unit=unit,
        volume=volume,
        user_id=trove_env["datastore_manager"],
        project_id=trove_env["tenant_id"],
        resource_id=trove_env["guest_id"],
        resource_metadata=resource_metadata,
        monotonic_time=monotonic_time,
    )


def instance_name():
    """Shortcut to get instance name."""
    return socket.gethostname()


def get_guest_env():
    cfg = ConfigParser.ConfigParser()
    cfg.read(trove_file)
    value = cfg.defaults()
    return dict(value)
