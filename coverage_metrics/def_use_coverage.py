from collections import namedtuple, defaultdict
import pandas as pd

from coverage_metrics.coverage_interface import Coverage
from coverage_metrics.util import percent
from coverage_metrics.coverage_metric_enum import CoverageMetric
from model.cfg.project_cfg import ProjectCFG
from model.test_case import TestCase
from tracing.cpp_tracing.analize import analyze_trace_w_index
from tracing.cpp_tracing.intermethod_interclass_anaize import analyze
from tracing.index_factory import VarIndexFactory
from tracing.trace_reader import read_files_index, read_df, get_trace_files, \
    trace_path_to_tracee_index_and_test_case, read_scopes_for_trace_file, get_traces_for_tracee
from util.misc import key_where

row = namedtuple("row", ["test_case", "module_under_test",
                         "intramethod_pairs", "intermethod_pairs", "interclass_pairs"])


class DefUsePairsCoverage(Coverage):
    file_name_col = "File name"
    file_path_col = "File path"
    m_col = "M {}"
    im_col = "IM {}"
    ic_col = "IC {}"

    def __init__(self, trace_root, project_root, exclude_folders=None, max_trace_size=None):
        self.project_cfg = ProjectCFG.create_from_path(project_root,
                                                       exclude_folders=exclude_folders,
                                                       use_cached_if_possible=True)
        self.max_trace_size = max_trace_size
        self.trace_root = trace_root
        self.files_index = read_files_index(trace_root)
        self.vi = VarIndexFactory.new_py_index(project_root, trace_root)
        self.cppvi = VarIndexFactory.new_cpp_index(project_root, trace_root)

    def report(self):
        collected_pairs = self.collect_pairs()
        report = {}
        for module_index, items in self.group_items_by_key(collected_pairs, "module_under_test").items():

            tracee_path = self.files_index[module_index]
            module_cfg = self.project_cfg.module_cfgs.get(tracee_path)
            if module_cfg:
                m_tot = set()
                im_tot = set()
                ic_tot = set()
                for item in items:
                    m_tot.update(item.intramethod_pairs)
                    im_tot.update(item.intermethod_pairs)
                    ic_tot.update(item.interclass_pairs)
                d = {}
                d[self.m_col.format("")] = percent(m_tot, module_cfg.intramethod_pairs)
                d[self.im_col.format("")] = percent(im_tot, module_cfg.intermethod_pairs)
                d[self.ic_col.format("")] = percent(ic_tot, module_cfg.interclass_pairs)
                all_pairs_possible = set(module_cfg.intramethod_pairs) | set(module_cfg.intermethod_pairs) | set(
                    module_cfg.interclass_pairs)
                d["Total"] = percent(m_tot | im_tot | ic_tot, all_pairs_possible)
                report[module_index] = d

        return pd.DataFrame.from_dict(report, orient="index")

    def report_per_test_case(self):
        collected_pairs = self.collect_pairs()
        report = {}
        trailing_row = {}
        for test_case, items in self.group_items_by_key(collected_pairs, "test_case").items():
            d = {}
            for item in items:
                tracee_index = item.module_under_test
                tracee_path = self.files_index[tracee_index]
                module_cfg = self.project_cfg.module_cfgs.get(tracee_path)
                intra_cov = None
                inter_cov = None
                inter_c_cov = None

                if module_cfg:
                    intra_cov = percent(item.intramethod_pairs, module_cfg.intramethod_pairs)
                    inter_cov = percent(item.intermethod_pairs, module_cfg.intermethod_pairs)
                    inter_c_cov = percent(item.interclass_pairs, module_cfg.interclass_pairs)
                d[self.m_col.format(tracee_index)] = intra_cov
                d[self.im_col.format(tracee_index)] = inter_cov
                d[self.ic_col.format(tracee_index)] = inter_c_cov
            report[test_case.function_name[-10:]] = d
        for path, module_cfg in self.project_cfg.module_cfgs.items():
            module_index = key_where(self.files_index, path)
            if module_index is not None:
                trailing_row[self.m_col.format(module_index)] = len(module_cfg.intramethod_pairs)
                trailing_row[self.im_col.format(module_index)] = len(module_cfg.intermethod_pairs)
                trailing_row[self.ic_col.format(module_index)] = len(module_cfg.interclass_pairs)
        report["Total pairs available"] = trailing_row

        return pd.DataFrame.from_dict(report, orient="index")

    def collect_pairs(self):
        analyzed_traces = []
        for trace_file in get_trace_files(self.trace_root):
            index, test_case = trace_path_to_tracee_index_and_test_case(trace_file)
            pairs = self.get_pairs(trace_file)
            r = row(test_case, index, *pairs)
            analyzed_traces.append(r)
        return analyzed_traces

    def get_pairs(self, trace_file_path):
        np_array, fsize = read_df(trace_file_path, max_size_mb=self.max_trace_size)

        if np_array is None:
            return set(), set(), set()

        scopes = read_scopes_for_trace_file(trace_file_path)

        if not scopes:
            return set(), set(), set()

        inter_method_pairs, intra_class_pairs = analyze(trace_file_path, self.vi, scopes)
        intramethod_pairs = analyze_trace_w_index(trace_file_path, self.cppvi)
        return rename_vars(intramethod_pairs), rename_vars(inter_method_pairs), rename_vars(intra_class_pairs)

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

    def covered_items_of(self, module_path, of_type=CoverageMetric.ALL_PAIRS) -> dict:
        tracee_index = key_where(self.files_index, value=module_path)
        report = {}
        for test_case, trace_file_path in get_traces_for_tracee(self.trace_root, tracee_index):
            test_case = TestCase.from_folder_name(test_case)
            np_array, fsize = read_df(trace_file_path, max_size_mb=self.max_trace_size)
            if np_array is None:
                continue

            scopes = read_scopes_for_trace_file(trace_file_path)
            if not scopes:
                continue

            if of_type == CoverageMetric.M_ONLY:
                mp = analyze_trace_w_index(trace_file_path, self.cppvi)
                report[test_case] = rename_vars(mp)
            elif of_type == CoverageMetric.IM_ONLY:
                imp, icp = analyze(trace_file_path, self.vi, scopes)
                report[test_case] = rename_vars(imp)
            elif of_type == CoverageMetric.IC_ONLY:
                imp, icp = analyze(trace_file_path, self.vi, scopes)
                report[test_case] = rename_vars(icp)
            elif of_type == CoverageMetric.M_AND_IM:
                mp = analyze_trace_w_index(trace_file_path, self.cppvi)
                imp, icp = analyze(trace_file_path, self.vi, scopes)
                report[test_case] = rename_vars(mp) | rename_vars(imp)
            elif of_type == CoverageMetric.M_AND_IC:
                mp = analyze_trace_w_index(trace_file_path, self.cppvi)
                imp, icp = analyze(trace_file_path, self.vi, scopes)
                report[test_case] = rename_vars(mp) | rename_vars(icp)
            elif of_type == CoverageMetric.IM_AND_IC:
                imp, icp = analyze(trace_file_path, self.vi, scopes)
                report[test_case] = rename_vars(imp) | rename_vars(icp)
            elif of_type == CoverageMetric.ALL_PAIRS:
                mp = analyze_trace_w_index(trace_file_path, self.cppvi)
                imp, icp = analyze(trace_file_path, self.vi, scopes)
                report[test_case] = rename_vars(mp) | rename_vars(imp) | rename_vars(icp)
            else:
                raise ValueError("Unknown coverage metric {} in parameter 'of_type'".format(of_type))
        return report


def rename_vars(s):
    return {(el[0], el[1]) for el in s}


def only_lines(s):
    return {(pair.definition.line, pair.use.line) for pair in s}
