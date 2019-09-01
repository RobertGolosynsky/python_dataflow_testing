import unittest

import unittest

from test.test_tracer import LINKED_LIST_LL, LINKED_LIST_ROOT, create_new_temp_dir
from model.cfg.project_cfg import ProjectCFG
from tracing.cpp_tracing.analize import get_trace_files, analyze_trace_w_index
from tracing.index_factory import VarIndexFactory, read_files_index
from tracing.trace_reader import read_df, read_scopes_for_trace_file
from tracing.cpp_tracing.intermethod_interclass_anaize import analyze

import thorough
from tracing.tracer import LINE_INDEX
from util.misc import key_where


class TestBranchCoverage(unittest.TestCase):

    def test_branch_coverage(self):
        test_cases = [
            "test_append_when_empty",
            "test_append_when_not_empty",
            "test_remove_when_empty",
            "test_remove_when_not_empty",
            "test_remove_middle",
            "test_len",
            "test_get",
            "test_get_empty",
            "test_get_out_bounds",
            "test_create_from_list",
            "test_as_list",
            "test_len_large_list",
            "test_len_on_empty",
            "test_as_list_on_empty",
            "test_append_on_removed",
            "test_get_middle",
            "test_remove_first_as_list",
            "test_remove_twice_when_not_empty",
            "test_remove_first_append"
        ]

        project_root = LINKED_LIST_ROOT
        trace_root = create_new_temp_dir()
        print(trace_root)
        exclude_folders = ["venv"]
        cfg = ProjectCFG.create_from_path(project_root,
                         exclude_folders=exclude_folders,
                         use_cached_if_possible=False)

        thorough.run_tests(LINKED_LIST_ROOT, trace_root, exclude_folders)

        file_index = read_files_index(trace_root)
        ll_py = str(LINKED_LIST_LL)
        ll_py_idx = key_where(file_index, ll_py)
        ll_py_cfg = cfg.module_cfgs[ll_py]

        def get_covered_lines(trace_name):
            trace_file_path = get_trace_files(trace_root, trace_name=trace_name, file_index=ll_py_idx)
            np_array, _ = read_df(trace_file_path)
            return np_array.T[LINE_INDEX]

        total_exercised = []
        available_branches = set(ll_py_cfg.branches)
        for test_case in test_cases:
            lines = get_covered_lines(test_case)
            total_exercised.extend(l for l in lines if l in available_branches)

        print("Coverage")
        print_percent("Branches covered", total_exercised, ll_py_cfg.branches)
        not_exercised_branches = set(available_branches) - set(total_exercised)
        print("Not exercised branches total ({}): ".format(len(not_exercised_branches)), not_exercised_branches)
        self.assertEqual(8, len(not_exercised_branches))


def print_percent(text, given, total):
    a = len(set(given))
    b = len(set(total))
    if b == 0:
        percent = 100
    else:
        percent = a * 100 / b
    print("{}: found {} / total {} | {}%".format(text, a, b, int(percent)))
