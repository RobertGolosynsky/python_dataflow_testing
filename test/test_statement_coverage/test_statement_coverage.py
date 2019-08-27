import unittest
import pandas as pd
from coverage_metrics.statement_coverage import StatementCoverage
from test.test_tracer import LINKED_LIST_ROOT, create_new_temp_dir

import thorough

pd.options.display.max_colwidth = 30


class TestBranchCoverageClass(unittest.TestCase):

    def test_branch_coverage(self):
        project_root = LINKED_LIST_ROOT
        trace_root = create_new_temp_dir()
        exclude_folders = ["venv", "dataset"]

        thorough.run_tests(project_root, trace_root, exclude_folders)

        coverage = StatementCoverage(trace_root, project_root, exclude_folders=exclude_folders)
        report = coverage.report()
        # check that there are no NaN values in report
        self.assertFalse(report.isnull().values.any())