import os
from collections import namedtuple, defaultdict
from pathlib import Path
import pandas as pd

from graphs.keys import LINE_KEY
from model.cfg.project_cfg import ProjectCFG
from model.test_case import TestCase
from tracing.cpp_tracing.analize import analyze_trace_w_index
from tracing.cpp_tracing.intermethod_interclass_anaize import analyze
from tracing.index_factory import VarIndexFactory
from tracing.trace_reader import read_files_index, get_traces_of_file, read_df, get_trace_files, \
    trace_path_to_tracee_index_and_test_case, read_scopes_for_trace_file
from tracing.tracer import LINE_INDEX
from util.misc import key_where

row = namedtuple("row", ["test_case", "module_under_test",
                         "intramethod_pairs", "intermethod_pairs", "interclass_pairs"])


class DefUsePairsCoverage:
    file_name_col = "File name"
    file_path_col = "File path"
    m_col = "M {}"
    im_col = "IM {}"
    ic_col = "IC {}"

    def __init__(self, trace_root, project_root, exclude_folders=None):
        self.project_cfg = ProjectCFG(project_root, exclude_folders=exclude_folders+["test"],
                                      use_cached_if_possible=False)
        self.trace_root = trace_root
        self.files_index = read_files_index(trace_root)
        self.vi = VarIndexFactory.new_py_index(project_root, trace_root)
        self.cppvi = VarIndexFactory.new_cpp_index(project_root, trace_root)

    # def report(self):
    #     statements_per_module = self._lines_per_module()
    #     coverage_per_tracee = self.covered_statements_per_tracee()
    #     report = {}
    #     for tracee in coverage_per_tracee:
    #         module_path = self.files_index[tracee]
    #         report[tracee] = len(coverage_per_tracee[tracee]) * 100 / len(statements_per_module[module_path])
    #
    #     df = pd.DataFrame.from_dict({self.coverage_col: report}, orient="columns")
    #
    #     files = pd.DataFrame.from_dict({self.file_path_col: self.files_index})
    #     report = pd.merge(files, df, left_index=True, right_index=True)
    #     # TODO: just create in a way that we don't need to rearrange
    #     report[self.file_name_col] = [os.path.basename(f) for f in report[self.file_path_col]]
    #     report = report[[self.file_name_col, self.coverage_col, self.file_path_col]]
    #     return report

    def report(self):
        collected_pairs = self.collect_pairs()
        report = {}
        for module_index, items in self.group_items_by_key(collected_pairs, "module_under_test").items():
            d = {}

            tracee_path = self.files_index[module_index]
            module_cfg = self.project_cfg.module_cfgs.get(tracee_path)

            m_tot = set()
            im_tot = set()
            ic_tot = set()
            for item in items:
                m_tot.update(item.intramethod_pairs)
                im_tot.update(item.intermethod_pairs)
                ic_tot.update(item.interclass_pairs)
            d = {}
            d[self.m_col.format("")] = self.percent_covered(m_tot, module_cfg.intramethod_pairs)
            d[self.im_col.format("")] = self.percent_covered(im_tot, module_cfg.intermethod_pairs)
            d[self.ic_col.format("")] = self.percent_covered(ic_tot, module_cfg.interclass_pairs)
            all_pairs_possible = set(module_cfg.intramethod_pairs)|set(module_cfg.intermethod_pairs)|set(module_cfg.interclass_pairs)
            d["Total"] = self.percent_covered(m_tot|im_tot|ic_tot, all_pairs_possible)
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
                    intra_cov = self.percent_covered(item.intramethod_pairs, module_cfg.intramethod_pairs)
                    inter_cov = self.percent_covered(item.intermethod_pairs, module_cfg.intermethod_pairs)
                    inter_c_cov = self.percent_covered(item.interclass_pairs, module_cfg.interclass_pairs)
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

    def percent_covered(self, covered, available):
        l_a = len(only_lines(available))
        if l_a == 0:
            return None
        return len(covered) * 100 / l_a

    def collect_pairs(self):
        analyzed_traces = []
        for trace_file in get_trace_files(self.trace_root):
            index, test_case = trace_path_to_tracee_index_and_test_case(trace_file)
            pairs = self.get_pairs(trace_file)
            r = row(test_case, index, *pairs)
            analyzed_traces.append(r)
        return analyzed_traces

    def get_pairs(self, trace_file_path):
        np_array, _ = read_df(trace_file_path)
        scopes = read_scopes_for_trace_file(trace_file_path)
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


def rename_vars(s):
    return {(el[0], el[1]) for el in s}


def only_lines(s):
    return {(pair.definition.line, pair.use.line) for pair in s}
