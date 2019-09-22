import unittest

import pandas as pd

import thorough
from coverage_metrics.coverage_metric_enum import CoverageMetric
from experiment.test_suite.suite_generator import SuiteGenerator

from test.test_tracer import PROJECT_ROOT, create_new_temp_dir


class TestCreateTestSuites(unittest.TestCase):

    def test_generate_fixed_size(self):
        pd.options.display.float_format = '{:,.2f}'.format
        pd.options.display.width = 0

        project_root = PROJECT_ROOT / "dataset" / "linked_list_clean"

        trace_root = create_new_temp_dir()
        exclude_folders = ["venv", "dataset"]

        thorough.run_tests(project_root, trace_root, exclude_folders)

        module_under_test_path = str(project_root / "core" / "ll.py")
        sg = SuiteGenerator(trace_root, project_root, exclude_folders=exclude_folders)
        suites = sg.fix_sized_suites(
            module_under_test_path=module_under_test_path,
            coverage_metric=CoverageMetric.BRANCH,
            exact_size=3,
            check_unique_items_covered=False,
            n=10
        )
        self.assertTrue(len(suites) > 0)