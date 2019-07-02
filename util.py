import os
from itertools import tee


def listdir_fullpath(d):
    return [os.path.join(d, f) for f in os.listdir(d)]


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)