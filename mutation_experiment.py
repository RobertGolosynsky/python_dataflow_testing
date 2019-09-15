import argparse
import operator
import os
from loguru import logger
from collections import defaultdict, namedtuple
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from config import COMMON_EXCLUDE
from coverage_metrics.coverage_metric_enum import CoverageMetric

from experiment.collect_test_suite import SubTestSuite, random_suites
from experiment.suite_generator import SuiteGenerator
from model.cfg.project_cfg import ProjectCFG
from tracing.trace_reader import TraceReader
from experiment.mutation import killed_mutants
from util.misc import scale

DataPoint = namedtuple("DataPoint", ["metric", "coverage", "mut_score", "suite_size"])

RANDOM_STRATEGY = 1337
color = {
    CoverageMetric.STATEMENT: "tab:gray",
    CoverageMetric.BRANCH: "tab:blue",
    CoverageMetric.M_ONLY: "tab:orange",
    CoverageMetric.IC_ONLY: "tab:pink",
    CoverageMetric.IM_ONLY: "tab:purple",
    CoverageMetric.M_AND_IC: "tab:cyan",
    CoverageMetric.M_AND_IM: "tab:blue",
    CoverageMetric.ALL_PAIRS: "tab:red",
    RANDOM_STRATEGY: "tab:olive"
}
marker = {
    CoverageMetric.STATEMENT: "<",
    CoverageMetric.BRANCH: "o",
    CoverageMetric.M_ONLY: "*",
    CoverageMetric.IC_ONLY: "d",
    CoverageMetric.IM_ONLY: "D",
    CoverageMetric.M_AND_IC: "x",
    CoverageMetric.M_AND_IM: "P",
    CoverageMetric.ALL_PAIRS: "s",
    RANDOM_STRATEGY: ">"

}

metric_names = {
    CoverageMetric.STATEMENT: "Statement",
    CoverageMetric.BRANCH: "Branch",
    CoverageMetric.M_ONLY: "Only intramethod",
    CoverageMetric.IC_ONLY: "Only interclass",
    CoverageMetric.IM_ONLY: "Only intermethod",
    CoverageMetric.M_AND_IC: "Intramethod and interclass",
    CoverageMetric.M_AND_IM: "Intramethod and intermethod",
    CoverageMetric.ALL_PAIRS: "All pairs",
    RANDOM_STRATEGY: "Random"
}


def run_mutation_experiment_fixed_size(
        project_root, module_under_test_path,
        evaluation_points=30,
        max_trace_size=10,
):
    logger.debug("Running mutation experiment for {module}", module=module_under_test_path)
    cfg = ProjectCFG.create_from_path(project_root, exclude_folders=COMMON_EXCLUDE)

    trace_reader = TraceReader(project_root)

    coverage_metrics = [
        # CoverageMetric.STATEMENT,
        CoverageMetric.BRANCH,
        # CoverageMetric.M_ONLY,
        # CoverageMetric.IC_ONLY,
        # CoverageMetric.IM_ONLY,
        # CoverageMetric.M_AND_IC,
        # CoverageMetric.M_AND_IM,
        CoverageMetric.ALL_PAIRS,
        RANDOM_STRATEGY
    ]

    node_ids, paths = trace_reader.get_traces_for(module_under_test_path)

    killed, total_mutants = killed_mutants(
        project_root=project_root,
        path_to_module_under_test=module_under_test_path,
        test_cases_ids=tuple(node_ids),
    )

    total_cases = len(node_ids)

    # support = 5 + int(math.sqrt(total_cases)) * 2
    support = 100

    if total_cases < evaluation_points:
        evaluation_points = total_cases
    sub_test_suites_sizes = np.arange(evaluation_points) + 1
    sub_test_suites_sizes = [int(c * total_cases / evaluation_points) for c in sub_test_suites_sizes]

    logger.debug("Testing test suites of sizes {ss}", ss=sub_test_suites_sizes)
    generator = SuiteGenerator(project_root, project_root, COMMON_EXCLUDE, max_trace_size=max_trace_size)
    experiment_data = {}

    for sub_test_suites_size in sub_test_suites_sizes:
        experiment_data[sub_test_suites_size] = defaultdict(list)
        for coverage_metric in coverage_metrics:
            logger.debug("Test suite size: {sub_test_suites_size}, metric: {coverage_metric}",
                         sub_test_suites_size=sub_test_suites_size,
                         coverage_metric=coverage_metric)
            if coverage_metric == RANDOM_STRATEGY:
                suites = random_suites(node_ids, sub_test_suites_size, support)
            else:
                suites = generator.fix_sized_suites(
                    module_under_test_path=module_under_test_path,
                    coverage_metric=coverage_metric,
                    exact_size=sub_test_suites_size,
                    n=support,
                    check_unique_items_covered=True,
                )

            for suite in suites:
                mutation_score = count_suite_mutation_score(suite, killed, total_mutants)
                experiment_data[sub_test_suites_size][coverage_metric].append((suite, mutation_score))
    return experiment_data, support, total_mutants
    # title = "{}:{}:{}".format(Path(project_root).name, Path(module_under_test_path).name, total_mutants)
    # draw_fixed_size(experiment_data, title, image_path, support)


def run_mutation_experiment_fixed_coverage(
        project_root,
        module_under_test_path,
        coverage_boundaries_count=20,
        max_trace_size=10
):
    cfg = ProjectCFG.create_from_path(project_root, exclude_folders=COMMON_EXCLUDE)

    trace_reader = TraceReader(project_root)

    coverage_metrics = [
        # CoverageMetric.STATEMENT,
        CoverageMetric.BRANCH,
        # CoverageMetric.M_ONLY,
        # CoverageMetric.IC_ONLY,
        # CoverageMetric.IM_ONLY,
        # CoverageMetric.M_AND_IC,
        # CoverageMetric.M_AND_IM,
        CoverageMetric.ALL_PAIRS,
        # RANDOM_STRATEGY
    ]

    node_ids, paths = trace_reader.get_traces_for(module_under_test_path)

    killed, total_mutants = killed_mutants(
        project_root=project_root,
        path_to_module_under_test=module_under_test_path,
        test_cases_ids=tuple(node_ids),
    )

    # support = 5 + int(math.sqrt(total_cases)) * 2
    support = 100

    coverage_boundaries = np.linspace(0.05, 1.0, num=coverage_boundaries_count)

    generator = SuiteGenerator(project_root, project_root, COMMON_EXCLUDE, max_trace_size=max_trace_size)
    points = []

    for boundary in coverage_boundaries:
        for metric in coverage_metrics:
            logger.debug("Coverage boundary: {boundary}, metric: {coverage_metric}", boundary=boundary,
                         coverage_metric=metric)
            suites = generator.fix_coverage_suites(
                module_under_test_path=module_under_test_path,
                coverage_metric=metric,
                coverage_boundary=boundary,
                n=support,
                check_unique_items_covered=True,
            )

            for suite in suites:
                mutation_score = count_suite_mutation_score(suite, killed, total_mutants)
                point = DataPoint(metric, suite.coverage, mutation_score, len(suite.test_cases))
                points.append(point)
    return points, total_mutants
    # title = "{}:{}:{}".format(Path(project_root).name, Path(module_under_test_path).name, total_mutants)
    # draw_fixed_coverage(points, title, image_path, support)


def draw_fixed_size(experiment_data, title, filename, support):
    stat = defaultdict(dict)
    added_legend = set()
    plt.figure(figsize=(16, 8))
    for suite_size in experiment_data:
        for metric in experiment_data[suite_size]:

            scores = []
            coverages = []
            stat[metric][suite_size] = len(experiment_data[suite_size][metric])
            for sub_suite, mutation_score in experiment_data[suite_size][metric]:
                scores.append(mutation_score)
                coverages.append(sub_suite.coverage)

            max_size = 80
            min_size = 10
            label = metric_names[metric] if metric not in added_legend else ""
            # m_size = np.average(scores) * max_size
            m_size = scale((len(scores) / support), min_size, max_size)
            plt.scatter(suite_size, np.average(scores),
                        c=color[metric],
                        marker=marker[metric],
                        alpha=0.7,
                        label=label,
                        s=m_size
                        )

            added_legend.add(metric)

    plt.title(title)
    plt.xlabel("Test suite size")
    plt.ylabel("Mutants killed (%)")
    # plt.legend(loc='lower right', numpoints=1)
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), numpoints=1)

    plt.tight_layout()

    plt.savefig(filename)
    plt.close()


def draw_fixed_coverage(points, title, filename):
    added_legend = set()
    plt.figure(figsize=(16, 8))
    for point in points:
        max_size = 80
        min_size = 10
        metric = point.metric
        label = metric_names[metric] if metric not in added_legend else ""
        # m_size = np.average(scores) * max_size
        # m_size = scale((len(scores) / support), min_size, max_size)
        plt.scatter(point.coverage, point.mut_score,
                    c=color[metric],
                    marker=marker[metric],
                    alpha=0.7,
                    label=label,
                    s=20
                    )

        added_legend.add(point.metric)
    plt.title(title)
    plt.xlabel("Coverage")
    plt.ylabel("Mutants killed (%)")
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), numpoints=1)

    plt.tight_layout()

    plt.savefig(filename)
    plt.close()


def count_suite_mutation_score(suite: SubTestSuite, killed, total):
    killed_muts = set()
    for case in suite.test_cases:
        killed_muts.update(killed[case])

    return len(killed_muts) / total


def project_stats(cfg):
    stats = []
    for module_path, mod_cfg in cfg.module_cfgs.items():
        count_im = len(mod_cfg.intermethod_pairs)
        count_ic = len(mod_cfg.interclass_pairs)
        stats.append((module_path, count_im, count_ic))
    return stats


def select_modules(project_root, max_of_each_category=1, exclude_cfg=None):
    if not exclude_cfg:
        exclude_cfg = COMMON_EXCLUDE

    cfg = ProjectCFG.create_from_path(project_root, exclude_folders=exclude_cfg)
    selected_modules = set()
    stats = project_stats(cfg)
    c = 0
    for module_path, count_im, count_ic in sorted(stats, key=operator.itemgetter(1), reverse=True):
        if count_im > 0:
            c += 1
            if c > max_of_each_category:
                break
            else:
                selected_modules.add(module_path)
    c = 0
    for module_path, count_im, count_ic in sorted(stats, key=operator.itemgetter(2), reverse=True):
        if count_ic > 0:
            c += 1
            if c > max_of_each_category:
                break
            else:
                selected_modules.add(module_path)
    return selected_modules


def image_path(graphs_path, project_root, module_path, mark):
    pname = Path(project_root).name
    rel_p = str(Path(module_path).relative_to(project_root))

    file_name = pname + "@" + rel_p.replace("/", "::") + mark + ".png"

    image_p = os.path.join(graphs_path, file_name)
    os.makedirs(graphs_path, exist_ok=True)
    return image_p


def full_experiment(module_under_test_path, evaluation_points, coverage_boundaries_count, max_trace_size):
    run_mutation_experiment_fixed_coverage(
        project_root, module_under_test_path,
        coverage_boundaries_count=coverage_boundaries_count,
        max_trace_size=max_trace_size
    )


def maybe_expand(path):
    p = Path(path)
    if p.is_absolute():
        return str(p)
    else:
        return str(p.resolve())


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Mutation experiment')
    parser.add_argument('--module', type=str, help='Module under test path')

    parser.add_argument('--max_select', type=int, help='Select modules based on pairs count')
    parser.add_argument('--exclude_folders', nargs="+", help='<Required> Set flag')

    parser.add_argument('--graphs_folder', type=str, help='Folder for resulting graphs')

    parser.add_argument('--test_suite_sizes_count', type=int,
                        help='How many sub test suite sizes to test (between min and max available)')
    parser.add_argument('--test_suite_coverages_count', type=int, help='How many bins for coverage to use')
    parser.add_argument('--max_trace_size', type=int, help='Largest trace file to open (MB)')

    args, unknown = parser.parse_known_args()

    project_root = maybe_expand("")
    evaluation_points = args.test_suite_sizes_count
    coverage_boundaries_count = args.test_suite_coverages_count
    max_trace_size = args.max_trace_size
    graphs_folder = maybe_expand(args.graphs_folder)


    def experiment(module):
        data_s, support, total_mutants = run_mutation_experiment_fixed_size(
            project_root,
            module,
            evaluation_points,
            max_trace_size
        )
        title = f"{Path(module).name}, {total_mutants} mutants"
        image_p = image_path(graphs_folder, project_root, module, "fixed_size")

        draw_fixed_size(data_s, title, image_p, support)

        data_c, total_mutants = run_mutation_experiment_fixed_coverage(
            project_root,
            module,
            evaluation_points,
            max_trace_size
        )
        title = f"{Path(module).name}, {total_mutants} mutants"
        image_p = image_path(graphs_folder, project_root, module, "fixed_coverage")
        draw_fixed_coverage(data_c, title, image_p)


    module = args.module
    if not module:
        max_of_each_category = args.max_select
        exclude_cfg = args.exclude_folders
        selected_modules = select_modules(project_root, max_of_each_category=max_of_each_category,
                                          exclude_cfg=exclude_cfg)
        for module in selected_modules:
            experiment(module)
    else:
        module = maybe_expand(module)
        experiment(module)
