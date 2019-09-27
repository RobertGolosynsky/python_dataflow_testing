import functools
import os
import pickle
import shutil


class DiskCache:

    def __init__(self, location, version=0):
        self.location = location
        self.version = str(version)
        if os.path.exists(location):
            for file in os.listdir(location):
                if file != self.version:
                    shutil.rmtree(os.path.join(location, file))

    def _cache_version_location(self):
        return os.path.join(self.location, self.version)

    def _file_location(self, key):
        return os.path.join(self._cache_version_location(), key)

    def has(self, key):
        file = self._file_location(key)
        if not os.path.exists(file):
            return False
        else:
            return True

    def get_value(self, key):
        file = self._file_location(key)
        with open(file, "rb") as f:
            return pickle.load(f)

    def save_value(self, key, value):
        os.makedirs(self._cache_version_location(), exist_ok=True)
        file = self._file_location(key)
        with open(file, "wb") as f:
            pickle.dump(value, f)


def cache(_func=None, *, key=None, arg_names=None, location=None, version=None):
    def decorator(func):

        @functools.wraps(func)
        def wrapper_cache(*args, **kwargs):
            cache_key = key(**{k: v for k, v in kwargs.items() if k in arg_names})
            if not wrapper_cache.cache.has(cache_key):
                wrapper_cache.cache.save_value(cache_key, func(*args, **kwargs))
            return wrapper_cache.cache.get_value(cache_key)

        wrapper_cache.cache = DiskCache(location, version=version)
        return wrapper_cache

    if _func is None:
        return decorator
    else:
        return decorator(_func)
