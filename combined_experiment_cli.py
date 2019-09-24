import shutil

import thorough

import argparse

from pathlib import Path

from config import COMMON_EXCLUDE
from coverage_metrics.coverage_metric_enum import CoverageMetric
from experiment.core.generic_experiment import image_path, df_path, module_path
from experiment.core.mutation_experiment import run_mutation_experiment_fixed_size, MUTATION_SCORE, \
    run_mutation_experiment_fixed_coverage
from experiment.core.real_bugs_experiment import run_real_bugs_experiment_fixed_size, \
    run_real_bugs_experiment_fixed_coverage, SUITE_SIZE, METRIC, BUG_REVEALED_SCORE, SUITE_COVERAGE_BIN
from experiment.core.visualization import create_cat_plot_with_count
from tracing.trace_reader import TraceReader
from util.misc import maybe_expand
from enum import Enum


class DataFrameType(Enum):
    MUTATION_FIXED_SIZE = "MUTATION_FIXED_SIZE"
    MUTATION_FIXED_COVERAGE = "MUTATION_FIXED_COVERAGE"
    BUGS_FIXED_SIZE = "BUGS_FIXED_SIZE"
    BUGS_FIXED_COVERAGE = "BUGS_FIXED_COVERAGE"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Real project experiment')
    parser.add_argument('--module', type=str, help='Module under test path')
    parser.add_argument('--timeout', type=str, help='Mutation testing timeout')

    parser.add_argument('--revealing_node_ids', nargs="+", help='These will be used in bug experiment part')

    parser.add_argument('--out', type=str, help='Folder for results')

    parser.add_argument('--test_suite_sizes', nargs="+", type=int,
                        help='Suite sizes to test (priority over "test_suite_coverages_count")')
    parser.add_argument('--test_suite_coverages_count', type=int, help='How many bins for coverage to use')
    parser.add_argument('--support', type=int, help='How many test suites to generate for each ts size of coverage bin',
                        default=1000)
    parser.add_argument('--max_trace_size', type=int, help='Largest trace file to open (MB)', default=10)

    args, unknown = parser.parse_known_args()

    project_root = maybe_expand("")
    trace_root = project_root
    support = args.support
    test_suite_sizes = args.test_suite_sizes
    coverage_boundaries_count = args.test_suite_coverages_count

    max_trace_size = args.max_trace_size
    out_folder = maybe_expand(args.out)

    module = args.module
    revealing_node_ids = args.revealing_node_ids

    exclude_folders_tracing = COMMON_EXCLUDE
    thorough.run_tests(
        project_root, trace_root,
        exclude_folders_tracing=exclude_folders_tracing,
        exclude_folders_collection=None,
        show_time_per_test=False,
        quiet=False,
        deselect_tests=None
    )


    trace_reader = TraceReader(trace_root)
    failed_node_ids = trace_reader.read_failed_test_cases()

    module = maybe_expand(module)
    coverage_metrics = (CoverageMetric.STATEMENT, CoverageMetric.BRANCH, CoverageMetric.ALL_PAIRS)

    new_module_path = module_path(out_folder, project_root, module)
    shutil.copy(module, new_module_path)

    df_fixed_size, total_bugs = run_real_bugs_experiment_fixed_size(
        project_root=project_root,
        module_under_test_path=module,
        revealing_node_ids=revealing_node_ids,
        test_suite_sizes_count=None,
        test_suite_sizes=test_suite_sizes,
        max_trace_size=max_trace_size,
        coverage_metrics=coverage_metrics,
        support=support
    )

    df_p = df_path(out_folder, project_root, module, DataFrameType.BUGS_FIXED_SIZE.value)
    df_fixed_size.to_csv(df_p)

    title = f"{Path(module).name}, {total_bugs} bugs"

    image_p = image_path(out_folder, project_root, module, DataFrameType.BUGS_FIXED_SIZE.value)
    create_cat_plot_with_count(df_fixed_size, title, image_p,
                               x=SUITE_SIZE, y=BUG_REVEALED_SCORE, hue=METRIC,
                               xlabel="Test suite size", ylabel="Bugs revealed", no_ordering=True)

    df_fixed_coverage, total_bugs = run_real_bugs_experiment_fixed_coverage(
        project_root=project_root,
        module_under_test_path=module,
        revealing_node_ids=revealing_node_ids,
        coverage_boundaries_count=coverage_boundaries_count,
        max_trace_size=max_trace_size,
        coverage_metrics=coverage_metrics,
        support=support
    )

    df_p = df_path(out_folder, project_root, module, DataFrameType.BUGS_FIXED_COVERAGE.value)
    df_fixed_coverage.to_csv(df_p)

    image_p = image_path(out_folder, project_root, module, DataFrameType.BUGS_FIXED_COVERAGE.value)
    create_cat_plot_with_count(df_fixed_coverage, title, image_p,
                               x=SUITE_COVERAGE_BIN, y=BUG_REVEALED_SCORE, hue=METRIC,
                               xlabel="Test suite coverage (%)", ylabel="Bugs revealed")

    # mutation experiment
    df_fixed_size, total_mutants = run_mutation_experiment_fixed_size(
        project_root=project_root,
        module_under_test_path=module,
        test_suite_sizes_count=None,
        test_suite_sizes=test_suite_sizes,
        max_trace_size=max_trace_size,
        timeout=args.timeout,
        coverage_metrics=coverage_metrics,
        support=support
    )
    title = f"{Path(module).name}, {total_mutants} mutants"
    df_p = df_path(out_folder, project_root, module, DataFrameType.MUTATION_FIXED_SIZE.value)
    df_fixed_size.to_csv(df_p)

    image_p = image_path(out_folder, project_root, module, DataFrameType.MUTATION_FIXED_SIZE.value)
    create_cat_plot_with_count(df_fixed_size, title, image_p,
                               x=SUITE_SIZE, y=MUTATION_SCORE, hue=METRIC,
                               xlabel="Test suite size", ylabel="Mutants killed (%)", no_ordering=True)

    # fixed coverage

    df_fixed_coverage, total_mutants = run_mutation_experiment_fixed_coverage(
        project_root=project_root,
        module_under_test_path=module,
        coverage_boundaries_count=coverage_boundaries_count,
        max_trace_size=max_trace_size,
        timeout=args.timeout,
        coverage_metrics=coverage_metrics,
        support=support
    )
    df_p = df_path(out_folder, project_root, module, DataFrameType.MUTATION_FIXED_COVERAGE.value)
    df_fixed_coverage.to_csv(df_p)

    title = f"{Path(module).name}, {total_mutants} mutants"
    image_p = image_path(out_folder, project_root, module, DataFrameType.MUTATION_FIXED_COVERAGE.value)
    create_cat_plot_with_count(df_fixed_coverage, title, image_p,
                               x=SUITE_COVERAGE_BIN, y=MUTATION_SCORE, hue=METRIC,
                               xlabel="Test suite coverage", ylabel="Mutants killed (%)")

    exit(0)
