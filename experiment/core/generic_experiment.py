import operator
import os
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

from config import COMMON_EXCLUDE
from coverage_metrics.coverage_metric_enum import CoverageMetric
from experiment.suites.collect_test_suite import random_suites
from experiment.suites.suite_generator import SuiteGenerator
from model.cfg.project_cfg import ProjectCFG
from tracing.trace_reader import TraceReader

RANDOM_STRATEGY = 1337
DEFAULT_METRICS = (
    # CoverageMetric.STATEMENT,
    CoverageMetric.BRANCH,
    # CoverageMetric.M_ONLY,
    # CoverageMetric.IC_ONLY,
    # CoverageMetric.IM_ONLY,
    # CoverageMetric.M_AND_IC,
    # CoverageMetric.M_AND_IM,
    CoverageMetric.ALL_PAIRS,
    # RANDOM_STRATEGY
)
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


def generic_experiment_size(
        project_root, module_under_test_path,
        scoring_function,
        test_suite_sizes_count=30,
        test_suite_sizes=None,
        max_trace_size=10,
        coverage_metrics=None,
        node_ids=None,
        support=100
):
    logger.debug("Running mutation experiment for {module}", module=module_under_test_path)

    if coverage_metrics is None:
        coverage_metrics = DEFAULT_METRICS
    cfg = ProjectCFG.create_from_path(project_root, exclude_folders=COMMON_EXCLUDE)
    if node_ids is None:
        trace_reader = TraceReader(project_root)
        node_ids, paths = trace_reader.get_traces_for(module_under_test_path)
    total_cases = len(node_ids)
    if test_suite_sizes is None:
        if total_cases < test_suite_sizes_count:
            test_suite_sizes_count = total_cases
        test_suite_sizes = np.arange(test_suite_sizes_count) + 1
        test_suite_sizes = [int(c * total_cases / test_suite_sizes_count) for c in test_suite_sizes]

    logger.debug("Testing test suites of sizes {ss}", ss=test_suite_sizes)
    generator = SuiteGenerator(project_root, project_root, COMMON_EXCLUDE, max_trace_size=max_trace_size)
    points = []

    for sub_test_suites_size in test_suite_sizes:
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
                    check_unique_items_covered=False,
                    test_cases=node_ids
                )

            for suite in suites:
                mutation_score = scoring_function(suite)
                point = (sub_test_suites_size, metric_names[coverage_metric], mutation_score, suite.coverage)
                points.append(point)
    return points


def generic_experiment_coverage(
        project_root,
        module_under_test_path,
        scoring_function,
        coverage_boundaries_count=20,
        max_trace_size=10,
        coverage_metrics=None,
        node_ids=None,
        support=100
):
    cfg = ProjectCFG.create_from_path(project_root, exclude_folders=COMMON_EXCLUDE)

    if coverage_metrics is None:
        coverage_metrics = DEFAULT_METRICS

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
                check_unique_items_covered=False,
                test_cases=node_ids
            )

            for suite in suites:
                mutation_score = scoring_function(suite)
                point = (len(suite.test_cases), metric_names[metric], mutation_score, suite.coverage)
                points.append(point)

    return points


def bin_zero_to_one_column_to_percent(df, column_to_bin, bin_column_name, bin_count):
    bins = np.linspace(0, 100, num=bin_count + 1, dtype=int, endpoint=True)
    bin_labels = [f"[{int(np.floor(l))}-{int(np.ceil(r))}]" for l, r in zip(bins[:-1], bins[1:])]
    kw = {bin_column_name: lambda x: pd.cut(x[column_to_bin], bins=bins, labels=bin_labels)}

    df: pd.DataFrame = df.assign(**kw)
    return df


def project_stats(cfg):
    stats = []
    for module_path, mod_cfg in cfg.module_cfgs.items():
        count_im = len(mod_cfg.intermethod_pairs)
        count_ic = len(mod_cfg.interclass_pairs)
        stats.append((module_path, count_im, count_ic))
    return stats


def select_modules(project_root, max_of_each_category=1, min_pairs=0, exclude_cfg=None):
    if not exclude_cfg:
        exclude_cfg = COMMON_EXCLUDE

    cfg = ProjectCFG.create_from_path(project_root, exclude_folders=exclude_cfg)
    selected_modules = set()
    stats = project_stats(cfg)
    c = 0
    for module_path, count_im, count_ic in sorted(stats, key=operator.itemgetter(1), reverse=True):
        if count_im > 0:
            if count_im < min_pairs:
                continue
            c += 1
            if c > max_of_each_category:
                break
            else:
                selected_modules.add(module_path)
    c = 0
    for module_path, count_im, count_ic in sorted(stats, key=operator.itemgetter(2), reverse=True):
        if count_ic > 0:
            if count_ic < min_pairs:
                continue
            c += 1
            if c > max_of_each_category:
                break
            else:
                selected_modules.add(module_path)
    return selected_modules


def image_path(graphs_path, project_root, module_path, mark):
    pname = Path(project_root).name
    rel_p = str(Path(module_path).relative_to(project_root))

    file_name = pname + "@" + rel_p.replace("/", "::") + "::" + mark + ".png"

    image_p = os.path.join(graphs_path, file_name)
    os.makedirs(graphs_path, exist_ok=True)
    return image_p


def df_path(graphs_path, project_root, module_path, mark):
    pname = Path(project_root).name
    rel_p = str(Path(module_path).relative_to(project_root))

    file_name = pname + "@" + rel_p.replace("/", "::") + "::" + mark + ".csv"

    image_p = os.path.join(graphs_path, file_name)
    os.makedirs(graphs_path, exist_ok=True)
    return image_p


def module_path(graphs_path, project_root, module_path):
    pname = Path(project_root).name
    rel_p = str(Path(module_path).relative_to(project_root))

    file_name = pname + "@" + rel_p.replace("/", "::")

    image_p = os.path.join(graphs_path, file_name)
    os.makedirs(graphs_path, exist_ok=True)
    return image_p
