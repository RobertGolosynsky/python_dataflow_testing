from pathlib import Path
from typing import List

from joblib import Memory

from coverage_metrics.branch_coverage import BranchCoverage
from coverage_metrics.coverage_metric_enum import CoverageMetric
from coverage_metrics.def_use_coverage import DefUsePairsCoverage
from coverage_metrics.statement_coverage import StatementCoverage
from experiment.suites.collect_test_suite import SubTestSuite, generate_test_suites_fixed_size, \
    generate_test_suites_fixed_coverage


class SuiteGenerator:

    def __init__(self, trace_root, project_root,
                 exclude_folders=None,
                 max_trace_size=None):
        self.stcov = StatementCoverage(trace_root, project_root,
                                       exclude_folders=exclude_folders,
                                       max_trace_size=max_trace_size)
        self.brcov = BranchCoverage(trace_root, project_root,
                                    exclude_folders=exclude_folders,
                                    max_trace_size=max_trace_size)
        self.ducov = DefUsePairsCoverage(trace_root, project_root,
                                         exclude_folders=exclude_folders,
                                         max_trace_size=max_trace_size)
        cache_path = "/tmp/thorough/.cached_coverage"
        # self.memory = Memory(location=Path(trace_root) / ".coverage_cache", verbose=0)
        self.memory = Memory(location=cache_path, verbose=0)
        self.cached_get_total_items = self.memory.cache(_get_total_items, ignore=["cov"])

    def _get_total_items(self, coverage_metric, module_under_test_path, test_cases):
        if coverage_metric == CoverageMetric.STATEMENT:
            cov = self.stcov
        elif coverage_metric == CoverageMetric.BRANCH:
            cov = self.brcov
        else:
            cov = self.ducov
        if test_cases is not None and not isinstance(test_cases, frozenset):
            test_cases = frozenset(test_cases)
        return self.cached_get_total_items(cov, coverage_metric, module_under_test_path, test_cases)
        # return _get_total_items(cov, coverage_metric, module_under_test_path, test_cases)

    def fix_sized_suites(self,
                         module_under_test_path: str,
                         coverage_metric: CoverageMetric,
                         n,
                         exact_size,
                         check_unique_items_covered=False,
                         test_cases=None
                         ) -> List[SubTestSuite]:

        coverage_report, total_items = self._get_total_items(coverage_metric, module_under_test_path, test_cases)
        if len(total_items) == 0:
            return []
        suites = generate_test_suites_fixed_size(
            data=coverage_report,
            n=n,
            total_coverage_items=total_items,
            exact_size=exact_size,
            check_unique_items_covered=check_unique_items_covered
        )
        return suites

    def fix_coverage_suites(self,
                            module_under_test_path: str,
                            coverage_metric: CoverageMetric,
                            n,
                            coverage_boundary,
                            check_unique_items_covered=False,
                            test_cases=None
                            ) -> List[SubTestSuite]:
        coverage_report, total_items = self._get_total_items(coverage_metric, module_under_test_path, test_cases)
        if len(total_items) == 0:
            return []
        suites = generate_test_suites_fixed_coverage(
            data=coverage_report,
            n=n,
            total_coverage_items=total_items,
            coverage_boundary=coverage_boundary,
            check_unique_items_covered=check_unique_items_covered
        )
        return suites


def _get_total_items(cov, coverage_metric, module_under_test_path, test_cases):
    coverage_report = cov.covered_items_of(
        module_under_test_path,
        of_type=coverage_metric,
        selected_node_ids=test_cases
    )

    total_items = cov.total_items_of(module_under_test_path, of_type=coverage_metric)

    return coverage_report, total_items
