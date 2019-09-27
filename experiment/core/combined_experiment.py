import pandas as pd
from loguru import logger

from experiment.core.columns import MUTATION_SCORE, METRIC, BUG_REVEALED_SCORE, SUITE_COVERAGE, SUITE_SIZE, \
    SUITE_COVERAGE_BIN
from experiment.core.mutation_experiment import get_mutation_scoring_function
from experiment.core.real_bugs_experiment import get_bugs_scoring_function
from experiment.core.generic_experiment import generic_experiment_size, generic_experiment_coverage, \
    bin_zero_to_one_column_to_percent
from tracing.trace_reader import TraceReader


def combined_experiment_fixed_size(
        project_root,
        module_under_test_path,
        revealing_node_ids,
        test_suite_sizes_count=30,
        test_suite_sizes=None,
        max_trace_size=10,
        coverage_metrics=None,
        support=100,
        timeout=None
):
    logger.debug("Running real project experiment for {module} (fixed size)", module=module_under_test_path)
    trace_reader = TraceReader(project_root)
    not_failing_node_ids = trace_reader.get_not_failing_node_ids(module_under_test_path)

    mutation_scoring_function, total_mutants_count = get_mutation_scoring_function(
        project_root,
        module_under_test_path,
        not_failing_node_ids=not_failing_node_ids,
        timeout=timeout
    )

    bugs_scoring_function = get_bugs_scoring_function(revealing_node_ids)
    total_bugs_count = len(revealing_node_ids)

    points = generic_experiment_size(
        project_root,
        module_under_test_path,
        [mutation_scoring_function, bugs_scoring_function],
        test_suite_sizes_count=test_suite_sizes_count,
        test_suite_sizes=test_suite_sizes,
        max_trace_size=max_trace_size,
        coverage_metrics=coverage_metrics,
        node_ids=set(revealing_node_ids) | not_failing_node_ids,
        support=support
    )
    columns = [SUITE_SIZE, METRIC, MUTATION_SCORE, BUG_REVEALED_SCORE, SUITE_COVERAGE]
    df = pd.DataFrame(data=points, columns=columns)

    return df, total_mutants_count, total_bugs_count


def combined_experiment_fixed_coverage(
        project_root,
        module_under_test_path,
        revealing_node_ids,
        coverage_boundaries_count=20,
        max_trace_size=10,
        coverage_metrics=None,
        support=100,
        timeout=None
):
    logger.debug("Running real project experiment for {module} (fixed coverage)", module=module_under_test_path)

    trace_reader = TraceReader(project_root)
    not_failing_node_ids = trace_reader.get_not_failing_node_ids(module_under_test_path)

    mutation_scoring_function, total_mutants_count = get_mutation_scoring_function(
        project_root,
        module_under_test_path,
        not_failing_node_ids=not_failing_node_ids,
        timeout=timeout
    )

    bugs_scoring_function = get_bugs_scoring_function(revealing_node_ids)
    total_bugs_count = len(revealing_node_ids)

    points = generic_experiment_coverage(
        project_root,
        module_under_test_path,
        [mutation_scoring_function, bugs_scoring_function],
        coverage_boundaries_count=coverage_boundaries_count,
        max_trace_size=max_trace_size,
        coverage_metrics=coverage_metrics,
        node_ids=set(revealing_node_ids) | set(not_failing_node_ids),
        support=support
    )
    columns = [SUITE_SIZE, METRIC, MUTATION_SCORE, BUG_REVEALED_SCORE, SUITE_COVERAGE]
    df = pd.DataFrame(data=points, columns=columns)

    df = bin_zero_to_one_column_to_percent(df, SUITE_COVERAGE, SUITE_COVERAGE_BIN, coverage_boundaries_count)

    return df, total_mutants_count, total_bugs_count
