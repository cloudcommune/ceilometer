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


import abc
import collections
import redis
import six
import subprocess

if six.PY2:
    from monotonic import monotonic as now
else:
    from time import monotonic as now

from ceilometer.compute.server_pollsters import util
from ceilometer.i18n import _
from ceilometer.i18n import _LE
from ceilometer.polling import plugin_base
from ceilometer import sample
from oslo_concurrency import processutils
from oslo_log import log


LOG = log.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class _Base(plugin_base.PollsterBase):

    section = None
    host = '127.0.0.1'
    port = '6379'
    sub_key = None
    inspector_method = None
    redis_config_file = '/etc/redis.conf'

    def _get_redis_passwd(self):
        cmd = 'sudo cat %s | grep requirepass' % self.redis_config_file
        line = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, shell=True
        )
        line = line.stdout.read()
        line = line.strip()
        if len(line) > 0:
            passwd = line.split()[1]
            return str(passwd)
        else:
            return ''

    @property
    def default_discovery(self):
        return "server_discovery"

    def connect_redis(self, host, port):
        passwd = self._get_redis_passwd()
        if len(passwd) > 0:
            r = redis.Redis(host, port, password=passwd)
        else:
            r = redis.Redis(host, port)
        return r

    def _inspect_cached(self, cache, instance, duration):
        cache.setdefault(self.inspector_method, {})
        if instance.id not in cache[self.inspector_method]:
            result = getattr(self.inspector, self.inspector_method)(
                instance, duration)
            polled_time = now()
            # Ensure we don't cache an iterator
            if isinstance(result, collections.Iterable):
                result = list(result)
            else:
                result = [result]
            cache[self.inspector_method][instance.id] = (polled_time, result)
        return cache[self.inspector_method][instance.id]

    def get_samples(self, manager, cache, resources):
        try:
            r = self.connect_redis(self.host, self.port)
            r.ping()
            redis_info = r.info(section=self.section)
            if self.key in redis_info.keys():
                value = redis_info[self.key]
                if self.sub_key:
                    value = value[self.sub_key]
            else:
                value = 0
            LOG.debug("get vm %s %s" % (self.name, value))
            yield util.make_sample_from_instance(
                self.conf,
                name=self.name,
                type=sample.TYPE_GAUGE,
                unit=self.unit,
                volume=value,
            )
        except processutils.ProcessExecutionError as e:
            LOG.error(
                _LE('get vm %(key)s %(error)s') %
                {'key': self.key, 'error': e.stderr}
            )
        except Exception as err:
            LOG.exception(
                _('could not get vm %(key)s %(e)s'),
                {'key': self.key, 'e': err}
            )
