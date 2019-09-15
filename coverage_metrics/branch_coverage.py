import networkx as nx
from typing import Set

from loguru import logger

from coverage_metrics.statement_coverage import StatementCoverage
from coverage_metrics.util import percent
from graphs.keys import LINE_KEY
import pandas as pd


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

    def report(self):
        logger.info("Generating branch coverage report")
        data = {}
        covered_statements = self.covered_statements_per_module()
        for module_path in self.trace_reader.files_mapping.keys():
            covered_branches = self._calculate_covered_branches(module_path, covered_statements[module_path])
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
            return []
        branches = tracee_module.branches

        return branches

    def covered_items_of(self, module_path, of_type=None, selected_node_ids=None) -> dict:
        branches = self.total_items_of(module_path)

        covered_statements = super().covered_items_of(module_path, of_type=None, selected_node_ids=selected_node_ids)
        covered_branches_of_node_id = {}

        for node_id, lines in covered_statements.items():
            not_exercised_branches = branches - lines
            covered_branches = branches - not_exercised_branches
            covered_branches_of_node_id[node_id] = covered_branches

        return covered_branches_of_node_id
