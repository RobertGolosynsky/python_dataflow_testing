from collections import defaultdict

import networkx as nx
from typing import Set

from loguru import logger

from coverage_metrics.statement_coverage import StatementCoverage
from coverage_metrics.util import percent
from graphs.keys import LINE_KEY, INSTRUCTION_KEY
import pandas as pd

from tracing.trace_reader import read_df
from tracing.tracer import LINE_INDEX


def find_branch_heads(g: nx.DiGraph, branch_node):
    branch_start = g.nodes[branch_node].get(LINE_KEY)
    if branch_start is None:
        return set()

    working_list = list(g.successors(branch_node))
    branches = set()
    while len(working_list) > 0:
        cur = working_list.pop()
        instr = g.nodes[cur].get(INSTRUCTION_KEY)
        if not instr:
            continue
        if instr.starts_line:
            cur_line = g.nodes[cur].get(LINE_KEY)
            if cur_line != branch_start:
                branches.add((branch_start, cur_line))
            else:
                working_list.extend(list(g.successors(cur)))
        else:
            next_after_cur = list(g.successors(cur))
            if len(next_after_cur) == 1:
                next = next_after_cur[0]
                instr = g.nodes[next].get(INSTRUCTION_KEY)
                if instr and instr.starts_line:
                    cur_line = g.nodes[next].get(LINE_KEY)
                    if cur_line and cur_line != branch_start:
                        branches.add((branch_start, cur_line))

        # else:
        #     cur = next_node_linear(g, cur)
        #     if cur:
        #         cur_line = g.nodes[cur].get(LINE_KEY)
        #         if cur_line != branch_start:
        #             branches.add((branch_start, cur_line))
        #         else:
        #             working_list.extend(list(g.successors(cur)))
    return branches

def next_node_linear(g:nx.DiGraph, node):
    line = g.nodes[node].get(LINE_KEY)
    while True:
        succs = list(g.successors(node))
        if len(succs) == 1:
            succ = succs[0]
            cur = g.nodes[succ].get(LINE_KEY)
            if not cur:
                return None # reached exit node potentially
            if cur>line:
                return succ
            elif cur<line:
                return None
            else:
                node = succ
        else:
            return None

def find_branches(g: nx.DiGraph) -> (dict, set):
    branching_edges = defaultdict(set)
    countable_representation = set()
    for branching_point in g.nodes():
        if g.out_degree[branching_point] > 1:
            brs = find_branch_heads(g, branching_point)
            for fr, to in brs:
                branching_edges[fr].add(to)
                countable_representation.add((fr, to))

    return branching_edges, countable_representation


def find_covered_branches(lines, branching_edges) -> Set:
    covered_branches = set()
    for line, next_line in zip(lines, lines[1:]):
        if line in branching_edges:
            if next_line in branching_edges[line]:
                covered_branches.add((line, next_line))

    return covered_branches


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

    def _branching_edges_of(self, module_path):
        tracee_module = self.project_cfg.module_cfgs.get(module_path)
        if not tracee_module:
            return set()
        branching_edges = tracee_module.branching_edges

        return branching_edges

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
        # branches = self.total_items_of(module_path)
        #
        # covered_statements = super().covered_items_of(module_path, of_type=None, selected_node_ids=selected_node_ids)
        # covered_branches_of_node_id = {}
        #
        # for node_id, lines in covered_statements.items():
        #     not_exercised_branches = branches - lines
        #     covered_branches = branches - not_exercised_branches
        #     covered_branches_of_node_id[node_id] = covered_branches
        #
        # return covered_branches_of_node_id
        #
        covered_lines = {}
        node_ids, paths = self.trace_reader.get_traces_for(module_path=module_path,
                                                           selected_node_ids=selected_node_ids)
        total_items = self.total_items_of(module_path)
        branching_edges = self._branching_edges_of(module_path)
        for node_id, trace_file_path in zip(node_ids, paths):
            df, size = read_df(trace_file_path, max_size_mb=self.max_trace_size)
            if df is not None:
                lines = df.T[LINE_INDEX]
                covered_branches = find_covered_branches(lines, branching_edges)
                covered_lines[node_id] = covered_branches.intersection(total_items)
            else:
                covered_lines[node_id] = set()
        return covered_lines
