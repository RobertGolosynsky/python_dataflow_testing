
import unittest

from test.test_tracer import get_trace


class TestTracer(unittest.TestCase):
    def test_trace_comprehension_is_excluded(self):
        for comp in [list_comp, set_comp, dict_comp]:
            trace = get_trace(comp)
            scopes = get_unique_scopes(trace)
            self.assertEqual(1, scopes)

    def test_trace_comprehension_calls_function_is_included(self):
        trace = get_trace(has_two_scopes)
        scopes = get_unique_scopes(trace)
        self.assertEqual(2, scopes)



def has_two_scopes():
    values = [el for el in list_comp()]


def get_unique_scopes(trace):
    return len(set(trace[:, 4]))


def dict_comp():
    alist = [1, 2, 3, 4, 5, 6, -1, -2]
    f = {el: 1 for el in alist if el > 0}
    x = 3


def set_comp():
    alist = [1, 2, 3, 4, 5, 6, -1, -2]
    f = {el for el in alist if el > 0}
    x = 3


def list_comp():
    alist = [1, 2, 3, 4, 5, 6, -1, -2]
    f = [el for el in alist if el > 0]
    x = 3
    return alist
