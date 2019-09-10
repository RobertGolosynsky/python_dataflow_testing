from loguru import logger
import os
from pathlib import Path
import pytest

from coverage_metrics.branch_coverage import BranchCoverage
from coverage_metrics.def_use_coverage import DefUsePairsCoverage
from coverage_metrics.statement_coverage import StatementCoverage
from test.test_tracer import create_new_temp_dir
from tracing.tracer import Tracer


class MyPlugin:
    def __init__(self, tracer):
        self.tracer = tracer

    def pytest_runtest_call(self, item):
        logger.info("Running test case {case}", case=item.nodeid)
        self.tracer.start(trace_name=item.nodeid)

    def pytest_runtest_teardown(self, item):
        self.tracer.stop()

    def pytest_runtest_logreport(self, report):
        if report.when == "call" and report.outcome == 'failed':
            self.tracer.mark_test_case_failed(report.nodeid)


def run_tests(project_root, trace_root,
              exclude_folders_collection=None,
              exclude_folders_tracing=None,
              show_time_per_test=True,
              deselect_tests=None
              ):
    if not exclude_folders_collection:
        exclude_folders_collection = []
    if not exclude_folders_tracing:
        exclude_folders_tracing = []
    ignore_dirs_expanded = [str((Path(project_root) / d).resolve()) for d in exclude_folders_tracing]
    t = Tracer(
        [
            str(project_root),
        ],
        ignore_dirs_expanded,
        trace_folder_parent=trace_root
    )

    pytest_params = []
    pytest_params += ["-s"]

    pytest_params += ["--ignore=" + d for d in exclude_folders_collection]

    if show_time_per_test:
        pytest_params.append("--durations=0")
    if deselect_tests and isinstance(deselect_tests, list):
        pytest_params += ["--deselect=" + d for d in deselect_tests]

    current_working_dir = os.curdir
    os.chdir(project_root)
    pytest.main(
        pytest_params,
        plugins=[MyPlugin(tracer=t)],
    )

    t.full_stop()
    os.chdir(current_working_dir)


if __name__ == "__main__":
    # TODO: add sys.agrv parsing and -help

    trace_root = create_new_temp_dir()
    project_root = str(Path("").resolve())
    exclude_folders = ["dataset", "venv"]
    run_tests(project_root, trace_root,
              exclude_folders_collection=exclude_folders,
              exclude_folders_tracing=exclude_folders + ["tests"],
              deselect_tests=[
                  "-"
              ]

              )
    coverage_exclude = exclude_folders

    import pandas as pd

    pd.options.display.width = 0
    pd.options.display.float_format = '{:,.2f}'.format
    max_size = 100
    stcoverage = StatementCoverage(trace_root, project_root, exclude_folders=coverage_exclude, max_trace_size=max_size)
    brcoverage = BranchCoverage(trace_root, project_root, exclude_folders=coverage_exclude, max_trace_size=max_size)
    ducoverage = DefUsePairsCoverage(trace_root, project_root, exclude_folders=coverage_exclude,
                                     max_trace_size=max_size)
    streport = stcoverage.report()
    brreport = brcoverage.report()
    dureport = ducoverage.report()
    merged_report: pd.DataFrame = pd.concat([streport, brreport, dureport], axis=1)
    merged_report = merged_report[pd.notnull(merged_report['StCov'])]
    print("Report:")
    print(merged_report)

    debug = True
    if debug:
        pairs = ducoverage.collect_pairs()
        grouped_by_module = ducoverage.group_items_by_key(pairs, key="module_under_test")
        file_index = ducoverage.files_index
        for module_index in grouped_by_module:
            module_path = file_index[module_index]
            module_cfg = ducoverage.project_cfg.module_cfgs[module_path]
            traces = get_traces_for_tracee(trace_root, module_index)
            print(" " * 2, "Intramethod pairs found:", module_cfg.intramethod_pairs)
            print(" " * 2, "Intermethod pairs found:", module_cfg.intermethod_pairs)
            print(" " * 2, "Interclass pair found:", module_cfg.interclass_pairs)

            print("Module under test: {}".format(module_path))
            for test_case_result in grouped_by_module[module_index]:
                # p = [path for tc, path in traces if tc == test_case_result.test_case.to_folder_name()][0]
                # import numpy as np
                # module_source = open(module_path).readlines()
                # with np.printoptions(precision=3, linewidth=100):
                #     t = read_df(p)[0]
                #     for row in t:
                #         line = row[LINE_INDEX]
                #         print(row, end="")
                #         print(module_source[line-1])

                print(" " * 4, "Test case:", test_case_result.test_case)
                print(" " * 8, "Intramethod pairs covered:", test_case_result.intramethod_pairs)
                print(" " * 8, "Intermethod pairs covered:", test_case_result.intermethod_pairs)
                print(" " * 8, "Interclass pair covered:", test_case_result.interclass_pairs)
