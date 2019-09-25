import pandas as pd

from coverage_metrics.coverage_interface import Coverage
from coverage_metrics.util import percent
from graphs.keys import LINE_KEY
from model.cfg.project_cfg import ProjectCFG
from tracing.trace_reader import TraceReader, read_as_np_array
from tracing.tracer import LINE_INDEX

from loguru import logger


class StatementCoverage(Coverage):
    file_name_col = "Fname"
    file_path_col = "Fpath"
    coverage_col = "StCov"

    def __init__(self, trace_root, project_root, exclude_folders=None, max_trace_size=None, use_cached_if_possible=True):
        self.max_trace_size = max_trace_size
        self.project_cfg = ProjectCFG.create_from_path(project_root, exclude_folders=exclude_folders,
                                                       use_cached_if_possible=use_cached_if_possible)
        self.trace_root = trace_root
        self.trace_reader = TraceReader(self.trace_root)

    def report(self):
        logger.info("Generating statement coverage report")
        statements_per_module = self._lines_per_module()
        coverage_per_module = self.covered_statements_per_module()
        report = {}

        for module_path in coverage_per_module:
            if module_path in statements_per_module:
                covered_statements = coverage_per_module[module_path]
                cfg_statements = statements_per_module[module_path]
                covered_cfg_statements = covered_statements.intersection(cfg_statements)
                report[module_path] = percent(covered_cfg_statements,
                                              cfg_statements)

        report = pd.DataFrame.from_dict({self.coverage_col: report}, orient="columns")
        return report

    def covered_statements_per_module(self):
        logger.info("Counting covered statements per module")
        covered = self.covered_statements()
        data = {}
        for module_path in covered:
            all_covered_statements = set()
            for node_id in covered[module_path]:
                all_covered_statements |= covered[module_path][node_id]
            data[module_path] = all_covered_statements

        return data

    def covered_statements(self):
        logger.info("Counting covered statements per module and test case")
        data = {}
        modules_paths = self.trace_reader.files_mapping.keys()
        for module_path in modules_paths:
            data[module_path] = self.covered_items_of(module_path)

        return data

    def _lines_per_module(self):
        logger.info("Counting lines per module")
        statements_per_module = {}
        for module_path in self.project_cfg.module_cfgs:
            statements_per_module[module_path] = self.total_items_of(module_path)
        return statements_per_module

    # TODO: can be moved into ModuleCFG
    @staticmethod
    def lines_in_module(module_cfg):
        statements = set()
        for func_name, func_cfg in module_cfg.walk():
            g = func_cfg.cfg.g
            for node, data in g.nodes(data=True):
                line = data.get(LINE_KEY, -1)
                if line > 0:
                    statements.add(line)
        return statements

    def total_items_of(self, module_path, of_type=None):
        module_cfg = self.project_cfg.module_cfgs[module_path]
        return self.lines_in_module(module_cfg)

    def covered_items_of(self, module_path, of_type=None, selected_node_ids=None) -> dict:
        covered_lines = {}
        node_ids, paths = self.trace_reader.get_traces_for(module_path=module_path,
                                                           selected_node_ids=selected_node_ids)
        total_items = self.total_items_of(module_path)
        for node_id, trace_file_path in zip(node_ids, paths):
            df, size = read_as_np_array(trace_file_path, max_size_mb=self.max_trace_size)
            if df is not None:
                lines = df.T[LINE_INDEX]
                covered_lines[node_id] = set(lines).intersection(total_items)
            else:
                covered_lines[node_id] = set()
        return covered_lines
