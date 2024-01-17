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

import mock
from oslo_config import fixture as config_fixture
from oslotest import base

from ceilometer.network.statistics.cloudcommunesdn import client
from ceilometer import service as ceilometer_service


class TestCloudCommuneSDNClient(base.BaseTestCase):

    def setUp(self):
        super(TestCloudCommuneSDNClient, self).setUp()
        conf = ceilometer_service.prepare_service(argv=[], config_files=[])
        self.CONF = self.useFixture(config_fixture.Config(conf)).conf

        data = [{
            "fip_address": "10.3.10.181",
            "eip_address": "100.10.33.11",
            "receive_bytes": 100,
            "receive_pks": 2,
            "transmit_bytes": 50,
            "transmit_pks": 1,
            "timestamp": "2016-09-01 09:00:00",
            "duration": 120
        }]
        self.client = client.Client(self.CONF, 'http://127.0.0.1:8088',
                                    data)

        self.get_resp = mock.MagicMock()
        self.get = mock.patch('requests.get',
                              return_value=self.get_resp).start()
        self.get_resp.raw.version = 1.1
        self.get_resp.status_code = 200
        self.get_resp.reason = 'OK'
        self.get_resp.content = ''

    def test_ip_statistics(self):
        self.client.networks.get_ip_statistics()

        call_args = self.get.call_args_list[0][0]
        call_kwargs = self.get.call_args_list[0][1]

        expected_url = ('http://127.0.0.1:8088/statistics/floatingip')
        self.assertEqual(expected_url, call_args[0])

        data = call_kwargs.get('data')

        expected_data = [{
            "fip_address": "10.3.10.181",
            "eip_address": "100.10.33.11",
            "receive_bytes": 100,
            "receive_pks": 2,
            "transmit_bytes": 50,
            "transmit_pks": 1,
            "timestamp": "2016-09-01 09:00:00",
            "duration": 120
        }]
        self.assertEqual(expected_data, data)
