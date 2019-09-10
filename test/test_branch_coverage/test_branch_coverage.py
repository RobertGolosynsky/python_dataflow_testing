import unittest

from test.test_tracer import LINKED_LIST_LL, LINKED_LIST_ROOT, create_new_temp_dir
from model.cfg.project_cfg import ProjectCFG

from tracing.trace_reader import read_df, TraceReader

import thorough
from tracing.tracer import LINE_INDEX


class TestBranchCoverage(unittest.TestCase):

    def test_branch_coverage(self):
        project_root = LINKED_LIST_ROOT
        trace_root = create_new_temp_dir()
        print(trace_root)
        exclude_folders = ["venv"]
        cfg = ProjectCFG.create_from_path(project_root,
                                          exclude_folders=exclude_folders,
                                          use_cached_if_possible=False)

        thorough.run_tests(LINKED_LIST_ROOT, trace_root, exclude_folders)

        trace_reader = TraceReader(trace_root)

        ll_py = str(LINKED_LIST_LL)
        ll_py_cfg = cfg.module_cfgs[ll_py]

        total_exercised = []
        available_branches = set(ll_py_cfg.branches)
        node_ids = trace_reader.folders_mapping.keys()
        for node_id in node_ids:
            lines = get_covered_lines(trace_reader, node_id, ll_py)
            total_exercised.extend(l for l in lines if l in available_branches)

        print("Coverage")
        print_percent("Branches covered", total_exercised, ll_py_cfg.branches)
        not_exercised_branches = set(available_branches) - set(total_exercised)
        print("Not exercised branches total ({}): ".format(len(not_exercised_branches)), not_exercised_branches)
        self.assertEqual(8, len(not_exercised_branches))


def get_covered_lines(trace_reader, node_id, module_path):
    _, trace_file_paths = trace_reader.get_traces_for(module_path, selected_node_ids=[node_id])
    trace_file_path = trace_file_paths[0]
    np_array, _ = read_df(trace_file_path)
    return np_array.T[LINE_INDEX]


def print_percent(text, given, total):
    a = len(set(given))
    b = len(set(total))
    if b == 0:
        percent = 100
    else:
        percent = a * 100 / b
    print("{}: found {} / total {} | {}%".format(text, a, b, int(percent)))
