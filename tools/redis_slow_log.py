#!/usr/bin/env python2
# -*- coding: utf-8 -*-
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

import fileinput
import getopt
import hashlib
import json
import re
import redis
import sys
import time


class RedisSlowLog(object):

    def __init__(self):
        passwd = self.is_enable_auth()
        if passwd == '':
            self.redis_client = redis.Redis()
        else:
            self.redis_client = redis.Redis(password=passwd)

    def is_enable_auth(self):
        rt = "^requirepass (.*?)"
        for line in fileinput.input("/etc/redis.conf"):
            if re.search(rt, line):
                line = line.strip('\r\n')
                return line.split(' ')[1]
        return

    def get_slowlog_max_len(self):
        return self.redis_client.slowlog_len()

    def update_md5(self, value=None):
        value = json.dumps(value)
        md5hash = hashlib.md5(value)
        md5 = md5hash.hexdigest()
        dict_value = json.loads(value)
        dict_value['md5'] = md5
        time_format = '%Y-%m-%d %H:%M:%S'
        time_tuple = time.localtime(dict_value['start_time'])
        dict_value['time'] = time.strftime(time_format, time_tuple)
        return dict_value

    def get_slow_log(self):
        logs = []
        slowlog_max_len = self.get_slowlog_max_len()
        slow_logs = self.redis_client.slowlog_get(slowlog_max_len)
        for line in slow_logs:
            line = self.update_md5(value=line)
            logs.append(line)
        return logs

    def write_output(self, output=None, value=None):
        with open(output, 'a') as f:
            for line in value:
                line = json.dumps(line)
                f.write(line)
                f.write('\n')
            f.close()


def main():

    output = '/var/log/redis/redis_slow.log'
    redis_logs = RedisSlowLog()
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:", ["help", "output="])
    except getopt.GetoptError:
        print("opt error")

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print("redis_slow_log --output xxxx")
            sys.exit(1)
        if opt in ("-o", "--output"):
            output = arg

    logs = redis_logs.get_slow_log()
    redis_logs.write_output(output=output, value=logs)

if __name__ == "__main__":
    main()
