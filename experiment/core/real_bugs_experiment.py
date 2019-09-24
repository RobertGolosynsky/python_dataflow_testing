from typing import Set

import pandas as pd
from loguru import logger
from config import COMMON_EXCLUDE

from experiment.test_suite.collect_test_suite import SubTestSuite
from experiment.core.generic_experiment import generic_experiment_size, DEFAULT_METRICS, generic_experiment_coverage, \
    bin_zero_to_one_column_to_percent
from model.cfg.project_cfg import ProjectCFG
from tracing.trace_reader import TraceReader

METRIC = "Metric"
SUITE_SIZE = "Suite size"
SUITE_COVERAGE = "Coverage"
SUITE_COVERAGE_BIN = "Coverage bins (%)"
BUG_REVEALED_SCORE = "Bugs revealed score"


def run_real_bugs_experiment_fixed_size(
        project_root,
        module_under_test_path,
        revealing_node_ids,
        test_suite_sizes_count=30,
        test_suite_sizes=None,
        max_trace_size=10,
        coverage_metrics=None,
        support=100
):
    logger.debug("Running real project experiment for {module} (fixed size)", module=module_under_test_path)

    revealing_node_ids = set(revealing_node_ids)
    total_revealing_node_ids = len(revealing_node_ids)

    trace_reader = TraceReader(project_root)
    failing_node_ids = trace_reader.read_failed_test_cases()
    all_node_ids, _ = trace_reader.get_traces_for(module_under_test_path)
    not_failing_node_ids = set(all_node_ids) - set(failing_node_ids)

    scoring_function = get_scoring_function(revealing_node_ids)
    points = generic_experiment_size(
        project_root,
        module_under_test_path,
        scoring_function,
        test_suite_sizes_count=test_suite_sizes_count,
        test_suite_sizes=test_suite_sizes,
        max_trace_size=max_trace_size,
        coverage_metrics=coverage_metrics,
        node_ids=not_failing_node_ids | revealing_node_ids,
        support=support
    )

    df = pd.DataFrame(data=points, columns=[SUITE_SIZE, METRIC, BUG_REVEALED_SCORE, SUITE_COVERAGE])

    return df, total_revealing_node_ids


def run_real_bugs_experiment_fixed_coverage(
        project_root,
        module_under_test_path,
        revealing_node_ids,
        coverage_boundaries_count=20,
        max_trace_size=10,
        coverage_metrics=None,
        support=100
):
    logger.debug("Running real project experiment for {module} (fixed coverage)", module=module_under_test_path)

    revealing_node_ids = set(revealing_node_ids)

    trace_reader = TraceReader(project_root)
    failing_node_ids = trace_reader.read_failed_test_cases()
    all_node_ids, _ = trace_reader.get_traces_for(module_under_test_path)
    not_failing_node_ids = set(all_node_ids) - set(failing_node_ids)

    scoring_function = get_scoring_function(revealing_node_ids)
    points = generic_experiment_coverage(
        project_root,
        module_under_test_path,
        scoring_function,
        coverage_boundaries_count=coverage_boundaries_count,
        max_trace_size=max_trace_size,
        coverage_metrics=coverage_metrics,
        node_ids=not_failing_node_ids | revealing_node_ids,
        support=support
    )

    df = pd.DataFrame(data=points, columns=[SUITE_SIZE, METRIC, BUG_REVEALED_SCORE, SUITE_COVERAGE])
    df = bin_zero_to_one_column_to_percent(df, SUITE_COVERAGE, SUITE_COVERAGE_BIN, coverage_boundaries_count)

    total_revealing_node_ids = len(revealing_node_ids)
    return df, total_revealing_node_ids


def get_scoring_function(revealing_node_ids):
    def sf(suite: SubTestSuite):
        return bugs_revealed(suite, revealing_node_ids)

    return sf


def bugs_revealed(suite: SubTestSuite, revealing_node_ids: Set[str]):
    used_reveling_node_ids = revealing_node_ids.intersection(set(suite.test_cases))
    if len(revealing_node_ids) == 0:
        return 0.0
    return len(used_reveling_node_ids)/len(revealing_node_ids)
