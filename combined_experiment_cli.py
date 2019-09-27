import shutil

import thorough

import argparse

from pathlib import Path

from config import COMMON_EXCLUDE
from coverage_metrics.coverage_metric_enum import CoverageMetric
from experiment.core.columns import SUITE_SIZE, SUITE_COVERAGE_BIN, DataFrameType
from experiment.core.combined_experiment import combined_experiment_fixed_size, combined_experiment_fixed_coverage
from experiment.core.generic_experiment import image_path, df_path, module_path
from experiment.visualization.other import draw_vertically
from tracing.trace_reader import TraceReader
from util.misc import maybe_expand

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
                        default=100)
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
    timeout = args.timeout
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

    # fixed size
    df, total_mutants_count, total_bugs_count = combined_experiment_fixed_size(
        project_root=project_root,
        module_under_test_path=module,
        revealing_node_ids=revealing_node_ids,
        test_suite_sizes_count=None,
        test_suite_sizes=test_suite_sizes,
        max_trace_size=max_trace_size,
        coverage_metrics=coverage_metrics,
        support=support,
        timeout=timeout
    )

    df_p = df_path(out_folder, project_root, module, DataFrameType.FIXED_SIZE.value)
    df.to_csv(df_p)

    title = f"{Path(module).name}, {total_mutants_count} mutants, {total_bugs_count} bugs"

    image_p = image_path(out_folder, project_root, module, DataFrameType.FIXED_SIZE.value)
    draw_vertically(df, SUITE_SIZE, image_p, title=title)

    # fixed coverage
    df, total_mutants_count, total_bugs_count = combined_experiment_fixed_coverage(
        project_root=project_root,
        module_under_test_path=module,
        revealing_node_ids=revealing_node_ids,
        coverage_boundaries_count=coverage_boundaries_count,
        max_trace_size=max_trace_size,
        coverage_metrics=coverage_metrics,
        support=support,
        timeout=timeout
    )

    df_p = df_path(out_folder, project_root, module, DataFrameType.FIXED_COVERAGE.value)
    df.to_csv(df_p)

    image_p = image_path(out_folder, project_root, module, DataFrameType.FIXED_COVERAGE.value)
    draw_vertically(df, SUITE_COVERAGE_BIN, image_p, title=title)

    exit(0)
