import contextlib
import os
import sys

import py.io
import pytest
import json

EXCEPTIONS_FILE = ".exceptions.json"


def get_test(longrepr):
    tw = py.io.TerminalWriter(stringio=True)
    tw.hasmarkup = False
    longrepr.toterminal(tw)
    return tw.stringio.getvalue()


class FailedTestCasesPlugin:
    def __init__(self):
        self.failed_test_cases = []
        self.exceptions_text = {}

    def pytest_runtest_logreport(self, report):
        if report.when == "call" and report.outcome == 'failed':
            nodeid = report.nodeid
            self.failed_test_cases.append(nodeid)
            self.exceptions_text[nodeid] = get_test(report.longrepr)


def run_tests_return_failed_cases(pytest_args):
    with open(os.devnull, 'w') as devnull:
        with contextlib.redirect_stdout(devnull):
            with contextlib.redirect_stderr(devnull):
                plugin = FailedTestCasesPlugin()
                exit_code = pytest.main(
                    pytest_args,
                    plugins=[plugin],
                )
                with open(EXCEPTIONS_FILE, "w") as f:
                    json.dump(plugin.exceptions_text, f)
                return exit_code, plugin.failed_test_cases


if __name__ == "__main__":
    exit_code, failed_cases = run_tests_return_failed_cases(sys.argv[1:])
    print("\n".join(failed_cases))
    print()
    exit(exit_code)
