# Copyright 2013 Cloudbase Solutions Srl
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
"""Implementation of Inspector abstraction for Hyper-V"""

import collections
import functools
import sys
import warnings

from os_win import exceptions as os_win_exc
from os_win import utilsfactory
from oslo_utils import units

from ceilometer.compute.pollsters import util
from ceilometer.compute.virt import inspector as virt_inspector


def convert_exceptions(exception_map, yields=True):
    expected_exceptions = tuple(exception_map.keys())

    def _reraise_exception(exc):
        # exception might be a subclass of an expected exception.
        for expected in expected_exceptions:
            if isinstance(exc, expected):
                raised_exception = exception_map[expected]
                break

        exc_info = sys.exc_info()
        exc = raised_exception(str(exc_info[1]))
        raise exc.with_traceback(exc_info[2])

    def decorator(function):
        if yields:
            @functools.wraps(function)
            def wrapper(*args, **kwargs):
                try:
                    # NOTE(claudiub): We're consuming the function's yield in
                    # order to avoid yielding a generator.
                    for item in function(*args, **kwargs):
                        yield item
                except expected_exceptions as ex:
                    _reraise_exception(ex)
        else:
            @functools.wraps(function)
            def wrapper(*args, **kwargs):
                try:
                    return function(*args, **kwargs)
                except expected_exceptions as ex:
                    _reraise_exception(ex)

        return wrapper
    return decorator


exception_conversion_map = collections.OrderedDict([
    # NOTE(claudiub): order should be from the most specialized exception type
    # to the most generic exception type.
    # (expected_exception, converted_exception)
    (os_win_exc.NotFound, virt_inspector.InstanceNotFoundException),
    (os_win_exc.OSWinException, virt_inspector.InspectorException),
])

# NOTE(claudiub): the purpose of the decorators below is to prevent any
# os_win exceptions (subclasses of OSWinException) to leak outside of the
# HyperVInspector.


class HyperVInspector(virt_inspector.Inspector):

    def __init__(self, conf):
        super(HyperVInspector, self).__init__(conf)
        self._utils = utilsfactory.get_metricsutils()
        self._host_max_cpu_clock = self._compute_host_max_cpu_clock()

        warnings.warn('Support for HyperV is deprecated.',
                      category=DeprecationWarning, stacklevel=3)

    def _compute_host_max_cpu_clock(self):
        hostutils = utilsfactory.get_hostutils()
        # host's number of CPUs and CPU clock speed will not change.
        cpu_info = hostutils.get_cpus_info()
        host_cpu_count = len(cpu_info)
        host_cpu_clock = cpu_info[0]['MaxClockSpeed']

        return float(host_cpu_clock * host_cpu_count)

    @convert_exceptions(exception_conversion_map, yields=False)
    def inspect_instance(self, instance, duration):
        instance_name = util.instance_name(instance)
        (cpu_clock_used,
         cpu_count, uptime) = self._utils.get_cpu_metrics(instance_name)
        cpu_percent_used = cpu_clock_used / self._host_max_cpu_clock
        # Nanoseconds
        cpu_time = (int(uptime * cpu_percent_used) * units.k)
        memory_usage = self._utils.get_memory_metrics(instance_name)

        return virt_inspector.InstanceStats(
            cpu_number=cpu_count,
            cpu_time=cpu_time,
            memory_usage=memory_usage)

    @convert_exceptions(exception_conversion_map)
    def inspect_vnics(self, instance, duration):
        instance_name = util.instance_name(instance)
        for vnic_metrics in self._utils.get_vnic_metrics(instance_name):
            yield virt_inspector.InterfaceStats(
                name=vnic_metrics["element_name"],
                mac=vnic_metrics["address"],
                fref=None,
                parameters=None,
                rx_bytes=vnic_metrics['rx_mb'] * units.Mi,
                rx_packets=0,
                rx_drop=0,
                rx_errors=0,
                tx_bytes=vnic_metrics['tx_mb'] * units.Mi,
                tx_packets=0,
                tx_drop=0,
                tx_errors=0,
                rx_bytes_delta=0,
                tx_bytes_delta=0)

    @convert_exceptions(exception_conversion_map)
    def inspect_disks(self, instance, duration):
        instance_name = util.instance_name(instance)
        for disk_metrics in self._utils.get_disk_metrics(instance_name):
            yield virt_inspector.DiskStats(
                device=disk_metrics['instance_id'],
                read_requests=0,
                # Return bytes
                read_bytes=disk_metrics['read_mb'] * units.Mi,
                write_requests=0,
                write_bytes=disk_metrics['write_mb'] * units.Mi,
                errors=0, wr_total_times=0, rd_total_times=0)

    @convert_exceptions(exception_conversion_map)
    def inspect_disk_latency(self, instance, duration):
        instance_name = util.instance_name(instance)
        for disk_metrics in self._utils.get_disk_latency_metrics(
                instance_name):
            yield virt_inspector.DiskLatencyStats(
                device=disk_metrics['instance_id'],
                disk_latency=disk_metrics['disk_latency'] / 1000)

    @convert_exceptions(exception_conversion_map)
    def inspect_disk_iops(self, instance, duration):
        instance_name = util.instance_name(instance)
        for disk_metrics in self._utils.get_disk_iops_count(instance_name):
            yield virt_inspector.DiskIOPSStats(
                device=disk_metrics['instance_id'],
                iops_count=disk_metrics['iops_count'])
