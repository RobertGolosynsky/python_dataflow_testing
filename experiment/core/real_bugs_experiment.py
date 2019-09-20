from typing import Set

import pandas as pd
from loguru import logger
from config import COMMON_EXCLUDE

from experiment.collect_test_suite import SubTestSuite
from experiment.core.generic_experiment import generic_experiment_size, default_metrics, generic_experiment_coverage, \
    bin_zero_to_one_column_to_percent
from model.cfg.project_cfg import ProjectCFG

METRIC = "Metric"
SUITE_SIZE = "Suite size"
SUITE_COVERAGE = "Coverage"
SUITE_COVERAGE_BIN = "Coverage bins (%)"
BUG_REVEALED_SCORE = "Bugs revealed score"


def run_real_bugs_experiment_fixed_size(
        project_root,
        module_under_test_path,
        revealing_node_ids,
        evaluation_points=30,
        max_trace_size=10,
        coverage_metrics=None
):
    logger.debug("Running real project experiment for {module} (fixed size)", module=module_under_test_path)
    if coverage_metrics is None:
        coverage_metrics = default_metrics

    cfg = ProjectCFG.create_from_path(project_root, exclude_folders=COMMON_EXCLUDE)

    if not isinstance(revealing_node_ids, set):
        revealing_node_ids = set(revealing_node_ids)
    total_failing_node_ids = len(revealing_node_ids)

    scoring_function = get_scoring_function(revealing_node_ids)
    points = generic_experiment_size(
        project_root,
        module_under_test_path,
        scoring_function,
        evaluation_points=evaluation_points,
        max_trace_size=max_trace_size,
        coverage_metrics=coverage_metrics
    )

    df = pd.DataFrame(data=points, columns=[SUITE_SIZE, METRIC, BUG_REVEALED_SCORE, SUITE_COVERAGE])

    return df, total_failing_node_ids


def run_real_bugs_experiment_fixed_coverage(
        project_root,
        module_under_test_path,
        revealing_node_ids,
        coverage_boundaries_count=20,
        max_trace_size=10,
        coverage_metrics=None
):
    logger.debug("Running real project experiment for {module} (fixed coverage)", module=module_under_test_path)
    if coverage_metrics is None:
        coverage_metrics = default_metrics

    if not isinstance(revealing_node_ids, set):
        revealing_node_ids = set(revealing_node_ids)
    total_failing_node_ids = len(revealing_node_ids)

    scoring_function = get_scoring_function(revealing_node_ids)
    points = generic_experiment_coverage(
        project_root,
        module_under_test_path,
        scoring_function,
        coverage_boundaries_count=coverage_boundaries_count,
        max_trace_size=max_trace_size,
        coverage_metrics=coverage_metrics
    )

    df = pd.DataFrame(data=points, columns=[SUITE_SIZE, METRIC, BUG_REVEALED_SCORE, SUITE_COVERAGE])
    df = bin_zero_to_one_column_to_percent(df, SUITE_COVERAGE, SUITE_COVERAGE_BIN, coverage_boundaries_count)
    return df, total_failing_node_ids


def get_scoring_function(revealing_node_ids):
    def sf(suite: SubTestSuite):
        return bugs_revealed(suite, revealing_node_ids)

    return sf


def bugs_revealed(suite: SubTestSuite, revealing_node_ids: Set[str]):
    used_reveling_node_ids = revealing_node_ids.intersection(set(suite.test_cases))
    return len(used_reveling_node_ids)
