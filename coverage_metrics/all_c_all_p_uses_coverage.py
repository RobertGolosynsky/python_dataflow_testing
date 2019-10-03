import pandas as pd
from loguru import logger

from coverage_metrics.coverage_metric_enum import CoverageMetric
from coverage_metrics.statement_coverage import StatementCoverage
from coverage_metrics.util import percent
from tracing.trace_reader import read_as_np_array
from tracing.tracer import LINE_INDEX


class AllCAllPUses(StatementCoverage):
    metrics = {CoverageMetric.ALL_C_USES, CoverageMetric.ALL_P_USES}
    file_name_col = "File name"
    file_path_col = "File path"
    coverage_col = "Coverage"

    def report(self, of_type=CoverageMetric.ALL_C_USES):
        report = {}

        for module_path in self.trace_reader.files_mapping.keys():
            covered_items = self.covered_items_of(module_path, of_type=of_type)
            total_covered_items = set()
            for s in covered_items.values():
                total_covered_items.update(s)
            total_items_available = self.total_items_of(module_path, of_type=of_type)
            report[module_path] = percent(total_covered_items, total_items_available)

        report = pd.DataFrame.from_dict({self.coverage_col: report}, orient="columns")
        return report

    def total_items_of(self, module_path, of_type=None):
        module_cfg = self.project_cfg.module_cfgs[module_path]
        if of_type == CoverageMetric.ALL_C_USES:
            return module_cfg.c_uses
        elif of_type == CoverageMetric.ALL_P_USES:
            return module_cfg.p_uses
        else:
            logger.error("Unidentified metric {m}", m=of_type)
            return set()

    def covered_items_of(self, module_path, of_type=None, selected_node_ids=None) -> dict:
        covered_items = {}
        node_ids, paths = self.trace_reader.get_traces_for(module_path=module_path,
                                                           selected_node_ids=selected_node_ids)
        total_items = self.total_items_of(module_path, of_type=of_type)
        for node_id, trace_file_path in zip(node_ids, paths):
            df, size = read_as_np_array(trace_file_path, max_size_mb=self.max_trace_size)
            if df is not None:
                lines = df.T[LINE_INDEX]
                covered_items[node_id] = set(lines).intersection(total_items)
            else:
                covered_items[node_id] = set()
        return covered_items
