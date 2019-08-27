import os
import unittest
from time import time

from test.test_tracer import trace_this, PROJECT_ROOT, LINKED_LIST_LL, LINKED_LIST_ROOT, \
    create_new_temp_dir
from graphs.draw import source_w_pairs
from model.cfg.project_cfg import ProjectCFG
from tracing.cpp_tracing.analize import analyze_trace, get_trace_files
from tracing.index_factory import VarIndexFactory, read_files_index
from util.astroid_util import compile_module
from tracing.trace_reader import read_df, read_scopes_for_trace_file
from tracing.cpp_tracing.intermethod_interclass_anaize import analyze

import thorough
from util.misc import key_where


class TestTraceAnalyzer(unittest.TestCase):

    def test_inter_method_pairs(self):
        test_cases = ["test_append_when_empty",
                      "test_append_when_not_empty",
                      "test_len",
                      "test_get",
                      "test_get_empty",
                      "test_get_out_bounds",
                      "test_create_from_list"
                      ]
        len_pairs = [10, 15, 10, 10, 5, 16, 0]
        project_root = LINKED_LIST_ROOT
        trace_root = create_new_temp_dir()
        print(trace_root)
        exclude_folders = ["venv"]
        cfg = ProjectCFG(project_root, exclude_folders=exclude_folders)

        thorough.run_tests(LINKED_LIST_ROOT, trace_root, exclude_folders)

        vi = VarIndexFactory.new_py_index(project_root, trace_root)
        file_index = read_files_index(trace_root)
        ll_py = str(LINKED_LIST_LL)
        ll_py_idx = key_where(file_index, ll_py)

        def get_pairs(trace_name):
            trace_file = get_trace_files(trace_root, trace_name=trace_name, file_index=ll_py_idx)
            np_array, _ = read_df(trace_file)
            scopes = read_scopes_for_trace_file(trace_file)
            inter_method_pairs, intra_class_pairs = analyze(trace_file, vi, scopes)

            def rename_vars(s):
                return {(el[0], el[1]) for el in s}

            inter_method_pairs = rename_vars(inter_method_pairs)
            intra_class_pairs = rename_vars(intra_class_pairs)

            # source_w_pairs(ll_py, inter_method_pairs, np_array[:, 2])
            # source_w_pairs(ll_py, intra_class_pairs, np_array[:, 2])
            print("inter_method_pairs: ", inter_method_pairs)
            print("intra_class_pairs: ", intra_class_pairs)
            common = set(inter_method_pairs).intersection(set(intra_class_pairs))
            print("Common pairs", len(common))

            # idx_pairs = rename_vars(idx_pairs)
            # return idx_pairs

        for test_case, count in zip(test_cases, len_pairs):
            pairs = get_pairs(test_case)
            # self.assertEqual(count, len(pairs), "Pairs count don't match for test case: {}".format(test_case))
