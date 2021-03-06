import argparse
import shutil

from pathlib import Path

from experiment.core.mutation_experiment import run_mutation_experiment_fixed_size, \
    SUITE_SIZE, MUTATION_SCORE, METRIC, \
    run_mutation_experiment_fixed_coverage, SUITE_COVERAGE_BIN
from experiment.core.generic_experiment import image_path, select_modules, df_path, module_path
from experiment.core.visualization import create_box_plot, create_cat_plot_with_count
from util.misc import maybe_expand

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Mutation experiment')
    parser.add_argument('--module', type=str, help='Module under test path')

    parser.add_argument('--max_select', type=int, help='Select modules based on pairs count')
    parser.add_argument('--min_pairs', type=int,
                        help='Minimum amount interclass and intermethod pairs in a module to select it')
    parser.add_argument('--timeout', type=int, help='Maximum mutation time per module (will fail if takes longer)')
    parser.add_argument('--exclude_folders', nargs="+", help='Folders to exclude during cfg creation')

    parser.add_argument('--graphs_folder', type=str, help='Folder for resulting graphs')

    parser.add_argument('--test_suite_sizes_count', type=int,
                        help='How many sub test suite sizes to test (between min and max available)')
    parser.add_argument('--test_suite_coverages_count', type=int, help='How many bins for coverage to use')
    parser.add_argument('--max_trace_size', type=int, help='Largest trace file to open (MB)')

    args, unknown = parser.parse_known_args()

    project_root = maybe_expand("")
    test_suite_sizes_count = args.test_suite_sizes_count
    coverage_boundaries_count = args.test_suite_coverages_count
    max_trace_size = args.max_trace_size
    graphs_folder = maybe_expand(args.graphs_folder)


    def experiment(module_under_test):

        df_fixed_size, total_mutants = run_mutation_experiment_fixed_size(
            project_root,
            module_under_test,
            test_suite_sizes_count,
            max_trace_size,
            args.timeout
        )
        plot_type = "fixed_size_box_plot"
        title = f"{Path(module_under_test).name}, {total_mutants} mutants"
        df_p = df_path(graphs_folder, project_root, module_under_test, plot_type)
        df_fixed_size.to_csv(df_p)

        image_p = image_path(graphs_folder, project_root, module_under_test, plot_type)
        create_box_plot(df_fixed_size, title, image_p,
                        x=SUITE_SIZE, y=MUTATION_SCORE, hue=METRIC,
                        xlabel="Test suite size", ylabel="Mutants killed (%)")

        image_p = image_path(graphs_folder, project_root, module_under_test, "count_plot_fixed_size")
        create_cat_plot_with_count(df_fixed_size, title, image_p,
                                   x=SUITE_SIZE, y=MUTATION_SCORE, hue=METRIC,
                                   xlabel="Test suite size", ylabel="Mutants killed (%)", no_ordering=True)

        new_module_path = module_path(graphs_folder, project_root, module_under_test)
        shutil.copy(module_under_test, new_module_path)

        # fixed coverage
        plot_type = "fixed_coverage_box_plot"
        df_fixed_coverage, total_mutants = run_mutation_experiment_fixed_coverage(
            project_root,
            module_under_test,
            test_suite_sizes_count,
            max_trace_size,
            args.timeout
        )
        df_p = df_path(graphs_folder, project_root, module_under_test, plot_type)
        df_fixed_coverage.to_csv(df_p)

        title = f"{Path(module_under_test).name}, {total_mutants} mutants"
        image_p = image_path(graphs_folder, project_root, module_under_test, plot_type)
        create_box_plot(df_fixed_coverage, title, image_p,
                        x=SUITE_COVERAGE_BIN, y=MUTATION_SCORE, hue=METRIC,
                        xlabel="Test suite coverage", ylabel="Mutants killed (%)")

        image_p = image_path(graphs_folder, project_root, module_under_test, "count_plot_fixed_coverage")
        create_cat_plot_with_count(df_fixed_coverage, title, image_p,
                                   x=SUITE_COVERAGE_BIN, y=MUTATION_SCORE, hue=METRIC,
                                   xlabel="Test suite coverage", ylabel="Mutants killed (%)")


    module = args.module
    if not module:
        max_of_each_category = args.max_select
        exclude_cfg = args.exclude_folders
        selected_modules = select_modules(project_root, max_of_each_category=max_of_each_category,
                                          min_pairs=args.min_pairs,
                                          exclude_cfg=exclude_cfg)
        for module in selected_modules:
            experiment(module)
    else:
        module = maybe_expand(module)
        experiment(module)
