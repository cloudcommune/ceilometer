# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
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

"""Simple wrapper for oslo_cache."""

# NOTE(xiexianbin): this file is copied for nova and should be kept in sync
# until we can use external library for this.

from oslo_cache import core as cache
from oslo_config import cfg
from oslo_log import log as logging

from ceilometer.i18n import _LW, _


LOG = logging.getLogger(__name__)

WEEK = 604800


def _warn_if_null_backend(conf):
    if conf.cache.backend == 'dogpile.cache.null':
        LOG.warning(_LW("Cache enabled with backend dogpile.cache.null."))


def get_memcached_client(conf=None, expiration_time=0):
    """Used ONLY when memcached is explicitly needed."""
    if conf is None:
        conf = cfg.ConfigOpts()
        cache.configure(conf)

    # If the operator has [cache]/enabled flag on then we let oslo_cache
    # configure the region from the configuration settings
    if conf.cache.enabled and conf.cache.memcache_servers:
        _warn_if_null_backend(conf)
        return CacheClient(
            _get_default_cache_region(conf, expiration_time=expiration_time))


def get_client(conf=None, expiration_time=0):
    """Used to get a caching client."""
    if conf is None:
        conf = cfg.ConfigOpts()
        cache.configure(conf)

    # If the operator has [cache]/enabled flag on then we let oslo_cache
    # configure the region from configuration settings.
    if conf.cache.enabled:
        _warn_if_null_backend(conf)
        return CacheClient(
            _get_default_cache_region(conf, expiration_time=expiration_time))
    # If [cache]/enabled flag is off, we use the dictionary backend
    return CacheClient(
        _get_custom_cache_region(expiration_time=expiration_time,
                                 backend='oslo_cache.dict'))


def _get_default_cache_region(conf, expiration_time):
    region = cache.create_region()
    if expiration_time != 0:
        conf.cache.expiration_time = expiration_time
    cache.configure_cache_region(conf, region)
    return region


def _get_custom_cache_region(expiration_time=WEEK,
                             backend=None,
                             url=None):
    """Create instance of oslo_cache client.

    For backends you can pass specific parameters by kwargs.
    For 'dogpile.cache.memcached' backend 'url' parameter must be specified.

    :param backend: backend name
    :param expiration_time: interval in seconds to indicate maximum
        time-to-live value for each key
    :param url: memcached url(s)
    """

    region = cache.create_region()
    region_params = {}
    if expiration_time != 0:
        region_params['expiration_time'] = expiration_time

    if backend == 'oslo_cache.dict':
        region_params['arguments'] = {'expiration_time': expiration_time}
    elif backend == 'dogpile.cache.memcached':
        region_params['arguments'] = {'url': url}
    else:
        raise RuntimeError(_('old style configuration can use '
                             'only dictionary or memcached backends'))

    region.configure(backend, **region_params)
    return region


class CacheClient(object):
    """Replicates a tiny subset of memcached client interface."""

    def __init__(self, region):
        self.region = region

    def get(self, key):
        value = self.region.get(key)
        if value == cache.NO_VALUE:
            return None
        return value

    def get_or_create(self, key, creator):
        return self.region.get_or_create(key, creator)

    def set(self, key, value):
        return self.region.set(key, value)

    def add(self, key, value):
        return self.region.get_or_create(key, lambda: value)

    def delete(self, key):
        return self.region.delete(key)

    def get_multi(self, keys):
        values = self.region.get_multi(keys)
        return [None if value is cache.NO_VALUE else value for value in
                values]

    def delete_multi(self, keys):
        return self.region.delete_multi(keys)
