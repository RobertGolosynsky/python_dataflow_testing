import os
import unittest

from coverage_metrics.branch_coverage import find_covered_branches, find_branches
from test.test_tracer import CLEAN_LINKED_LIST_LL, CLEAN_LINKED_LIST_ROOT, create_new_temp_dir
from model.cfg.project_cfg import ProjectCFG

from tracing.trace_reader import read_as_np_array, TraceReader, read_as_dataframe

import thorough
from tracing.tracer import LINE_INDEX


class TestBranchCoverage(unittest.TestCase):

    def test_branch_coverage(self):
        project_root = CLEAN_LINKED_LIST_ROOT
        # trace_root = create_new_temp_dir()
        trace_root = CLEAN_LINKED_LIST_ROOT

        exclude_folders = ["venv", "dataset"]
        cfg = ProjectCFG.create_from_path(project_root,
                                          exclude_folders=exclude_folders,
                                          use_cached_if_possible=False)

        thorough.run_tests(CLEAN_LINKED_LIST_ROOT, trace_root, exclude_folders)

        trace_reader = TraceReader(trace_root)

        ll_py = str(CLEAN_LINKED_LIST_LL)
        ll_py_cfg = cfg.module_cfgs[ll_py]

        total_exercised = set()
        available_branches = ll_py_cfg.branches

        for node_id, path in zip(*trace_reader.get_traces_for(ll_py)):
            df, size = read_as_dataframe(path)
            covered = find_covered_branches(df, ll_py_cfg.branches)
            total_exercised.update(covered)

        print("Coverage")
        print_percent("Branches covered", total_exercised, ll_py_cfg.branches)
        print(available_branches)
        print(total_exercised)
        not_exercised_branches = set(available_branches) - set(total_exercised)
        print("Not exercised branches total ({}): ".format(len(not_exercised_branches)), not_exercised_branches)
        self.assertEqual(13, len(not_exercised_branches))


def print_percent(text, given, total):
    a = len(set(given))
    b = len(set(total))
    if b == 0:
        percent = 100
    else:
        percent = a * 100 / b
    print("{}: found {} / total {} | {}%".format(text, a, b, int(percent)))
