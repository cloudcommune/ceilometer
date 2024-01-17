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

import abc
import six

from oslo_log import log
from six.moves.urllib import parse as urlparse

from ceilometer.objectstore import cloudcommune_oss_client

LOG = log.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class Driver(object):
    def __init__(self, conf):
        self.conf = conf

    @abc.abstractmethod
    def get_sample_data(self, meter_name, parse_url, params, cache):
        """Return volume, resource_id, resource_metadata, timestamp in tuple.

        If not implemented for meter_name, returns None
        """


class CloudCommuneOSSDriver(Driver):

    def _prepare_cache(self, endpoint, params, cache):
        s = urlparse.urlparse(endpoint)
        keys = ['objectstore.cloudcommuneoss']
        keys.extend(s.netloc.split(":"))
        cache_key = '.'.join(keys)
        if cache_key in cache:
            return cache[cache_key]
        oss_obj = cloudcommune_oss_client.CloudCommuneOssClient(endpoint)
        data = oss_obj.get_usage()
        cache[cache_key] = data
        return data

    def _get_oss_data(self, parse_url, params, cache):
        parts = urlparse.ParseResult(params.get('scheme', ['http'])[0],
                                     parse_url.netloc,
                                     parse_url.path,
                                     None,
                                     None,
                                     None)
        endpoint = urlparse.urlunparse(parts)
        data = self._prepare_cache(endpoint, params, cache)
        LOG.debug("tek add data is %s" % data)
        return data

    def _get_oss_bucket_sample_data(self, meter_name, parse_url, params,
                                    cache):
        """Functions to get sample data for meters:

        bucket.standard.storage.size
        """
        return self._get_oss_data(
            parse_url, params, cache).get("standardStorageList", [])

    def _get_oss_fee_bucket_sample_data(self, meter_name,
                                        parse_url, params, cache):
        """Functions to get sample data for meters:

        bucket.fee.standard.storage.size
        """
        return self._get_oss_data(
            parse_url, params, cache).get("feeStandardStorageList", [])

    def _get_extractor(self, meter_name):
        method_name = '_' + meter_name.replace('.', '_')
        return getattr(self, method_name, None)

    def _get_sample_extractor(self, meter_name):
        if meter_name.startswith('bucket.standard.storage'):
            return self._get_oss_bucket_sample_data
        elif meter_name.startswith('bucket.fee.standard.storage'):
            return self._get_oss_fee_bucket_sample_data
        return None

    def get_sample_data(self, meter_name, parse_url, params, cache):
        sample_extractor = self._get_sample_extractor(meter_name)
        if sample_extractor is None:
            # The extractor for this meter is no implemented or the API
            # doesn't have method to get this meter.
            return
        return sample_extractor(meter_name, parse_url, params, cache)

    @staticmethod
    def _bucket_fee_standard_storage_size(statistic, resource_id,
                                          resource_meta):
        return int(statistic), resource_id, resource_meta

    @staticmethod
    def _bucket_standard_storage_size(statistic, resource_id, resource_meta):
        return int(statistic), resource_id, resource_meta
