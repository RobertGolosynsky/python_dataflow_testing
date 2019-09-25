import unittest

from test.test_tracer import CLEAN_LINKED_LIST_LL, CLEAN_LINKED_LIST_ROOT, create_new_temp_dir
from model.cfg.project_cfg import ProjectCFG
from tracing.cpp_tracing.analyze import analyze_trace_w_index
from tracing.cpp_tracing.intermethod_interclass_analyze import analyze
from tracing.index_factory import VarIndexFactory
from tracing.trace_reader import read_as_np_array, TraceReader, read_scopes_for_trace_file
from cpp.cpp_import import load_cpp_extension

import thorough

cpp_def_use = load_cpp_extension("def_use_pairs_ext")
cpp_find_pairs = cpp_def_use.findPairsIndex


class TestTraceAnalyzer(unittest.TestCase):

    def test_intra_method_pairs(self):
        len_pairs = [9, 8, 13, 19, 3, 20, 8, 5, 18, 16, 12, 19, 3, 18, 18, 24, 9, 2, 8]

        project_root = CLEAN_LINKED_LIST_ROOT
        trace_root = create_new_temp_dir()
        exclude_folders = ["venv"]
        cfg = ProjectCFG.create_from_path(project_root, exclude_folders=exclude_folders)

        thorough.run_tests(CLEAN_LINKED_LIST_ROOT, trace_root, exclude_folders)
        trace_reader = TraceReader(trace_root)

        cppvi = VarIndexFactory.new_cpp_index(project_root, trace_root)

        ll_py = str(CLEAN_LINKED_LIST_LL)

        def get_pairs(trace_file_path):
            np_array, _ = read_as_np_array(trace_file_path)
            idx_pairs = analyze_trace_w_index(trace_file_path, cppvi)

            def rename_vars(s):
                return {(el[0], el[1]) for el in s}

            idx_pairs = rename_vars(idx_pairs)
            return idx_pairs

        node_ids, paths = trace_reader.get_traces_for(ll_py)
        for node_id, path, expected_pairs_count in zip(node_ids, paths, len_pairs):
            pairs = get_pairs(path)
            self.assertEqual(expected_pairs_count, len(pairs),
                             "Pairs count don't match for test case: {}".format(node_id))

    def test_inter_method_pairs_test_interclass_pairs(self):
        len_im_pairs = [0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
        len_ic_pairs = [5, 2, 5, 4, 1, 4, 2, 1, 5, 5, 7, 4, 1, 10, 7, 5, 9, 1, 4]

        project_root = CLEAN_LINKED_LIST_ROOT
        trace_root = create_new_temp_dir()
        exclude_folders = ["venv"]
        cfg = ProjectCFG.create_from_path(project_root, exclude_folders=exclude_folders)

        thorough.run_tests(CLEAN_LINKED_LIST_ROOT, trace_root, exclude_folders)
        trace_reader = TraceReader(trace_root)

        cppvi = VarIndexFactory.new_py_index(project_root, trace_root)

        ll_py = str(CLEAN_LINKED_LIST_LL)

        def get_pairs(trace_file_path):
            np_array, _ = read_as_np_array(trace_file_path)
            scopes = read_scopes_for_trace_file(trace_file_path)
            im_pairs, ic_pairs = analyze(trace_file_path, cppvi, scopes)

            def rename_vars(s):
                return {(el[0], el[1]) for el in s}

            im_pairs = rename_vars(im_pairs)
            ic_pairs = rename_vars(ic_pairs)
            return im_pairs, ic_pairs

        node_ids, paths = trace_reader.get_traces_for(ll_py)
        for node_id, path, expected_im_len, expected_ic_len in zip(node_ids, paths, len_im_pairs, len_ic_pairs):
            im_pairs, ic_pairs = get_pairs(path)
            self.assertEqual(expected_im_len, len(im_pairs),
                             "Intermethod pairs count don't match for test case: {}".format(node_id))
            self.assertEqual(expected_ic_len, len(ic_pairs),
                             "Intermethod pairs count don't match for test case: {}".format(node_id))
