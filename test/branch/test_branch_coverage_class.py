import unittest

from coverage_metrics.branch_coverage import BranchCoverage, first_lines_of_branches
from test.test_tracer import LINKED_LIST_ROOT, create_new_temp_dir

import thorough


class TestBranchCoverageClass(unittest.TestCase):

    def test_branch_coverage(self):

        project_root = LINKED_LIST_ROOT
        trace_root = create_new_temp_dir()
        exclude_folders = ["venv", "dataset"]

        thorough.runTests(project_root, trace_root, exclude_folders)

        coverage = BranchCoverage(trace_root, project_root, exclude_folders=exclude_folders)
        report = coverage.module_coverage()
        # check that there are no NaN values in report
        self.assertFalse(report.isnull().values.any())