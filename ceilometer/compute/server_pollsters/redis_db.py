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


from ceilometer.compute.server_pollsters import _Base
from ceilometer.compute.server_pollsters import util
from ceilometer.i18n import _
from ceilometer.i18n import _LE
from ceilometer import sample
from oslo_concurrency import processutils
from oslo_log import log
import time


LOG = log.getLogger(__name__)


class KeyTotalPollster(_Base):
    key = "dbsize"
    name = "trove.redis.key.total"
    unit = "C"

    def get_samples(self, manager, cache, resources):
        value = 0
        try:
            r = self.connect_redis(self.host, self.port)
            r.ping()
            redis_dbs = r.info(section='keyspace')
            for db in redis_dbs.keys():
                value = value + redis_dbs[db]['keys']
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


class KeyspaceUsageHitPollster(_Base):
    name = "trove.redis.keyspace.usage.hit"
    unit = "%"

    def get_samples(self, manager, cache, resources):
        try:
            r = self.connect_redis(self.host, self.port)
            r.ping()
            redis_info = r.info()
            keyspace_hits = int(redis_info['keyspace_hits'])
            keyspace_misses = int(redis_info['keyspace_misses'])
            sum = keyspace_hits + keyspace_misses
            if sum == 0:
                value = 0
            else:
                value = keyspace_hits/(keyspace_hits + keyspace_misses) * 100
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
                _LE('get vm %(name)s %(error)s') %
                {'name': self.name, 'error': e.stderr}
                )
        except Exception as err:
            LOG.exception(
                _('could not get vm %(name)s %(e)s'),
                {'name': self.name, 'e': err}
            )


class KeyExpiredPollster(_Base):
    key = "expired_keys"
    name = "trove.redis.key.expired"
    unit = "C"


class KeyEvictedPollster(_Base):
    key = "evicted_keys"
    name = "trove.redis.key.evicted"
    unit = "C"


class KeyspaceHitsPollster(_Base):
    key = "keyspace_hits"
    name = "trove.redis.keyspace.hits"
    unit = "C"


class KeyspaceMissesPollster(_Base):
    key = "keyspace_misses"
    name = "trove.redis.keyspace.misses"
    unit = "C"


class KeyspaceExpiresPollster(_Base):
    section = "Keyspace"
    key = "db0"
    sub_key = "expires"
    name = "trove.redis.keyspace.expires"
    unit = "kbps"


class ClientConnectedPollster(_Base):
    key = "connected_clients"
    name = "trove.redis.client.connected"
    unit = "C"


class ClientConnectedUsagePollster(_Base):
    key = "connected_clients"
    name = "trove.redis.client.connected.usage"
    unit = "%"
    maxclients = 10000

    def get_samples(self, manager, cache, resources):
        try:
            r = self.connect_redis(self.host, self.port)
            r.ping()
            redis_info = r.info()
            connected_clients = redis_info[self.key]
            value = connected_clients/self.maxclients * 100
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
                _LE('get vm %(name)s %(error)s') %
                {'name': self.name, 'error': e.stderr}
                )
        except Exception as err:
            LOG.exception(
                _('could not get vm %(name)s %(e)s'),
                {'name': self.name, 'e': err}
            )


class KeyErrorRepliesPollster(_Base):
    key = "unexpected_error_replies"
    name = "trove.redis.key.error"
    unit = "C"


class CmdStatGetAvgPollster(_Base):
    section = 'Commandstats'
    key = "cmdstat_get"
    name = "trove.redis.cmdstat.get.avg"
    unit = "C/S"

    def get_samples(self, manager, cache, resources):
        value = 0
        try:
            r = self.connect_redis(self.host, self.port)
            r.ping()
            redis_info = r.info(section=self.section)
            if self.key in redis_info.keys():
                calls1 = redis_info[self.key]['calls']
                times1 = redis_info[self.key]['usec']
                time.sleep(1)
                calls2 = redis_info[self.key]['calls']
                times2 = redis_info[self.key]['usec']
                interval = times2 - times1
                calls = calls2 - calls1
                if int(interval) > 0:
                    value = calls / interval
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
                _LE('get vm %(name)s %(error)s') %
                {'name': self.name, 'error': e.stderr}
                )
        except Exception as err:
            LOG.exception(
                _('could not get vm %(name)s %(e)s'),
                {'name': self.name, 'e': err}
            )


class CmdStatGetCallsPollster(_Base):
    section = 'Commandstats'
    key = "cmdstat_get"
    sub_key = "calls"
    name = "trove.redis.cmdstat.get.calls"
    unit = "C"


class CmdStatSetAvgPollster(_Base):
    section = 'Commandstats'
    key = "cmdstat_set"
    name = "trove.redis.cmdstat.set.avg"
    unit = "C/S"

    def get_samples(self, manager, cache, resources):
        value = 0
        try:
            r = self.connect_redis(self.host, self.port)
            r.ping()
            redis_info = r.info(section=self.section)
            if self.key in redis_info.keys():
                calls1 = redis_info[self.key]['calls']
                times1 = redis_info[self.key]['usec']
                time.sleep(1)
                calls2 = redis_info[self.key]['calls']
                times2 = redis_info[self.key]['usec']
                interval = times2 - times1
                calls = calls2 - calls1
                if int(interval) > 0:
                    value = calls / interval
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
                _LE('get vm %(name)s %(error)s') %
                {'name': self.name, 'error': e.stderr}
                )
        except Exception as err:
            LOG.exception(
                _('could not get vm %(name)s %(e)s'),
                {'name': self.name, 'e': err}
            )


class CmdStatSetCallsPollster(_Base):
    section = 'Commandstats'
    key = "cmdstat_set"
    sub_key = "calls"
    name = "trove.redis.cmdstat.set.calls"
    unit = "C"


class CmdStatOthersAvgPollster(_Base):

    section = 'Commandstats'
    remove_keys = ["cmdstat_set", "cmdstat_get"]
    sub_key = "usec_per_call"
    name = "trove.redis.cmdstat.others.avg"
    unit = "C/S"
    sum = 0

    def get_samples(self, manager, cache, resources):
        try:
            r = self.connect_redis(self.host, self.port)
            r.ping()
            redis_info = r.info(section=self.section)
            for remove_key in self.remove_keys:
                if remove_key in redis_info.keys():
                    del redis_info[remove_key]
            numbers = len(redis_info.keys())
            if numbers > 0:
                list_values = redis_info.values()
                for dict_value in list_values:
                    self.sum = self.sum + int(dict_value[self.sub_key])
                value = self.sum / numbers
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
                _LE('get vm %(name)s %(error)s') %
                {'name': self.name, 'error': e.stderr}
                )
        except Exception as err:
            LOG.exception(
                _('could not get vm %(name)s %(e)s'),
                {'name': self.name, 'e': err}
            )


class StatsInstantaneousOpsPollster(_Base):
    section = "Stats"
    key = "instantaneous_ops_per_sec"
    name = "trove.redis.instantaneous.ops"
    unit = "C/S"


class StatsInstantaneousInputPollster(_Base):
    section = "Stats"
    key = "instantaneous_input_kbps"
    name = "trove.redis.instantaneous.input"
    unit = "kbps"


class StatsInstantaneousOutputPollster(_Base):
    section = "Stats"
    key = "instantaneous_output_kbps"
    name = "trove.redis.instantaneous.output"
    unit = "kbps"


class SlowNumPollster(_Base):

    name = "trove.redis.slow.num"
    unit = "C"
    num = 0

    def get_samples(self, manager, cache, resources):
        try:
            r = self.connect_redis(self.host, self.port)
            r.ping()
            num = r.slowlog_len()
            value = int(num)
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
                _LE('get vm %(name)s %(error)s') %
                {'name': self.name, 'error': e.stderr}
                )
        except Exception as err:
            LOG.exception(
                _('could not get vm %(name)s %(e)s'),
                {'name': self.name, 'e': err}
            )
