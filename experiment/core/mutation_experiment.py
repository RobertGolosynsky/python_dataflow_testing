import pandas as pd
from loguru import logger

from experiment.core.columns import MUTATION_SCORE, METRIC, SUITE_COVERAGE, SUITE_SIZE, \
    SUITE_COVERAGE_BIN
from experiment.suites.collect_test_suite import SubTestSuite
from experiment.core.generic_experiment import generic_experiment_size, generic_experiment_coverage, \
    bin_zero_to_one_column_to_percent
from experiment.core.mutation import killed_mutants
from tracing.trace_reader import TraceReader


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
    trace_reader = TraceReader(project_root)
    not_failing_node_ids = trace_reader.get_not_failing_node_ids(module_under_test_path)

    mutation_scoring_function, total_mutants_count = get_mutation_scoring_function(
        project_root,
        module_under_test_path,
        not_failing_node_ids=not_failing_node_ids,
        timeout=timeout
    )

    points = generic_experiment_size(
        project_root,
        module_under_test_path,
        [mutation_scoring_function],
        test_suite_sizes_count=test_suite_sizes_count,
        test_suite_sizes=test_suite_sizes,
        max_trace_size=max_trace_size,
        coverage_metrics=coverage_metrics,
        node_ids=tuple(not_failing_node_ids),
        support=support
    )

    df = pd.DataFrame(data=points, columns=[SUITE_SIZE, METRIC, MUTATION_SCORE, SUITE_COVERAGE])

    return df, total_mutants_count


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
    trace_reader = TraceReader(project_root)
    not_failing_node_ids = trace_reader.get_not_failing_node_ids(module_under_test_path)
    scoring_function, total_mutants_count = get_mutation_scoring_function(
        project_root,
        module_under_test_path,
        not_failing_node_ids,
        timeout=timeout
    )

    points = generic_experiment_coverage(
        project_root,
        module_under_test_path,
        [scoring_function],
        coverage_boundaries_count=coverage_boundaries_count,
        max_trace_size=max_trace_size,
        coverage_metrics=coverage_metrics,
        support=support
    )

    df = pd.DataFrame(data=points, columns=[SUITE_SIZE, METRIC, MUTATION_SCORE, SUITE_COVERAGE])
    df = bin_zero_to_one_column_to_percent(df, SUITE_COVERAGE, SUITE_COVERAGE_BIN, coverage_boundaries_count)
    return df, total_mutants_count


def count_suite_mutation_score(suite: SubTestSuite, killed, total):
    killed_muts = set()
    for case in suite.test_cases:
        killed_muts.update(killed[case])

    return len(killed_muts) / total


def get_mutation_scoring_function(project_root, module_under_test_path, not_failing_node_ids, timeout=None):
    killed, total_mutants = killed_mutants(
        project_root=project_root,
        module_under_test_path=module_under_test_path,
        not_failing_node_ids=not_failing_node_ids,
        timeout=timeout
    )

    def mutation_scoring_function(suite: SubTestSuite):
        return count_suite_mutation_score(suite, killed, total_mutants)

    return mutation_scoring_function, total_mutants
