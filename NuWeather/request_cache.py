"""Helpers to manage cached JSON queries"""

import json
import os.path
import time

from supybot import log, utils

def check_cache_outdated(cache_path, cache_ttl):
    if not os.path.exists(cache_path) or \
            (time.time() - os.path.getmtime(cache_path)) > cache_ttl:
        log.debug('NuWeather.request_cache: cache file %s is missing or out of date (TTL=%s)', cache_path, cache_ttl)
        return True
    return False

def get_json_save_cache(url, cache_path, headers):
    log.debug('NuWeather.request_cache: fetching %s', url)
    data_text = utils.web.getUrl(url, headers=headers).decode('utf-8')
    with open(cache_path, 'w', encoding='utf-8') as f:
        log.debug('NuWeather.request_cache: saving %s to %s', url, cache_path)
        f.write(data_text)
    return json.loads(data_text)

def load_json_cache(cache_path):
    with open(cache_path, encoding='utf-8') as f:
        log.debug('NuWeather.request_cache: reloading existing %s', cache_path)
        return json.load(f)
