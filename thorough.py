from loguru import logger
import os
from pathlib import Path
import pytest

from coverage_metrics.branch_coverage import BranchCoverage
from coverage_metrics.def_use_coverage import DefUsePairsCoverage
from coverage_metrics.statement_coverage import StatementCoverage
from model.test_case import TestCase
from test.test_tracer import create_new_temp_dir
from tracing.tracer import Tracer


class MyPlugin:
    def __init__(self, tracer):
        self.tracer = tracer

    def pytest_runtest_call(self, item):
        rel_path, line, class_and_method = item.location
        cls = ""
        if "." in class_and_method:
            cls, method = class_and_method.split(".")
        else:
            method = class_and_method
        test_case = TestCase(rel_path, cls, method)
        logger.info("Running test case {case}", case=test_case)
        self.tracer.start(trace_name=test_case)

    def pytest_runtest_teardown(self, item):
        self.tracer.stop()


def run_tests(project_root, trace_root,
              exclude_folders=None,
              show_time_per_test=True,
              deselect_tests=None
              ):
    if not exclude_folders:
        exclude_folders = []
    ignore_dirs_expanded = [str((Path(project_root) / d).resolve()) for d in exclude_folders]
    t = Tracer(
        [
            str(project_root),
        ],
        ignore_dirs_expanded,
        trace_folder_parent=trace_root
    )

    pytest_params = []
    pytest_params += ["--ignore=" + d for d in exclude_folders]

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

    t.fullstop()
    os.chdir(current_working_dir)


if __name__ == "__main__":
    # trace_root = create_new_temp_dir()
    trace_root = "/tmp/thorough/2019-08-28_02-17-10-800489/"
    project_root = str(Path("").resolve())
    exclude_folders = ["dataset", "venv"]
    # run_tests(project_root, trace_root,
    #           exclude_folders=exclude_folders,
    #           deselect_tests=[
    #               ""
    #           ]
    #
    #           )
    coverage_exclude = exclude_folders+["test"]

    import pandas as pd

    pd.options.display.width = 0
    pd.options.display.float_format = '{:,.2f}'.format
    max_size = 100
    stcoverage = StatementCoverage(trace_root, project_root, exclude_folders=coverage_exclude, max_trace_size=max_size)
    brcoverage = BranchCoverage(trace_root, project_root, exclude_folders=coverage_exclude, max_trace_size=max_size)
    ducoverage = DefUsePairsCoverage(trace_root, project_root, exclude_folders=coverage_exclude, max_trace_size=max_size)
    streport = stcoverage.report()
    brreport = brcoverage.report()
    dureport = ducoverage.report()
    merged_report: pd.DataFrame = pd.concat([streport, brreport, dureport], axis=1)
    merged_report = merged_report[pd.notnull(merged_report['StCov'])]
    print(merged_report)
