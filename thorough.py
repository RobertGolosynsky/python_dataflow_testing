from loguru import logger
import os
from pathlib import Path
import pytest

from model.test_case import TestCase
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


def run_tests(project_root, trace_root, exclude_folders=None, show_time_per_test=True):
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

    current_working_dir = os.curdir
    os.chdir(project_root)
    pytest.main(
        pytest_params,
        plugins=[MyPlugin(tracer=t)],
    )

    t.fullstop()
    os.chdir(current_working_dir)


if __name__ == "__main__":
    here = str(Path("").resolve())
    run_tests(here, here, exclude_folders=["dataset", "venv"])
