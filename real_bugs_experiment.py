import shutil

from joblib import Memory
import thorough

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
from mutation_experiment import metric_names, color, marker, image_path
from tracing.trace_reader import TraceReader
from util.misc import scale, maybe_expand

DataPoint = namedtuple("DataPoint", ["metric", "coverage", "mut_score", "suite_size"])

RANDOM_STRATEGY = 1337
memory = Memory(location=".cached_real_projects_experiment", verbose=0)


def bugs_revealed(revealing_node_ids, suite: SubTestSuite):
    used_reveling_node_ids = revealing_node_ids.intersection(set(suite.test_cases))
    return len(used_reveling_node_ids)


def run_real_bugs_experiment_fixed_size(
        project_root,
        module_under_test_path,
        revealing_node_ids,
        evaluation_points=30,
        max_trace_size=10

):
    logger.debug("Running real project experiment for {module} (fixed size)", module=module_under_test_path)
    cfg = ProjectCFG.create_from_path(project_root, exclude_folders=COMMON_EXCLUDE)

    if not isinstance(revealing_node_ids, set):
        revealing_node_ids = set(revealing_node_ids)
    total_failing_node_ids = len(revealing_node_ids)

    trace_reader = TraceReader(project_root)

    coverage_metrics = [
        # CoverageMetric.STATEMENT,
        CoverageMetric.BRANCH,
        CoverageMetric.M_ONLY,
        # CoverageMetric.IC_ONLY,
        # CoverageMetric.IM_ONLY,
        CoverageMetric.M_AND_IC,
        CoverageMetric.M_AND_IM,
        CoverageMetric.ALL_PAIRS,
        RANDOM_STRATEGY
    ]

    node_ids, paths = trace_reader.get_traces_for(module_under_test_path)

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
                score = bugs_revealed(revealing_node_ids, suite)
                experiment_data[sub_test_suites_size][coverage_metric].append((suite, score))
    return experiment_data, support, total_failing_node_ids


def run_real_bugs_experiment_fixed_coverage(
        project_root,
        module_under_test_path,
        revealing_node_ids,
        coverage_boundaries_count=20,
        max_trace_size=10
):
    logger.debug("Running real project experiment for {module} (fixed coverage)", module=module_under_test_path)

    if not isinstance(revealing_node_ids, set):
        revealing_node_ids = set(revealing_node_ids)
    total_failing_node_ids = len(revealing_node_ids)

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
                mutation_score = bugs_revealed(revealing_node_ids, suite)
                point = DataPoint(metric, suite.coverage, mutation_score, len(suite.test_cases))
                points.append(point)
    return points, total_failing_node_ids


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
    plt.ylabel("Bugs revealed (%)")
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
    plt.ylabel("Bugs revealed (%)")
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), numpoints=1)

    plt.tight_layout()

    plt.savefig(filename)
    plt.close()


def project_stats(cfg):
    stats = []
    for module_path, mod_cfg in cfg.module_cfgs.items():
        count_im = len(mod_cfg.intermethod_pairs)
        count_ic = len(mod_cfg.interclass_pairs)
        stats.append((module_path, count_im, count_ic))
    return stats


def select_modules(trace_root, node_ids):
    trace_reader = TraceReader(trace_root)
    selected_modules = set()
    for node_id in node_ids:
        selected_modules.update(trace_reader.get_modules_covered_by(node_id))

    return selected_modules


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
    evaluation_points = args.test_suite_sizes_count
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
        data_s, support, total_bugs = run_real_bugs_experiment_fixed_size(
            project_root,
            module,
            node_ids,
            evaluation_points,
            max_trace_size
        )
        title = f"{Path(module).name}, {total_bugs} bugs"
        image_p = image_path(graphs_folder, project_root, module, "fixed_size")

        draw_fixed_size(data_s, title, image_p, support)
        new_module_path = image_p + ".py"
        shutil.copy(module, new_module_path)

        data_c, total_bugs = run_real_bugs_experiment_fixed_coverage(
            project_root,
            module,
            node_ids,
            evaluation_points,
            max_trace_size
        )
        title = f"{Path(module).name}, {total_bugs} bugs"
        image_p = image_path(graphs_folder, project_root, module, "fixed_coverage")
        draw_fixed_coverage(data_c, title, image_p)


    module = args.module
    if not module:
        node_ids = args.node_ids
        selected_modules = select_modules(trace_root, node_ids)
        for module in selected_modules:
            experiment(module)
    else:
        module = maybe_expand(module)
        experiment(module)

    exit(0)
