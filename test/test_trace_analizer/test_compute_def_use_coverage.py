import unittest

from test.test_tracer import CLEAN_LINKED_LIST_LL, CLEAN_LINKED_LIST_ROOT, create_new_temp_dir
from model.cfg.project_cfg import ProjectCFG
from tracing.cpp_tracing.analyze import analyze_trace_w_index
from tracing.index_factory import VarIndexFactory
from tracing.trace_reader import read_df, read_scopes_for_trace_file, TraceReader
from tracing.cpp_tracing.intermethod_interclass_analyze import analyze

import thorough


class TestComputeCoverage(unittest.TestCase):

    def test_inter_method_pairs(self):
        project_root = CLEAN_LINKED_LIST_ROOT
        trace_root = create_new_temp_dir()
        exclude_folders = ["venv"]
        cfg = ProjectCFG.create_from_path(project_root,
                                          exclude_folders=exclude_folders,
                                          use_cached_if_possible=False)

        thorough.run_tests(CLEAN_LINKED_LIST_ROOT, trace_root, exclude_folders)
        trace_reader = TraceReader(trace_root)

        vi = VarIndexFactory.new_py_index(project_root, trace_root)
        cppvi = VarIndexFactory.new_cpp_index(project_root, trace_root)
        ll_py = str(CLEAN_LINKED_LIST_LL)

        def get_pairs(trace_file_path):
            np_array, _ = read_df(trace_file_path)
            scopes = read_scopes_for_trace_file(trace_file_path)

            inter_method_pairs, intra_class_pairs = analyze(trace_file_path, vi, scopes)

            intramethod_pairs = analyze_trace_w_index(trace_file_path, cppvi)

            return rename_vars(intramethod_pairs), rename_vars(inter_method_pairs), rename_vars(intra_class_pairs)

        total_intramethod_pairs = []
        total_intermethod_pairs = []
        total_interclass_pairs = []

        node_ids, paths = trace_reader.get_traces_for(module_path=ll_py)
        for node_id, trace_path in zip(node_ids, paths):
            intra, inter, clas = get_pairs(trace_path)
            total_intramethod_pairs.extend(intra)
            total_intermethod_pairs.extend(inter)
            total_interclass_pairs.extend(clas)
        ll_py_cfg = cfg.module_cfgs[ll_py]

        print("Coverage")
        print_percent("Intramethod", total_intramethod_pairs, ll_py_cfg.intramethod_pairs)
        print_percent("Intermethod", total_intermethod_pairs, ll_py_cfg.intermethod_pairs)
        print_percent("Interclass", total_interclass_pairs, ll_py_cfg.interclass_pairs)
        total_pairs_exercised = total_interclass_pairs + total_intermethod_pairs + total_intramethod_pairs
        total_pairs_possible = ll_py_cfg.interclass_pairs | ll_py_cfg.intermethod_pairs | ll_py_cfg.intramethod_pairs

        print_percent("Total unique pairs", total_pairs_exercised, total_pairs_possible)

        not_exercised_pairs = total_pairs_possible - set(total_pairs_exercised)
        print("Not exercised pairs total ({}): ".format(len(not_exercised_pairs)), not_exercised_pairs)
        print("total intermethod", ll_py_cfg.intermethod_pairs)

        self.assertEqual(16, len(not_exercised_pairs))


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
