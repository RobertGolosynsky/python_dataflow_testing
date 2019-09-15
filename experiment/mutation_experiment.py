import math
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


def count_suite_mutation_score(suite: SubTestSuite, killed, total):
    killed_muts = set()
    for case in suite.test_cases:
        killed_muts.update(killed[case])

    return len(killed_muts) / total


def run_mutation_experiment_fixed_size(
        project_root, module_under_test_path, image_path,
        evaluation_points=30,
        max_trace_size=10,
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
    print("support:", support)
    if total_cases < evaluation_points:
        evaluation_points = total_cases
    sub_test_suites_sizes = np.arange(evaluation_points) + 1
    sub_test_suites_sizes = [int(c * total_cases / evaluation_points) for c in sub_test_suites_sizes]

    generator = SuiteGenerator(project_root, project_root, COMMON_EXCLUDE, max_trace_size=max_trace_size)
    experiment_data = {}

    for sub_test_suites_size in sub_test_suites_sizes:
        experiment_data[sub_test_suites_size] = defaultdict(list)
        for coverage_metric in coverage_metrics:
            print("size:", sub_test_suites_size, "coverage_metric:", coverage_metric)
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

    title = "{}:{}:{}".format(Path(project_root).name, Path(module_under_test_path).name, total_mutants)
    draw_fixed_size(experiment_data, title, image_path, support)


DataPoint = namedtuple("DataPoint", ["metric", "coverage", "mut_score", "suite_size"])


def run_mutation_experiment_fixed_coverage(
        project_root, module_under_test_path, image_path,
        max_trace_size=10,
        coverage_boundaries_count=20
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
    print("support:", support)

    coverage_boundaries = np.linspace(0.05, 1.0, num=coverage_boundaries_count)

    generator = SuiteGenerator(project_root, project_root, COMMON_EXCLUDE, max_trace_size=max_trace_size)
    points = []

    for boundary in coverage_boundaries:
        for metric in coverage_metrics:
            print("Coverage boundary:", boundary, "coverage_metric:", metric)
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

    title = "{}:{}:{}".format(Path(project_root).name, Path(module_under_test_path).name, total_mutants)
    draw_fixed_coverage(points, title, image_path, support)


def draw_fixed_coverage(points, title, filename, support):
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
