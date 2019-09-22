import shutil

import thorough

import argparse

from pathlib import Path

from experiment.core.generic_experiment import image_path, df_path, module_path
from experiment.core.real_bugs_experiment import run_real_bugs_experiment_fixed_size, \
    run_real_bugs_experiment_fixed_coverage, SUITE_SIZE, METRIC, BUG_REVEALED_SCORE, SUITE_COVERAGE_BIN
from experiment.core.visualization import create_box_plot, create_cat_plot, create_cat_plot_with_count
from tracing.trace_reader import TraceReader
from util.misc import maybe_expand

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Real project experiment')
    parser.add_argument('--module', type=str, help='Module under test path')

    parser.add_argument('--node_ids', nargs="+", help='Pytest args')

    parser.add_argument('--graphs_folder', type=str, help='Folder for resulting graphs')

    parser.add_argument('--test_suite_sizes_count', type=int,
                        help='How many sub test suite sizes to test (between min and max_available)')
    parser.add_argument('--test_suite_coverages_count', type=int, help='How many bins for coverage to use')
    parser.add_argument('--max_trace_size', type=int, help='Largest trace file to open (MB)')

    args, unknown = parser.parse_known_args()

    project_root = maybe_expand("")
    trace_root = project_root
    test_suite_sizes_count = args.test_suite_sizes_count
    coverage_boundaries_count = args.test_suite_coverages_count
    max_trace_size = args.max_trace_size
    graphs_folder = maybe_expand(args.graphs_folder)

    exclude_folders_tracing = ["dataset", "venv", "tests", "test"]
    thorough.run_tests(
        project_root, trace_root,
        exclude_folders_tracing=exclude_folders_tracing,
        exclude_folders_collection=None,
        show_time_per_test=False,
        quiet=False,
        deselect_tests=None,
        # node_ids=args.node_ids
    )

    trace_reader = TraceReader(trace_root)
    failed_test_cases = trace_reader.read_failed_test_cases()

    print("Failed cases:", failed_test_cases)
    if len(failed_test_cases) == 0:
        raise ValueError("No test cases failed")


    def experiment(module):
        df_fixed_size, total_bugs = run_real_bugs_experiment_fixed_size(
            project_root,
            module,
            node_ids,
            test_suite_sizes_count,
            max_trace_size
        )

        plot_type = "fixed_size_box_plot"
        title = f"{Path(module).name}, {total_bugs} bugs"

        image_p = image_path(graphs_folder, project_root, module, plot_type)
        create_box_plot(df_fixed_size, title, image_p,
                        x=SUITE_SIZE, y=BUG_REVEALED_SCORE, hue=METRIC,
                        xlabel="Test suite size", ylabel="Bugs revealed")
        df_p = df_path(graphs_folder, project_root, module, plot_type)
        df_fixed_size.to_csv(df_p)

        plot_type = "fixed_size_cat_plot"
        image_p = image_path(graphs_folder, project_root, module, plot_type)
        create_cat_plot(df_fixed_size, title, image_p,
                        x=SUITE_SIZE, y=BUG_REVEALED_SCORE, hue=METRIC,
                        xlabel="Test suite size", ylabel="Bugs revealed")

        plot_type = "fixed_size_count_plot"
        image_p = image_path(graphs_folder, project_root, module, plot_type)
        create_cat_plot_with_count(df_fixed_size, title, image_p,
                                   x=SUITE_SIZE, y=BUG_REVEALED_SCORE, hue=METRIC,
                                   xlabel="Test suite size", ylabel="Bugs revealed", no_ordering=True)

        new_module_path = module_path(graphs_folder, project_root, module)
        shutil.copy(module, new_module_path)

        df_fixed_coverage, total_bugs = run_real_bugs_experiment_fixed_coverage(
            project_root,
            module,
            node_ids,
            coverage_boundaries_count,
            max_trace_size
        )
        plot_type = "fixed_coverage_box_plot"

        df_p = df_path(graphs_folder, project_root, module, plot_type)
        df_fixed_coverage.to_csv(df_p)

        image_p = image_path(graphs_folder, project_root, module, plot_type)
        title = f"{Path(module).name}, {total_bugs} bugs"
        create_box_plot(df_fixed_coverage, title, image_p,
                        x=SUITE_COVERAGE_BIN, y=BUG_REVEALED_SCORE, hue=METRIC,
                        xlabel="Test suite coverage (%)", ylabel="Bugs revealed")

        plot_type = "fixed_coverage_cat_plot"
        image_p = image_path(graphs_folder, project_root, module, plot_type)
        create_cat_plot(df_fixed_coverage, title, image_p,
                        x=SUITE_COVERAGE_BIN, y=BUG_REVEALED_SCORE, hue=METRIC,
                        xlabel="Test suite coverage (%)", ylabel="Bugs revealed")

        plot_type = "fixed_coverage_count_plot"
        image_p = image_path(graphs_folder, project_root, module, plot_type)
        create_cat_plot_with_count(df_fixed_coverage, title, image_p,
                                   x=SUITE_COVERAGE_BIN, y=BUG_REVEALED_SCORE, hue=METRIC,
                                   xlabel="Test suite coverage (%)", ylabel="Bugs revealed")


    module = args.module
    node_ids = args.node_ids
    if not module:
        selected_modules = trace_reader.get_modules_covered_by_nodes(node_ids)
        for module in selected_modules:
            experiment(module)
    else:
        module = maybe_expand(module)
        experiment(module)

    exit(0)
