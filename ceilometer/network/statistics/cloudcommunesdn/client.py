# Copyright (C) 2024 CloudCommune
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import copy

from oslo_log import log
import requests
import six
from six.moves.urllib import parse as urlparse

from ceilometer.i18n import _


LOG = log.getLogger(__name__)


class CloudCommuneSDNAPIFailed(Exception):
    pass


class AnalyticsAPIBaseClient(object):
    """CloudCommuneSDN Base Statistics REST API Client."""

    def __init__(self, conf, endpoint, data):
        self.conf = conf
        self.endpoint = endpoint
        self.data = data or {}

    def request(self, path, data=None):
        req_data = copy.copy(self.data)
        if data:
            req_data.update(data)

        req_params = self._get_req_params(data=req_data)

        url = urlparse.urljoin(self.endpoint, path)
        self._log_req(url, req_params)
        resp = requests.get(url, **req_params)
        self._log_res(resp)

        if resp.status_code != 200:
            raise CloudCommuneSDNAPIFailed (
                _('CloudCommuneSDN API returned %(status)s %(reason)s') %
                {'status': resp.status_code, 'reason': resp.reason})

        return resp

    def _get_req_params(self, data=None):
        req_params = {
            'headers': {
                'Accept': 'application/json'
            },
            'data': data,
            'allow_redirects': False,
            'timeout': self.conf.http_timeout,
        }

        return req_params

    def _log_req(self, url, req_params):
        if not self.conf.debug:
            return

        curl_command = ['REQ: curl -i -X GET ']

        params = []
        for name, value in six.iteritems(req_params['data']):
            params.append("%s=%s" % (name, value))

        curl_command.append('"%s?%s" ' % (url, '&'.join(params)))

        for name, value in six.iteritems(req_params['headers']):
            curl_command.append('-H "%s: %s" ' % (name, value))

        LOG.debug(''.join(curl_command))

    def _log_res(self, resp):
        if not self.conf.debug:
            return

        dump = ['RES: \n', 'HTTP %.1f %s %s\n' % (resp.raw.version,
                                                  resp.status_code,
                                                  resp.reason)]
        dump.extend('%s: %s\n' % (k, v)
                    for k, v in six.iteritems(resp.headers))
        dump.append('\n')
        if resp.content:
            dump.extend([resp.content, '\n'])

        LOG.debug(''.join(dump))


class CloudCommuneSDNAPIClient(AnalyticsAPIBaseClient):
    """CloudCommuneSDN Statistics REST API Client."""

    def get_ip_statistics(self, path=None, data=None):
        """Get statistics of a floating ip or eip.

        URL:
            {endpoint}/statistics/floatingip
        RESP:
            resp = [{
                "fip_address": "10.3.10.181",
                "eip_address": "100.10.33.11",
                "receive_bytes": 100,
                "receive_pks": 2,
                "transmit_bytes": 50,
                "transmit_pks": 1,
                "timestamp": "2016-09-01 09:00:00",
                "duration": 120
            },
            {
                "fip_address": "10.3.10.182",
                "eip_address": "100.10.33.12",
                "receive_bytes": 200,
                "receive_pks": 2,
                "transmit_bytes": 70,
                "transmit_pks": 1,
                "timestamp": "2016-09-01 09:00:00",
                "duration": 120
            },
            {
                "fip_address": "10.3.10.185",
                "eip_address": "100.10.33.15",
                "receive_bytes": 500,
                "receive_pks": 10,
                "transmit_bytes": 450,
                "transmit_pks": 9,
                "timestamp": "2016-09-01 09:00:00",
                "duration": 120
            }]
        """

        path = '/statistics/floatingip' if path is None else path
        resp = self.request(path, data)

        return resp.json()


class Client(object):

    def __init__(self, conf, endpoint, data=None):
        self.networks = CloudCommuneSDNAPIClient(conf, endpoint, data)
