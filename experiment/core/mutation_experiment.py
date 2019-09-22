import pandas as pd
from loguru import logger

from config import COMMON_EXCLUDE
from experiment.test_suite.collect_test_suite import SubTestSuite
from experiment.core.generic_experiment import generic_experiment_size, generic_experiment_coverage, \
    bin_zero_to_one_column_to_percent
from model.cfg.project_cfg import ProjectCFG
from tracing.trace_reader import TraceReader
from experiment.mutation import killed_mutants

METRIC = "Metric"
SUITE_SIZE = "Suite size"
SUITE_COVERAGE = "Coverage"
SUITE_COVERAGE_BIN = "Coverage bins (%)"
MUTATION_SCORE = "Mutation score"


def run_mutation_experiment_fixed_size(
        project_root, module_under_test_path,
        test_suite_sizes_count=30,
        test_suite_sizes=None,
        max_trace_size=10,
        timeout=None,
        coverage_metrics=None,
        support=100
):
    logger.debug("Running mutation experiment (fixed size) for {module}", module=module_under_test_path)
    cfg = ProjectCFG.create_from_path(project_root, exclude_folders=COMMON_EXCLUDE)

    trace_reader = TraceReader(project_root)
    all_node_ids, paths = trace_reader.get_traces_for(module_under_test_path)
    failing_node_ids = trace_reader.read_failed_test_cases()
    not_failing_node_ids = set(all_node_ids) - set(failing_node_ids)

    killed, total_mutants = killed_mutants(
        project_root=project_root,
        path_to_module_under_test=module_under_test_path,
        test_cases_ids=tuple(not_failing_node_ids),
        timeout=timeout
    )
    scoring_function = get_scoring_function(killed, total_mutants)
    points = generic_experiment_size(
        project_root,
        module_under_test_path,
        scoring_function,
        test_suite_sizes_count=test_suite_sizes_count,
        test_suite_sizes=test_suite_sizes,
        max_trace_size=max_trace_size,
        coverage_metrics=coverage_metrics,
        node_ids=tuple(not_failing_node_ids),
        support=support
    )

    df = pd.DataFrame(data=points, columns=[SUITE_SIZE, METRIC, MUTATION_SCORE, SUITE_COVERAGE])

    return df, total_mutants


def run_mutation_experiment_fixed_coverage(
        project_root,
        module_under_test_path,
        coverage_boundaries_count=20,
        max_trace_size=10,
        timeout=None,
        coverage_metrics=None,
        support=100
):
    logger.debug("Running mutation experiment (fixed coverage) for {module}", module=module_under_test_path)
    cfg = ProjectCFG.create_from_path(project_root, exclude_folders=COMMON_EXCLUDE)

    trace_reader = TraceReader(project_root)
    all_node_ids, paths = trace_reader.get_traces_for(module_under_test_path)
    failing_node_ids = trace_reader.read_failed_test_cases()
    not_failing_node_ids = set(all_node_ids) - set(failing_node_ids)

    killed, total_mutants = killed_mutants(
        project_root=project_root,
        path_to_module_under_test=module_under_test_path,
        test_cases_ids=tuple(not_failing_node_ids),
        timeout=timeout
    )
    scoring_function = get_scoring_function(killed, total_mutants)

    points = generic_experiment_coverage(
        project_root,
        module_under_test_path,
        scoring_function,
        coverage_boundaries_count=coverage_boundaries_count,
        max_trace_size=max_trace_size,
        coverage_metrics=coverage_metrics,
        node_ids=not_failing_node_ids,
        support=support
    )
    df = pd.DataFrame(data=points, columns=[SUITE_SIZE, METRIC, MUTATION_SCORE, SUITE_COVERAGE])
    df = bin_zero_to_one_column_to_percent(df, SUITE_COVERAGE, SUITE_COVERAGE_BIN, coverage_boundaries_count)
    return df, total_mutants


def get_scoring_function(killed, total_mutants):
    def sf(suite: SubTestSuite):
        return count_suite_mutation_score(suite, killed, total_mutants)

    return sf


def count_suite_mutation_score(suite: SubTestSuite, killed, total):
    killed_muts = set()
    for case in suite.test_cases:
        killed_muts.update(killed[case])

    return len(killed_muts) / total
