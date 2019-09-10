from collections import namedtuple, defaultdict
import pandas as pd

from coverage_metrics.coverage_interface import Coverage
from coverage_metrics.util import percent
from coverage_metrics.coverage_metric_enum import CoverageMetric
from model.cfg.project_cfg import ProjectCFG
from tracing.cpp_tracing.analize import analyze_trace_w_index
from tracing.cpp_tracing.intermethod_interclass_anaize import analyze
from tracing.index_factory import VarIndexFactory
from tracing.trace_reader import TraceReader, read_df, read_scopes_for_trace_file

row = namedtuple("row", ["test_case", "module_under_test",
                         "intramethod_pairs", "intermethod_pairs", "interclass_pairs"])


class DefUsePairsCoverage(Coverage):
    file_name_col = "File name"
    file_path_col = "File path"
    coverage_col = "Coverage"

    def __init__(self, trace_root, project_root, exclude_folders=None, max_trace_size=None):
        self.project_cfg = ProjectCFG.create_from_path(project_root,
                                                       exclude_folders=exclude_folders,
                                                       use_cached_if_possible=True)
        self.max_trace_size = max_trace_size
        self.trace_root = trace_root
        self.trace_reader = TraceReader(trace_root)
        self.vi = VarIndexFactory.new_py_index(project_root, trace_root)
        self.cppvi = VarIndexFactory.new_cpp_index(project_root, trace_root)

    def report(self, of_type=CoverageMetric.ALL_PAIRS):
        report = {}

        for module_path in self.trace_reader.files_mapping.keys():
            covered_pairs = self.covered_items_of(module_path, of_type=of_type)
            total_pairs = self.total_items_of(module_path, of_type=of_type)
            report[module_path] = percent(covered_pairs,
                                          total_pairs)

        report = pd.DataFrame.from_dict({self.coverage_col: report}, orient="columns")
        return report

    def group_items_by_key(self, items, key):
        d = defaultdict(list)
        if isinstance(key, str):
            attr = key
            key = lambda x: getattr(x, attr)
        for item in items:
            k = key(item)
            d[k].append(item)
        return d

    def total_items_of(self, module_path, of_type=CoverageMetric.ALL_PAIRS):
        module = self.project_cfg.module_cfgs.get(module_path)
        if not module:
            return []
        if of_type == CoverageMetric.M_ONLY:
            return module.intramethod_pairs
        elif of_type == CoverageMetric.IM_ONLY:
            return module.intermethod_pairs
        elif of_type == CoverageMetric.IC_ONLY:
            return module.interclass_pairs
        elif of_type == CoverageMetric.M_AND_IM:
            return module.intramethod_pairs | module.intermethod_pairs
        elif of_type == CoverageMetric.M_AND_IC:
            return module.intramethod_pairs | module.interclass_pairs
        elif of_type == CoverageMetric.IM_AND_IC:
            return module.intermethod_pairs | module.interclass_pairs
        elif of_type == CoverageMetric.ALL_PAIRS:
            return module.intramethod_pairs | module.intermethod_pairs | module.interclass_pairs
        else:
            raise ValueError("Unknown coverage metric {} in parameter 'of_type'".format(of_type))

    def covered_items_of(self, module_path, of_type=CoverageMetric.ALL_PAIRS, selected_node_ids=None) -> dict:
        data = {}
        node_ids, traces_paths = self.trace_reader.get_traces_for(module_path, selected_node_ids=selected_node_ids)
        for test_case, trace_file_path in zip(node_ids, traces_paths):
            np_array, fsize = read_df(trace_file_path, max_size_mb=self.max_trace_size)
            if np_array is None:
                continue

            scopes = read_scopes_for_trace_file(trace_file_path)
            if not scopes:
                continue

            if of_type == CoverageMetric.M_ONLY:
                mp = analyze_trace_w_index(trace_file_path, self.cppvi)
                data[test_case] = rename_vars(mp)
            elif of_type == CoverageMetric.IM_ONLY:
                imp, icp = analyze(trace_file_path, self.vi, scopes)
                data[test_case] = rename_vars(imp)
            elif of_type == CoverageMetric.IC_ONLY:
                imp, icp = analyze(trace_file_path, self.vi, scopes)
                data[test_case] = rename_vars(icp)
            elif of_type == CoverageMetric.M_AND_IM:
                mp = analyze_trace_w_index(trace_file_path, self.cppvi)
                imp, icp = analyze(trace_file_path, self.vi, scopes)
                data[test_case] = rename_vars(mp) | rename_vars(imp)
            elif of_type == CoverageMetric.M_AND_IC:
                mp = analyze_trace_w_index(trace_file_path, self.cppvi)
                imp, icp = analyze(trace_file_path, self.vi, scopes)
                data[test_case] = rename_vars(mp) | rename_vars(icp)
            elif of_type == CoverageMetric.IM_AND_IC:
                imp, icp = analyze(trace_file_path, self.vi, scopes)
                data[test_case] = rename_vars(imp) | rename_vars(icp)
            elif of_type == CoverageMetric.ALL_PAIRS:
                mp = analyze_trace_w_index(trace_file_path, self.cppvi)
                imp, icp = analyze(trace_file_path, self.vi, scopes)
                data[test_case] = rename_vars(mp) | rename_vars(imp) | rename_vars(icp)
            else:
                raise ValueError("Unknown coverage metric {} in parameter 'of_type'".format(of_type))
        return data


def rename_vars(s):
    return {(el[0], el[1]) for el in s}


def only_lines(s):
    return {(pair.definition.line, pair.use.line) for pair in s}
