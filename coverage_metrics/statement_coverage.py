import os
from pathlib import Path
import pandas as pd

from graphs.keys import LINE_KEY
from model.cfg.project_cfg import ProjectCFG
from tracing.trace_reader import read_files_index, get_traces_of_file, read_df
from tracing.tracer import LINE_INDEX


class StatementCoverage:

    file_name_col = "Fname"
    file_path_col = "Fpath"
    coverage_col = "StCov"

    def __init__(self, trace_root, project_root, exclude_folders=None):
        self.project_cfg = ProjectCFG(project_root, exclude_folders=exclude_folders,
                                      use_cached_if_possible=False)
        self.trace_root = trace_root
        self.files_index = read_files_index(trace_root)

    def report(self):
        statements_per_module = self._lines_per_module()
        coverage_per_tracee = self.covered_statements_per_tracee()
        report = {}
        for tracee in coverage_per_tracee:
            module_path = self.files_index[tracee]
            report[tracee] = len(coverage_per_tracee[tracee]) * 100 / len(statements_per_module[module_path])

        df = pd.DataFrame.from_dict({self.coverage_col: report}, orient="columns")

        files = pd.DataFrame.from_dict({self.file_path_col: self.files_index})
        report = pd.merge(files, df, left_index=True, right_index=True)
        # TODO: just create in a way that we don't need to rearrange
        report[self.file_name_col] = [os.path.basename(f) for f in report[self.file_path_col]]
        report = report[[self.file_name_col, self.coverage_col, self.file_path_col]]
        return report

    def covered_statements_per_tracee(self):
        covered = self.covered_statements()
        data = {}
        for tracee_index in covered:
            statements_per_tracee = set()
            for test_case in covered[tracee_index]:
                statements_per_tracee |= covered[tracee_index][test_case]
            data[tracee_index] = statements_per_tracee

        return data

    def covered_statements(self):
        trace_root = Path(self.trace_root)
        data = {}

        for tracee_index in self.files_index:

            covered_lines = {}

            for test_case, trace_file_path in get_traces_of_file(trace_root, tracee_index):
                lines = read_df(trace_file_path)[0].T[LINE_INDEX]  # TODO: mb move line index to trace reader?
                covered_lines[test_case] = set(lines)

            data[tracee_index] = covered_lines

        return data

    def _lines_per_module(self):
        statements_per_module = {}
        for module_path, module_cfg in self.project_cfg.module_cfgs.items():
            statements = set()
            for func_name, func_cfg in module_cfg.walk():
                g = func_cfg.cfg.g
                for node, data in g.nodes(data=True):
                    line = data.get(LINE_KEY, -1)
                    if line > 0:
                        statements.add(line)
            statements_per_module[module_path] = statements
        return statements_per_module
