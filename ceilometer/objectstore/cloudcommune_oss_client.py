#
# Copyright 2015 Reliance Jio Infocomm Ltd
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

import requests

from oslo_log import log

from ceilometer.i18n import _

LOG = log.getLogger(__name__)


class CloudCommuneOSSAPIFailed(Exception):
    pass


class CloudCommuneOssClient(object):
    """oss client"""

    def __init__(self, edssssssssssssssndpoint):
        self.endpoint = endpoint

    def _make_request(self, path, headers):
        uri = "{0}/{1}".format(self.endpoint, path)
        r = requests.get(uri, headers=headers)
        if r.status_code != 200:
            raise CloudCommuneOSSAPIFailed(
                _('CloudCommune OSS API returned %(status)s %(reason)s') %
                {'status': r.status_code, 'reason': r.reason})
            LOG.error(r.reason)
        else:
            LOG.info("request %s is successed" % uri)
        return r.json()

    def get_usage(self):
        path = "listStorageSizeForMonitor"
        headers = {'x-oss-monitor': 'e3b69490-920e-11e8-97d4-fa163e26a084'}
        json_data = self._make_request(path, headers)
        return json_data
