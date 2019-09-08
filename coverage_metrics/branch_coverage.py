import os
from pathlib import Path

import networkx as nx
from typing import Set

from loguru import logger

from coverage_metrics.statement_coverage import StatementCoverage
from coverage_metrics.util import percent
from graphs.keys import LINE_KEY
from model.test_case import TestCase
from tracing.trace_reader import read_df, get_traces_for_tracee
from tracing.tracer import Tracer, LINE_INDEX
import pandas as pd
import numpy as np

from util.misc import key_where


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
    column_name = "BrCov"

    def __init__(self, trace_root, project_root, exclude_folders=None, max_trace_size=None):
        super().__init__(trace_root, project_root, exclude_folders, max_trace_size=max_trace_size)

    def test_case_module_coverage(self):
        trace_root = Path(self.trace_root) / Tracer.trace_folder
        data = {}
        for test_case_trace_root in trace_root.iterdir():
            if not test_case_trace_root.is_dir():
                continue

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

    def report(self):
        logger.info("Generating branch coverage report")
        covered_statements = self.covered_statements_per_tracee()
        data = {}
        for tracee in covered_statements:
            covered_branches = self._calculate_covered_branches(tracee, covered_statements[tracee])
            tracee_file = self.files_index[tracee]
            total_branches = self.total_items_of(tracee_file)
            data[tracee] = percent(covered_branches, total_branches)

        df = pd.DataFrame.from_dict({self.column_name: data}, orient="columns")

        return df

    def _calculate_trace_coverage(self, trace_file_path: Path, tracee_index: int):
        df, _ = read_df(trace_file_path, max_size_mb=self.max_trace_size)
        if df is not None:
            lines_exercised = set(df.T[LINE_INDEX])
        else:
            lines_exercised = set()
        covered_branches = self._calculate_covered_branches(tracee_index, lines_exercised)
        tracee_file = self.files_index[tracee_index]
        total_branches = self.total_items_of(tracee_file)
        return percent(covered_branches, total_branches)

    def _calculate_covered_branches(self, tracee_index, lines_exercised):

        tracee_file = self.files_index[tracee_index]
        branches = self.total_items_of(tracee_file)

        not_exercised_branches = branches - lines_exercised
        covered_branches = branches - not_exercised_branches
        return covered_branches

    def total_items_of(self, module_path, of_type=None):
        tracee_module = self.project_cfg.module_cfgs.get(module_path)
        if not tracee_module:
            return []
        branches = tracee_module.branches

        return branches

    def covered_items_of(self, module_path, of_type=None) -> dict:
        tracee_index = key_where(self.files_index, value=module_path)
        trace_root = Path(self.trace_root)
        branches = self.total_items_of(module_path)

        covered_branches_per_test_case = {}

        for test_case, trace_file_path in get_traces_for_tracee(trace_root, tracee_index):
            test_case = TestCase.from_folder_name(test_case)
            df, size = read_df(trace_file_path, max_size_mb=self.max_trace_size)
            if df is not None:
                lines = set(df.T[LINE_INDEX])

                not_exercised_branches = branches - lines
                covered_branches = branches - not_exercised_branches

                covered_branches_per_test_case[test_case] = covered_branches
            else:
                covered_branches_per_test_case[test_case] = set()
        return covered_branches_per_test_case
