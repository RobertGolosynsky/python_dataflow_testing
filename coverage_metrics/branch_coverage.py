import os
from pathlib import Path

import networkx as nx
from typing import Set

from coverage_metrics.statement_coverage import StatementCoverage
from graphs.keys import LINE_KEY
from model.cfg.project_cfg import ProjectCFG
from model.test_case import TestCase
from tracing.trace_reader import read_files_index, read_df, get_test_cases, get_traces_of_file
from tracing.tracer import Tracer, LINE_INDEX
import pandas as pd
import numpy as np


def first_lines_of_branches(g: nx.DiGraph) -> Set:
    first_lines = []
    for node in g.nodes():
        if g.out_degree[node] > 1:
            for successor in g.successors(node):
                line = g.nodes[successor].get(LINE_KEY)
                if line:
                    first_lines.append(line)

    return set(first_lines)


class BranchCoverage(StatementCoverage):
    column_name = "Branch coverage"

    def __init__(self, trace_root, project_root, exclude_folders=None):
        super().__init__(trace_root, project_root, exclude_folders)

    def test_case_module_coverage(self):
        trace_root = Path(self.trace_root) / Tracer.trace_folder
        data = {}
        for test_case_trace_root in trace_root.iterdir():
            if not test_case_trace_root.is_dir():
                continue
            print(test_case_trace_root)

            test_case_coverage = np.zeros(shape=len(self.files_index))
            for trace_file in test_case_trace_root.iterdir():
                if trace_file.suffix.endswith(Tracer.trace_file_ext):
                    tracee_index = int(trace_file.stem)
                    trace_file_path = test_case_trace_root / trace_file
                    cov = self._calculate_trace_coverage(trace_file_path,
                                                         tracee_index=tracee_index)
                    test_case_coverage[tracee_index] = cov

            test_case = TestCase.from_folder_name(test_case_trace_root.name)

            data[test_case] = test_case_coverage

        return pd.DataFrame.from_dict(data, orient='index')

    def module_coverage(self):
        covered_statements = self.covered_statements_per_tracee()
        data = {}
        for tracee in covered_statements:
            module_coverage = self._calculate_covered_branches(tracee, covered_statements[tracee])
            data[tracee] = module_coverage

        df = pd.DataFrame.from_dict({self.column_name: data}, orient="columns")

        return df

    def _calculate_trace_coverage(self, trace_file_path: Path, tracee_index: int):
        df, _ = read_df(trace_file_path)
        lines_exercised = set(df.T[LINE_INDEX])
        return self._calculate_covered_branches(tracee_index, lines_exercised)

    def _calculate_covered_branches(self, tracee_index, lines_exercised):

        tracee_file = self.files_index[tracee_index]
        tracee_module = self.project_cfg.module_cfgs.get(tracee_file)
        if not tracee_module:
            return 0.0
        branches = tracee_module.branches

        not_exercised_branches = branches - lines_exercised
        exercised_branches = branches - not_exercised_branches
        coverage = len(exercised_branches) * 100 / len(branches)
        return coverage