# Copyright (C)  2024 CloudCommune.
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

from ceilometer.network.statistics import fip
from ceilometer import sample
from ceilometer.tests.unit.network import statistics


class TestFipPollster(statistics._PollsterTestBase):

    def test_fip_receive_packets_pollster(self):
        self._test_pollster(
            fip.FIPReceivePacketsPollster,
            'ip.floating.incoming.packets',
            sample.TYPE_DELTA,
            'packet')

    def test_fip_transmit_packets_pollster(self):
        self._test_pollster(
            fip.FIPTransmitPacketsPollster,
            'ip.floating.outgoing.packets',
            sample.TYPE_DELTA,
            'packet')

    def test_fip_receive_bytes_pollster(self):
        self._test_pollster(
            fip.FIPReceiveBytesPollster,
            'ip.floating.incoming.bytes',
            sample.TYPE_CUMULATIVE,
            'B')

    def test_fip_pollster_transmit_bytes(self):
        self._test_pollster(
            fip.FIPTransmitBytesPollster,
            'ip.floating.outgoing.bytes',
            sample.TYPE_CUMULATIVE,
            'B')
