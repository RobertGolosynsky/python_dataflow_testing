import operator
import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from typing import List

from tqdm import tqdm

from coverage_metrics.coverage_metric_enum import CoverageMetric
from experiment.core.columns import *
import numpy as np
from playhouse.sqlite_ext import SqliteExtDatabase

from experiment.core.columns import DataFrameType
from experiment.db_model.repo import DATABASE_PROXY, Module, Repo
from experiment.folders import results_root
from experiment.visualization.dataset_visualization import visualize_dataset
from experiment.visualization.other import read_combined_df, read_data_frames_of_type, load_data_frames, draw_vertically

# STATEMENT = CoverageMetric.STATEMENT.__repr__()
MIN_ALL_PAIRS_COVERAGE = "Min all pairs coverage"
MAX_ALL_PAIRS_COVERAGE = "Max all pairs coverage"
MIN_BRANCH_COVERAGE = "Min branch coverage"
MAX_BRANCH_COVERAGE = "Max branch coverage"
MIN_STATEMENT_COVERAGE = "Min statement coverage"
MAX_STATEMENT_COVERAGE = "Max statement coverage"
MAX_SUITE_SIZE = "Max suite size"
REPO = "Repo"


def draw_grouped_fixed_size(root, repo_ids, img_folder="", image_file=""):
    # size
    size_dfs = [read_combined_df(root, repo_id, DataFrameType.FIXED_SIZE) for repo_id in repo_ids]
    size_dfs = [df.groupby([SUITE_SIZE, METRIC], as_index=False).mean() for df in size_dfs]
    size_dfs = pd.concat(size_dfs, axis=0, ignore_index=True, sort=False)
    if not image_file:
        image_file = Path(img_folder) / "fixed_size_grouped.png"
    draw_vertically(size_dfs, SUITE_SIZE, image_file)


def draw_grouped_fixed_coverage(root, repo_ids, img_folder="", image_file=""):
    # # coverage
    coverage_dfs = [read_combined_df(root, repo_id, DataFrameType.FIXED_COVERAGE) for repo_id in repo_ids]

    coverage_dfs = [df.groupby([SUITE_COVERAGE_BIN, METRIC], as_index=False).mean() for df in coverage_dfs]
    coverage_dfs = pd.concat(coverage_dfs, axis=0, ignore_index=True, sort=False)
    if not image_file:
        image_file = Path(img_folder) / "fixed_coverage_grouped.png"

    draw_vertically(coverage_dfs, SUITE_COVERAGE_BIN, image_file)


if __name__ == "__main__":
    lim = 1000
    off = 0
    flag = "no_filter"
    data_path = results_root / "graphs_cumulative_off_0_lim_1000all"
    graphs_path = results_root / "graphs_cumulative_off_{}_lim_{}{}".format(off, lim, flag)
    general_graphs = graphs_path / "graphs"
    # os.makedirs(graphs_path, exist_ok=True)
    # os.makedirs(general_graphs, exist_ok=True)

    database = "../selection.db"

    db = SqliteExtDatabase(
        database,
        pragmas={
            "journal_mode": "wal",
            "cache_size": -64 * 1000,
            "foreign_key": 1,
            "ignore_check_constraints": 9,
            "synchronous": 0,
        }
    )
    DATABASE_PROXY.initialize(db)
    # .where(Module.total_cases < 100) \
    #     .where(Module.bugs < 8) \
    ms: List[Module] = Module.select() \
        .join(Repo) \
        .group_by(Repo.name) \
        .order_by(Module.total_cases.desc()) \
        .offset(off) \
        .limit(lim)
    ms = list(ms)
    repos = []

    for m in ms:
        repo_id = m.repo.id
        repo_id = repo_id.replace("@", "_")
        df = read_combined_df(data_path, repo_id, DataFrameType.FIXED_SIZE)
        if df is not None:
            # print(df)
            metrics = df[METRIC].unique()
            if len(metrics) < 3:
                continue
            by_metric = df.groupby(METRIC)[SUITE_COVERAGE].agg(["min", "max"])

            r = (
                repo_id,
                df[SUITE_SIZE].max(),
                by_metric["max"][str(CoverageMetric.STATEMENT)],
                by_metric["max"][str(CoverageMetric.BRANCH)],
                by_metric["max"][str(CoverageMetric.ALL_PAIRS)],
                by_metric["min"][str(CoverageMetric.STATEMENT)],
                by_metric["min"][str(CoverageMetric.BRANCH)],
                by_metric["min"][str(CoverageMetric.ALL_PAIRS)],
            )
            repos.append(r)

    data = pd.DataFrame(
        data=repos,
        columns=[
            REPO,
            MAX_SUITE_SIZE,
            MAX_STATEMENT_COVERAGE, MAX_BRANCH_COVERAGE,
            MAX_ALL_PAIRS_COVERAGE, MIN_STATEMENT_COVERAGE,
            MIN_BRANCH_COVERAGE, MIN_ALL_PAIRS_COVERAGE
        ]
    )


    def get_modules_from_db(repo_ids):
        repo_ids = [r.replace("_", "@") for r in repo_ids]
        ms: List[Module] = Module.select() \
            .join(Repo) \
            .group_by(Repo.name) \
            .where(Repo.id << repo_ids)
        return ms


    with pd.option_context('display.max_rows', None, 'display.max_columns',
                           None):  # more options can be specified also
        # print(data)
        min_cov = 90
        data = data.loc[
            #     # (data[MAX_STATEMENT_COVERAGE] > min_cov)
            #     # & (data[MAX_BRANCH_COVERAGE] > min_cov)
            #     # & (data[MAX_ALL_PAIRS_COVERAGE] > min_cov)
            #     # &
            (data[MAX_SUITE_SIZE] > 4)
            #     & (data[MAX_SUITE_SIZE] < 100 )
        ]
        data = data.sort_values(MAX_SUITE_SIZE, ascending=False)
        dataset_stats_folder = general_graphs / "dataset_stats"
        os.makedirs(dataset_stats_folder)
        visualize_dataset(get_modules_from_db(data[REPO]), dataset_stats_folder)

        for window_size in [4, 8, 16]:
            window_folder = general_graphs / f"window_size{window_size}"
            os.makedirs(window_folder, exist_ok=True)
            for i in tqdm(range(len(data) - window_size)):
                im_size = window_folder / f"im{i}-{i + window_size}_fixed_size.png"
                im_coverage = window_folder / f"im{i}-{i + window_size}_fixed_coverage.png"
                stat_folder = window_folder / f"stats{i}-{i + window_size}"

                os.makedirs(stat_folder, exist_ok=True)

                repo_ids = data[i:i + window_size][REPO]
                visualize_dataset(get_modules_from_db(repo_ids), stat_folder)

                draw_grouped_fixed_size(data_path, repo_ids, image_file=im_size)
                draw_grouped_fixed_coverage(data_path, repo_ids, image_file=im_coverage)

# for i, (repo_id, suite_size) in zip(np.arange(100), sorted(repos, key=operator.itemgetter(1), reverse=True)):
#     print(i, repo_id, suite_size)
# fig, ax = plt.figure()
# ax = sns.countplot(data=data, x=MAX_SUITE_SIZE)
# fig, ax = plt.subplots(3, 1, sharex=False)
# sns.swarmplot(data=data, y=MAX_ALL_PAIRS_COVERAGE, ax=ax[0], orient="h")
# sns.boxplot(data=data, y=MAX_BRANCH_COVERAGE, ax=ax[1], orient="h")
# sns.boxplot(data=data, y=MAX_STATEMENT_COVERAGE, ax=ax[2], orient="h")
# ax.set(xlabel='Max test suite size', ylabel='Number of projects')
# plt.show()
