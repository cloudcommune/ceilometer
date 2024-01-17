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


import ConfigParser
import time

from ceilometer.compute import server_pollsters as pollsters
from ceilometer.compute.server_pollsters import util
from ceilometer.i18n import _
from ceilometer.i18n import _LE
from ceilometer import sample
from oslo_concurrency import processutils
from oslo_log import log


LOG = log.getLogger(__name__)

mysql_auth_file = '/home/trove/.my.cnf'


class _Base(pollsters.BaseComputePollster):

    keys = []
    name = None

    def _get_mysql_auth(self, auth_file=None):
        conf = ConfigParser.ConfigParser()
        conf.read(auth_file)
        mysql_auth = {
            'host': conf.get("client", "host"),
            'user': conf.get("client", "user"),
            'password': conf.get("client", "password"),
            'port': 3306,
            'charset': 'utf8'
        }
        return mysql_auth

    def get_samples(self, manager, cache, resources):
        try:
            value = self.inspector.inspect_mysql_stats(
                auth=self._get_mysql_auth(auth_file=mysql_auth_file),
                keys=self.keys
            )
            LOG.debug("Get instance %s %s" % (self.name, value))
            yield util.make_sample_from_instance(
                self.conf,
                name=self.name,
                type=sample.TYPE_GAUGE,
                unit=self.unit,
                volume=value.get(self.keys[0], 0),
            )
        except processutils.ProcessExecutionError as e:
            LOG.error(
                _LE('Get instance %(key)s %(error)s') %
                {'key': self.keys, 'error': e.stderr}
                )
        except Exception as err:
            LOG.exception(
                _('could not get vm %(key)s %(e)s'),
                {'key': self.keys, 'e': err}
            )


class MySQLThreadConPollster(_Base):
    keys = ["Threads_connected"]
    name = "trove.mysql.threads_connected"
    unit = "C"


class MySQLThreadRunPollster(_Base):
    keys = ["Threads_running"]
    name = "trove.mysql.threads_running"
    unit = "C"


class MySQLSlowPollster(_Base):
    keys = ["Slow_queries"]
    name = "trove.mysql.slowquerys"
    unit = "C"


class MySQLScanPollster(_Base):
    keys = ["Select_scan"]
    name = "trove.mysql.scan"
    unit = "C"


class MySQLDelayPollster(_Base):
    keys = ["Seconds_Behind_Master"]
    name = "trove.mysql.syncdelay"
    unit = "C"

    def get_samples(self, manager, cache, resources):
        try:
            values = self.inspector.inspect_mysql_slave_stats(
                auth=self._get_mysql_auth(auth_file=mysql_auth_file),
            )
            if len(values) > 0:
                value = values[32]
                if isinstance(value, long):
                    value = int(value)
            else:
                value = 0
            LOG.debug("Get instance %s %s" % (self.name, value))
            yield util.make_sample_from_instance(
                self.conf,
                name=self.name,
                type=sample.TYPE_GAUGE,
                unit=self.unit,
                volume=value,
            )
        except processutils.ProcessExecutionError as e:
            LOG.error(
                _LE('Get instance %(key)s %(error)s') %
                {'key': self.keys, 'error': e.stderr}
                )
        except Exception as err:
            LOG.exception(
                _('could not get vm %(key)s %(e)s'),
                {'key': self.keys, 'e': err}
            )


class MySQLTpsCommitPollster(_Base):
    keys = ["Com_commit", "Uptime"]
    name = "trove.mysql.tps_commit"
    unit = "C"

    def get_samples(self, manager, cache, resources):
        try:
            value1 = self.inspector.inspect_mysql_stats(
                auth=self._get_mysql_auth(auth_file=mysql_auth_file),
                keys=self.keys
            )
            time.sleep(1)
            value2 = self.inspector.inspect_mysql_stats(
                auth=self._get_mysql_auth(auth_file=mysql_auth_file),
                keys=self.keys
            )
            commits = value2["Com_commit"] - value1["Com_commit"]
            times = value2["Uptime"] - value1["Uptime"]
            tps_com = int(commits/times)
            LOG.debug("Get instance %s %s" % (self.name, tps_com))
            yield util.make_sample_from_instance(
                self.conf,
                name=self.name,
                type=sample.TYPE_GAUGE,
                unit=self.unit,
                volume=tps_com,
            )
        except processutils.ProcessExecutionError as e:
            LOG.error(
                _LE('Get instance %(key)s %(error)s') %
                {'key': self.keys, 'error': e.stderr}
                )
        except Exception as err:
            LOG.exception(
                _('could not get vm %(key)s %(e)s'),
                {'key': self.keys, 'e': err}
            )


class MySQLTpsRollbackPollster(_Base):
    keys = ["Com_rollback", "Uptime"]
    name = "trove.mysql.tps_rollback"
    unit = "C"

    def get_samples(self, manager, cache, resources):
        try:
            value1 = self.inspector.inspect_mysql_stats(
                auth=self._get_mysql_auth(auth_file=mysql_auth_file),
                keys=self.keys
            )
            time.sleep(1)
            value2 = self.inspector.inspect_mysql_stats(
                auth=self._get_mysql_auth(auth_file=mysql_auth_file),
                keys=self.keys
            )
            rollbacks = value2["Com_rollback"] - value1["Com_rollback"]
            times = value2["Uptime"] - value1["Uptime"]
            tps_roll = int(rollbacks/times)
            LOG.debug("Get instance %s %s" % (self.name, tps_roll))
            yield util.make_sample_from_instance(
                self.conf,
                name=self.name,
                type=sample.TYPE_GAUGE,
                unit=self.unit,
                volume=tps_roll,
            )
        except processutils.ProcessExecutionError as e:
            LOG.error(
                _LE('Get instance %(key)s %(error)s') %
                {'key': self.keys, 'error': e.stderr}
                )
        except Exception as err:
            LOG.exception(
                _('could not get vm %(key)s %(e)s'),
                {'key': self.keys, 'e': err}
            )


class MySQLQpsPollster(_Base):
    keys = ["Questions", "Uptime"]
    name = "trove.mysql.qps"
    unit = "C"

    def get_samples(self, manager, cache, resources):
        try:
            value1 = self.inspector.inspect_mysql_stats(
                auth=self._get_mysql_auth(auth_file=mysql_auth_file),
                keys=self.keys
            )
            time.sleep(1)
            value2 = self.inspector.inspect_mysql_stats(
                auth=self._get_mysql_auth(auth_file=mysql_auth_file),
                keys=self.keys
            )
            questions = value2["Questions"] - value1["Questions"]
            times = value2["Uptime"] - value1["Uptime"]
            qps = int(questions/times)
            LOG.debug("Get instance %s %s" % (self.name, qps))
            yield util.make_sample_from_instance(
                self.conf,
                name=self.name,
                type=sample.TYPE_GAUGE,
                unit=self.unit,
                volume=qps,
            )
        except processutils.ProcessExecutionError as e:
            LOG.error(
                _LE('Get instance %(key)s %(error)s') %
                {'key': self.keys, 'error': e.stderr}
                )
        except Exception as err:
            LOG.exception(
                _('could not get vm %(key)s %(e)s'),
                {'key': self.keys, 'e': err}
            )
