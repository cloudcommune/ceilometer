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

from oslo_log import log

import ceilometer
from ceilometer.compute import pollsters
from ceilometer.compute.pollsters import util
from ceilometer.compute.virt import inspector as virt_inspector
from ceilometer.i18n import _
from ceilometer.polling import plugin_base
from ceilometer import sample


LOG = log.getLogger(__name__)


class GPUMemTotalPollster(pollsters.GenericComputePollster):

    def get_samples(self, manager, cache, resources):
        for instance in resources:
            LOG.debug('checking instance %s', instance.id)
            try:
                if not self.inspector.inspect_cc_ga_version(instance):
                    LOG.warning('%s get gpu memory total ignored', instance)
                    continue
                counts = self.inspector.inspect_gpu_counts(instance)
                if counts < 1:
                    LOG.warning('%s GPU not running or drive error', instance)
                    continue
                gpu_num = {"gpu_number": counts}
                for id in range(int(counts)):
                    gpu_info = self.inspector.inspect_gpu_memory_total(
                        instance,
                        id
                    )
                    LOG.debug("GPU MEMORY TOTAL: %(instance)s %(size)s",
                              {'instance': instance,
                               'size': gpu_info.memory_total})
                    resource_id = "{}_gpu{}".format(instance.id, id + 1)
                    yield util.make_sample_from_instance(
                        self.conf,
                        instance=instance,
                        resource_id=resource_id,
                        name='gpu.memory.total',
                        type=sample.TYPE_GAUGE,
                        unit='MiB',
                        volume=gpu_info.memory_total,
                        additional_metadata=gpu_num,
                    )
            except virt_inspector.InstanceNotFoundException as err:
                # Instance was deleted while getting samples. Ignore it.
                LOG.debug('Exception while getting samples %s', err)
            except virt_inspector.InstanceShutOffException as e:
                LOG.debug('Instance %(instance_id)s was shut off while '
                          'getting samples of %(pollster)s: %(exc)s',
                          {'instance_id': instance.id,
                           'pollster': self.__class__.__name__, 'exc': e})
            except ceilometer.NotImplementedError:
                # Selected inspector does not implement this pollster.
                LOG.debug('Obtaining GPU memory is not implemented for %s',
                          self.inspector.__class__.__name__)
                raise plugin_base.PollsterPermanentError(resources)
            except Exception as err:
                LOG.exception(
                    _('could not get GPU memory total for %(id)s: %(e)s'),
                    {'id': instance.id, 'e': err}
                )


class GPUMemUsedPollster(pollsters.GenericComputePollster):

    def get_samples(self, manager, cache, resources):
        for instance in resources:
            LOG.debug('checking instance %s', instance.id)
            try:
                if not self.inspector.inspect_cc_ga_version(instance):
                    LOG.warning('%s get gpu memory used ignored', instance)
                    continue
                counts = int(self.inspector.inspect_gpu_counts(instance))
                if counts < 1:
                    LOG.warning('%s GPU not running or drive error', instance)
                    continue
                gpu_num = {"gpu_number": counts}
                for id in range(int(counts)):
                    gpu_info = self.inspector.inspect_gpu_memory_used(
                        instance,
                        id
                    )
                    LOG.debug("GPU MEMORY USED: %(instance)s %(size)s",
                              {'instance': instance,
                               'size': gpu_info.memory_used})
                    resource_id = "{}_gpu{}".format(instance.id, id + 1)
                    yield util.make_sample_from_instance(
                        self.conf,
                        instance=instance,
                        resource_id=resource_id,
                        name='gpu.memory.used',
                        type=sample.TYPE_GAUGE,
                        unit='MiB',
                        volume=gpu_info.memory_used,
                        additional_metadata=gpu_num,
                    )
            except virt_inspector.InstanceNotFoundException as err:
                # Instance was deleted while getting samples. Ignore it.
                LOG.debug('Exception while getting samples %s', err)
            except virt_inspector.InstanceShutOffException as e:
                LOG.debug('Instance %(instance_id)s was shut off while '
                          'getting samples of %(pollster)s: %(exc)s',
                          {'instance_id': instance.id,
                           'pollster': self.__class__.__name__, 'exc': e})
            except ceilometer.NotImplementedError:
                # Selected inspector does not implement this pollster.
                LOG.debug('Obtaining GPU memory is not implemented for %s',
                          self.inspector.__class__.__name__)
                raise plugin_base.PollsterPermanentError(resources)
            except Exception as err:
                LOG.exception(
                    _('could not get GPU memory used for %(id)s: %(e)s'),
                    {'id': instance.id, 'e': err}
                )


class GPUUtilPollster(pollsters.GenericComputePollster):

    def get_samples(self, manager, cache, resources):
        for instance in resources:
            LOG.debug('checking instance %s', instance.id)
            try:
                if not self.inspector.inspect_cc_ga_version(instance):
                    LOG.warning('%s get gpu utilization ignored', instance)
                    continue
                counts = int(self.inspector.inspect_gpu_counts(instance))
                if counts < 1:
                    LOG.warning('%s GPU not running or drive error', instance)
                    continue
                gpu_num = {"gpu_number": counts}
                for id in range(int(counts)):
                    gpu_info = self.inspector.inspect_gpu_util(
                        instance,
                        id
                    )
                    LOG.debug("GPU MEMORY UTIL: %(instance)s %(size)s",
                              {'instance': instance,
                               'size': gpu_info.util})
                    resource_id = "{}_gpu{}".format(instance.id, id + 1)
                    yield util.make_sample_from_instance(
                        self.conf,
                        instance=instance,
                        resource_id=resource_id,
                        name='gpu.utilization',
                        type=sample.TYPE_GAUGE,
                        unit='%',
                        volume=gpu_info.util,
                        additional_metadata=gpu_num,
                    )
            except virt_inspector.InstanceNotFoundException as err:
                # Instance was deleted while getting samples. Ignore it.
                LOG.debug('Exception while getting samples %s', err)
            except virt_inspector.InstanceShutOffException as e:
                LOG.debug('Instance %(instance_id)s was shut off while '
                          'getting samples of %(pollster)s: %(exc)s',
                          {'instance_id': instance.id,
                           'pollster': self.__class__.__name__, 'exc': e})
            except ceilometer.NotImplementedError:
                # Selected inspector does not implement this pollster.
                LOG.debug('Obtaining GPU util is not implemented for %s',
                          self.inspector.__class__.__name__)
                raise plugin_base.PollsterPermanentError(resources)
            except Exception as err:
                LOG.exception(
                    _('could not get GPU utilization for %(id)s: %(e)s'),
                    {'id': instance.id, 'e': err}
                )


class GPUTempPollster(pollsters.GenericComputePollster):

    def get_samples(self, manager, cache, resources):
        for instance in resources:
            LOG.debug('checking instance %s', instance.id)
            try:
                if not self.inspector.inspect_cc_ga_version(instance):
                    LOG.warning('%s get gpu temperature ignored', instance)
                    continue
                counts = int(self.inspector.inspect_gpu_counts(instance))
                if counts < 1:
                    LOG.warning('%s GPU not running or drive error', instance)
                    continue
                gpu_num = {"gpu_number": counts}
                for id in range(int(counts)):
                    gpu_info = self.inspector.inspect_gpu_temperature(
                        instance,
                        id
                    )
                    LOG.debug(
                        "GPU MEMORY Temperature: %(instance)s %(size)s",
                        {'instance': instance, 'size': gpu_info.temperature}
                    )
                    resource_id = "{}_gpu{}".format(instance.id, id + 1)
                    yield util.make_sample_from_instance(
                        self.conf,
                        instance=instance,
                        resource_id=resource_id,
                        name='gpu.temperature',
                        type=sample.TYPE_GAUGE,
                        unit='C',
                        volume=gpu_info.temperature,
                        additional_metadata=gpu_num,
                    )
            except virt_inspector.InstanceNotFoundException as err:
                # Instance was deleted while getting samples. Ignore it.
                LOG.debug('Exception while getting samples %s', err)
            except virt_inspector.InstanceShutOffException as e:
                LOG.debug('Instance %(instance_id)s was shut off while '
                          'getting samples of %(pollster)s: %(exc)s',
                          {'instance_id': instance.id,
                           'pollster': self.__class__.__name__, 'exc': e})
            except ceilometer.NotImplementedError:
                # Selected inspector does not implement this pollster.
                LOG.debug(
                    'Obtaining GPU temperature is not implemented for '
                    '%s', self.inspector.__class__.__name__
                )
                raise plugin_base.PollsterPermanentError(resources)
            except Exception as err:
                LOG.exception(
                    _('could not get GPU temperature for %(id)s: %(e)s'),
                    {'id': instance.id, 'e': err}
                )
