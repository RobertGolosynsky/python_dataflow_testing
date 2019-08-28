import unittest

import thorough
from coverage_metrics.branch_coverage import BranchCoverage
from coverage_metrics.def_use_coverage import DefUsePairsCoverage
from coverage_metrics.statement_coverage import StatementCoverage
from test.test_tracer import LINKED_LIST_ROOT, create_new_temp_dir
import pandas as pd


class TestMergeReport(unittest.TestCase):

    def test_merge_reports(self):
        pd.options.display.float_format = '{:,.2f}'.format
        pd.options.display.width = 0

        project_root = LINKED_LIST_ROOT.parent / "dictionary"

        trace_root = create_new_temp_dir()
        exclude_folders = ["venv", "dataset"]

        thorough.run_tests(project_root, trace_root, exclude_folders)
        print(trace_root)

        stcoverage = StatementCoverage(trace_root, project_root, exclude_folders=exclude_folders, max_trace_size=30)
        brcoverage = BranchCoverage(trace_root, project_root, exclude_folders=exclude_folders, max_trace_size=30)
        ducoverage = DefUsePairsCoverage(trace_root, project_root, exclude_folders=exclude_folders, max_trace_size=30)
        streport = stcoverage.report()
        brreport = brcoverage.report()
        dureport = ducoverage.report()
        merged_report:pd.DataFrame = pd.concat([streport, brreport, dureport], axis=1)
        merged_report = merged_report[pd.notnull(merged_report['StCov'])]
        print(merged_report)

