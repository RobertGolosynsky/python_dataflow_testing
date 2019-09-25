import coverage
from coverage.parser import PythonParser
from typing import Set

from loguru import logger

from coverage_metrics.statement_coverage import StatementCoverage
from coverage_metrics.util import percent
import pandas as pd

from tracing.trace_reader import read_as_dataframe
from tracing.tracer import LINE_INDEX, SCOPE_INDEX
from util.astroid_util import get_function_sources


def find_branches(module_path):
    branches = set()
    with open(module_path) as f:
        source = f.read()
        if not source:
            return set()
        for start_line, function_source in get_function_sources(module_path, source):
            parser = PythonParser(text=function_source)
            try:
                parser.parse_source()
                arcs = parser.arcs()
            except coverage.misc.NotPython as e:
                logger.error(e)
                return set()
            offset = set()
            for fr, to in arcs:
                if fr < 0 or to < 0:
                    continue

                new_fr = fr + start_line - 1
                new_to = to + start_line - 1
                offset.add((new_fr, new_to))

            branches.update(offset)
    return branches


def find_covered_branches(df: pd.DataFrame, branches) -> Set:
    possible_branches = set()
    for scope, df in df.groupby(SCOPE_INDEX - 1):
        lines = df[LINE_INDEX - 1]
        possible_branches |= set(zip(lines, lines[1:]))
    return possible_branches.intersection(branches)


class BranchCoverage(StatementCoverage):
    column_name = "BrCov"

    def __init__(self, trace_root, project_root, exclude_folders=None, max_trace_size=None,
                 use_cached_if_possible=True):
        super().__init__(trace_root, project_root, exclude_folders, max_trace_size=max_trace_size,
                         use_cached_if_possible=use_cached_if_possible)

    def report(self):
        logger.info("Generating branch coverage report")
        data = {}
        for module_path in self.trace_reader.files_mapping.keys():
            covered_branches = self.covered_items_of(module_path)
            total_branches = self.total_items_of(module_path)
            data[module_path] = percent(covered_branches, total_branches)

        df = pd.DataFrame.from_dict({self.column_name: data}, orient="columns")

        return df

    def _calculate_covered_branches(self, module_path, lines_exercised):

        branches = self.total_items_of(module_path)
        not_exercised_branches = branches - lines_exercised
        covered_branches = branches - not_exercised_branches
        return covered_branches

    def total_items_of(self, module_path, of_type=None):
        tracee_module = self.project_cfg.module_cfgs.get(module_path)
        if not tracee_module:
            return set()
        branches = tracee_module.branches

        return branches

    def covered_items_of(self, module_path, of_type=None, selected_node_ids=None) -> dict:
        covered_lines = {}
        node_ids, paths = self.trace_reader.get_traces_for(module_path=module_path,
                                                           selected_node_ids=selected_node_ids)
        total_items = self.total_items_of(module_path)
        for node_id, trace_file_path in zip(node_ids, paths):
            df, size = read_as_dataframe(trace_file_path, max_size_mb=self.max_trace_size)
            if df is not None:
                covered_branches = find_covered_branches(df, total_items)
                covered_lines[node_id] = covered_branches.intersection(total_items)
            else:
                covered_lines[node_id] = set()
        return covered_lines
