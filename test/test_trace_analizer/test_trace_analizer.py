import os
import unittest
from time import time

from test.test_tracer import trace_this, PROJECT_ROOT, LINKED_LIST_LL, LINKED_LIST_ROOT, \
    create_new_temp_dir
from graphs.draw import source_w_pairs
from model.cfg.project_cfg import ProjectCFG
from tracing.cpp_tracing.analize import analyze_trace, analyze_trace_w_index, get_trace_files
from tracing.index_factory import VarIndexFactory, read_files_index
from util.astroid_util import compile_module
from tracing.trace_reader import read_df
from cpp.cpp_import import load_cpp_extension

import thorough
from util.misc import key_where

cpp_def_use = load_cpp_extension("def_use_pairs_ext")
cpp_find_pairs = cpp_def_use.findPairsIndex


class TestTraceAnalyzer(unittest.TestCase):

    def test_intra_method_pairs(self):
        test_cases = ["test_append_when_empty",
                      "test_append_when_not_empty",
                      "test_len",
                      "test_get",
                      "test_get_empty",
                      "test_get_out_bounds"]
        len_pairs = [10, 15, 14, 10, 5, 18]
        project_root = LINKED_LIST_ROOT
        trace_root = create_new_temp_dir()
        exclude_folders = ["venv"]
        cfg = ProjectCFG(project_root, exclude_folders=exclude_folders)

        thorough.runTests(LINKED_LIST_ROOT, trace_root, exclude_folders)

        cppvi = VarIndexFactory.new_cpp_index(project_root, trace_root)
        file_index = read_files_index(trace_root)
        ll_py = str(LINKED_LIST_LL)
        ll_py_idx = key_where(file_index, ll_py)

        def get_pairs(trace_name):
            trace_file = get_trace_files(trace_root, trace_name=trace_name, file_index=ll_py_idx)
            np_array, _ = read_df(trace_file)
            idx_pairs = analyze_trace_w_index(trace_file, cppvi)

            def rename_vars(s):
                return {(el[0], el[1]) for el in s}

            idx_pairs = rename_vars(idx_pairs)
            return idx_pairs
        for test_case, count in zip(test_cases, len_pairs):
            pairs = get_pairs(test_case)
            self.assertEqual(count, len(pairs), "Pairs count don't match for test case: {}".format(test_case))
