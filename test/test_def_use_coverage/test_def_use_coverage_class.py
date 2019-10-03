import unittest
import pandas as pd

from coverage_metrics.all_c_all_p_uses_coverage import AllCAllPUses
from coverage_metrics.def_use_coverage import DefUsePairsCoverage
from test.test_tracer import CLEAN_LINKED_LIST_ROOT, create_new_temp_dir

import thorough

pd.options.display.max_colwidth = 30


class TestDefUseCoverageClass(unittest.TestCase):

    def test_def_use_coverage(self):
        project_root = CLEAN_LINKED_LIST_ROOT
        trace_root = create_new_temp_dir()
        exclude_folders = ["venv", "dataset"]

        thorough.run_tests(project_root, trace_root, exclude_folders)

        coverage = DefUsePairsCoverage(trace_root, project_root, exclude_folders=exclude_folders)
        report = coverage.report()
        # check that there are no NaN values in report
        self.assertFalse(report.isnull().values.any())