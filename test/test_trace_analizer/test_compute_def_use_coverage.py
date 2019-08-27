import unittest

from test.test_tracer import LINKED_LIST_LL, LINKED_LIST_ROOT, create_new_temp_dir
from model.cfg.project_cfg import ProjectCFG
from tracing.cpp_tracing.analize import get_trace_files, analyze_trace_w_index
from tracing.index_factory import VarIndexFactory, read_files_index
from tracing.trace_reader import read_df, read_scopes_for_trace_file
from tracing.cpp_tracing.intermethod_interclass_anaize import analyze

import thorough
from util.misc import key_where


class TestComputeCoverage(unittest.TestCase):

    def test_inter_method_pairs(self):
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
        cfg = ProjectCFG(project_root,
                         exclude_folders=exclude_folders,
                         use_cached_if_possible=False)

        thorough.run_tests(LINKED_LIST_ROOT, trace_root, exclude_folders)

        vi = VarIndexFactory.new_py_index(project_root, trace_root)
        cppvi = VarIndexFactory.new_cpp_index(project_root, trace_root)

        file_index = read_files_index(trace_root)
        ll_py = str(LINKED_LIST_LL)
        ll_py_idx = key_where(file_index, ll_py)

        def get_pairs(trace_name):
            trace_file_path = get_trace_files(trace_root, trace_name=trace_name, file_index=ll_py_idx)
            np_array, _ = read_df(trace_file_path)
            scopes = read_scopes_for_trace_file(trace_file_path)

            inter_method_pairs, intra_class_pairs = analyze(trace_file_path, vi, scopes)

            intramethod_pairs = analyze_trace_w_index(trace_file_path, cppvi)

            return rename_vars(intramethod_pairs), rename_vars(inter_method_pairs), rename_vars(intra_class_pairs)

        total_intramethod_pairs = []
        total_intermethod_pairs = []
        total_interclass_pairs = []

        for test_case in test_cases:
            intra, inter, clas = get_pairs(test_case)
            total_intramethod_pairs.extend(intra)
            total_intermethod_pairs.extend(inter)
            total_interclass_pairs.extend(clas)
        ll_py_cfg = cfg.module_cfgs[ll_py]

        print("Coverage")
        print_percent("Intramethod", total_intramethod_pairs, ll_py_cfg.intramethod_pairs)
        print_percent("Intermethod", total_intermethod_pairs, ll_py_cfg.intermethod_pairs)
        print_percent("Interclass", total_interclass_pairs, ll_py_cfg.interclass_pairs)
        total_pairs_exercised = total_interclass_pairs + total_intermethod_pairs + total_intramethod_pairs
        total_pairs_possible = ll_py_cfg.interclass_pairs + ll_py_cfg.intermethod_pairs + ll_py_cfg.intramethod_pairs

        print_percent("Total unique pairs", total_pairs_exercised, total_pairs_possible)
        not_exercised_pairs = only_lines(set(total_pairs_possible)) - set(total_pairs_exercised)
        print("Not exercised pairs total ({}): ".format(len(not_exercised_pairs)), not_exercised_pairs)
        print("total intermethod", ll_py_cfg.intermethod_pairs)

        self.assertEqual(3, len(not_exercised_pairs))


def print_percent(text, given, total):
    a = len(set(given))
    b = len(set(total))
    if b == 0:
        percent = 100
    else:
        percent = a * 100 / b
    print("{}: found {} / total {} | {}%".format(text, a, b, int(percent)))


def only_lines(s):
    return {(pair.definition.line, pair.use.line) for pair in s}


def rename_vars(s):
    return {(el[0], el[1]) for el in s}
