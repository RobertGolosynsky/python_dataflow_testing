import subprocess
from pathlib import Path

from test.test_tracer import get_trace, BUGGY_LINKED_LIST_ROOT, PROJECT_ROOT

import unittest

from test.test_tracer import create_new_temp_dir

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
        project_root = BUGGY_LINKED_LIST_ROOT

        exclude_folders = ["venv"]
        thorough_location = str(PROJECT_ROOT / "thorough.py")
        subprocess.run(f"python3 {thorough_location} -t --trace_dir {str(project_root)}", cwd=project_root, shell=True)
        trace_root = project_root
        trace_reader = TraceReader(trace_root)
        failed_cases = trace_reader.read_failed_test_cases()
        self.assertEqual(1, len(failed_cases))
        expected_failed_test_case = "tests/test_linked_list_module.py::LinkedListTest::test_append_on_removed"
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
