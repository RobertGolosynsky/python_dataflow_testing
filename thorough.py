from loguru import logger
import os
from pathlib import Path
import pytest

from tracing.tracer import Tracer


class MyPlugin:
    def __init__(self, tracer):
        self.tracer = tracer

    @staticmethod
    def test_item_to_folder_name(item):
        return "_".join(map(str, item.location)).replace("/", "-")

    def pytest_runtest_call(self, item):
        # print(dir(item))
        # print(item.location)
        # print(item.name)
        # print(item.module)
        case_name = self.test_item_to_folder_name(item)
        logger.info("Running test case {case}", case=case_name)
        self.tracer.start(trace_name=case_name)

    def pytest_runtest_teardown(self, item):
        self.tracer.stop()


def runTests(project_root, trace_root, ignore_dirs=[], show_time_per_test=True):
    # sys.argv.append("--ignore=dataset")
    ignore_dirs_expanded = [str((Path(project_root) / d).resolve()) for d in ignore_dirs]
    t = Tracer(
        [
            str(project_root),
        ],
        ignore_dirs_expanded,
        trace_folder_parent=trace_root
    )

    pytest_params = []
    pytest_params += ["--ignore=" + d for d in ignore_dirs]

    if show_time_per_test:
        pytest_params.append("--durations=0")
    current_working_dir = os.curdir
    os.chdir(project_root)
    pytest.main(
        pytest_params,
        plugins=[MyPlugin(tracer=t)]
    )

    t.fullstop()
    os.chdir(current_working_dir)


if __name__ == "__main__":
    here = str(Path("").resolve())
    runTests(here, here, ignore_dirs=["dataset", "venv"])
