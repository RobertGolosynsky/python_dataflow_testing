import unittest

from test.test_tracer import get_trace

import os
import unittest

from test.test_tracer import LINKED_LIST_ROOT, create_new_temp_dir

import thorough
from tracing.trace_reader import TraceReader


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

    def test_failed_tests_recorded(self):
        project_root = LINKED_LIST_ROOT
        trace_root = create_new_temp_dir()
        exclude_folders = ["venv"]

        thorough.run_tests(project_root, trace_root, exclude_folders)
        trace_reader = TraceReader(trace_root)
        failed_cases = trace_reader.read_failed_test_cases()
        self.assertEqual(1, len(failed_cases))
        expected_failed_test_case = "tests/test_list.py::LinkedListTest::test_append_on_removed"
        self.assertEqual(expected_failed_test_case, failed_cases[0])


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
