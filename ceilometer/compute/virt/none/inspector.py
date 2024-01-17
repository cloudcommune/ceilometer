#
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
"""Implementation of Inspector abstraction for libvirt."""

import MySQLdb

from oslo_log import log as logging

from ceilometer.compute.virt import inspector as virt_inspector

LOG = logging.getLogger(__name__)


class NoneInspector(virt_inspector.Inspector):

    def __init__(self, conf):
        super(NoneInspector, self).__init__(conf)
        # NOTE(sileht): create a connection on startup

    def _connection_mysql(self, auth=None):
        conn = MySQLdb.connect(
            host=auth['host'],
            user=auth['user'],
            passwd=auth['password'],
            port=auth['port']
        )
        return conn

    def inspect_mysql_stats(self, auth=None, keys=None):
        conn = self._connection_mysql(auth=auth)
        query = 'show global status'
        cur = conn.cursor()
        cur.execute(query)
        result = cur.fetchall()
        conn.commit()
        cur.close()
        value = {}
        for key in keys:
            for t in result:
                if t[0] == key:
                    value[key] = int(t[1])
                    break
        return value

    def inspect_mysql_slave_stats(self, auth=None):
        conn = self._connection_mysql(auth=auth)
        query = 'show slave status'
        cur = conn.cursor()
        cur.execute(query)
        result = cur.fetchall()
        conn.commit()
        cur.close()
        if len(result) > 0:
            value = list(result[0])
        else:
            value = []
        return value
