# Copyright (C) 2024 CloudCommune.
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

from ceilometer.network import statistics
from ceilometer import sample


class FIPReceivePacketsPollster(statistics._Base):
    meter_name = 'ip.floating.incoming.packets'
    meter_type = sample.TYPE_DELTA
    meter_unit = 'packet'


class FIPTransmitPacketsPollster(statistics._Base):
    meter_name = 'ip.floating.outgoing.packets'
    meter_type = sample.TYPE_DELTA
    meter_unit = 'packet'


class FIPReceiveBytesPollster(statistics._Base):
    meter_name = 'ip.floating.incoming.bytes'
    meter_type = sample.TYPE_CUMULATIVE
    meter_unit = 'B'


class FIPTransmitBytesPollster(statistics._Base):
    meter_name = 'ip.floating.outgoing.bytes'
    meter_type = sample.TYPE_CUMULATIVE
    meter_unit = 'B'


class IP6ReceivePacketsPollster(statistics._Base):
    meter_name = 'ip6.incoming.packets'
    meter_type = sample.TYPE_DELTA
    meter_unit = 'packet'


class IP6TransmitPacketsPollster(statistics._Base):
    meter_name = 'ip6.outgoing.packets'
    meter_type = sample.TYPE_DELTA
    meter_unit = 'packet'


class IP6ReceiveBytesPollster(statistics._Base):
    meter_name = 'ip6.incoming.bytes'
    meter_type = sample.TYPE_CUMULATIVE
    meter_unit = 'B'


class IP6TransmitBytesPollster(statistics._Base):
    meter_name = 'ip6.outgoing.bytes'
    meter_type = sample.TYPE_CUMULATIVE
    meter_unit = 'B'
