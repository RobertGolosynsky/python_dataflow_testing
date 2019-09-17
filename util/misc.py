import itertools
from functools import wraps
from pathlib import Path
from time import time


def key_where(d, value, unique=True):
    found = [k for k, v in d.items() if v == value]
    if len(found) > 0:
        if unique and len(found) == 1 or not unique:
            return found[0]
        else:
            raise ValueError("Found {} keys for value {}.".format(len(found), value))
    else:
        return None


def grouper_it(n, iterable):
    it = iter(iterable)
    while True:
        chunk_it = itertools.islice(it, n)
        try:
            first_el = next(chunk_it)
        except StopIteration:
            return
        yield itertools.chain((first_el,), chunk_it)


def timing(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time()
        result = f(*args, **kwargs)
        end = time()
        print('Elapsed time {}: {}'.format(f.__name__, end - start))
        return result

    return wrapper


def get_timing(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time()
        result = f(*args, **kwargs)
        end = time()
        return (end - start), result

    return wrapper


def scale(number, lower_bound, upper_bound):
    return lower_bound + (upper_bound - lower_bound) * number

def maybe_expand(path):
    p = Path(path)
    if p.is_absolute():
        return str(p)
    else:
        return str(p.resolve())

