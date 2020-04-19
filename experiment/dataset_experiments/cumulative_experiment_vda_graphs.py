import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from typing import List

from loguru import logger

from coverage_metrics.coverage_metric_enum import CoverageMetric
from experiment.core.columns import *
from playhouse.sqlite_ext import SqliteExtDatabase

from experiment.core.columns import DataFrameType
from experiment.db_model.repo import DATABASE_PROXY, Module, Repo
from experiment.folders import results_root
from experiment.visualization.dataset_visualization import visualize_dataset
from experiment.visualization.other import read_combined_df, read_data_frames_of_type, load_data_frames, \
    draw_vertically, cov_bin_key

# STATEMENT = CoverageMetric.STATEMENT.__repr__()
MIN_ALL_PAIRS_COVERAGE = "Min all pairs coverage"
MAX_ALL_PAIRS_COVERAGE = "Max all pairs coverage"
MIN_BRANCH_COVERAGE = "Min branch coverage"
MAX_BRANCH_COVERAGE = "Max branch coverage"
MIN_STATEMENT_COVERAGE = "Min statement coverage"
MAX_STATEMENT_COVERAGE = "Max statement coverage"
MAX_SUITE_SIZE = "Max suite size"
REPO = "Repo"

SHORT_NAME = {
    CoverageMetric.BRANCH: "br",
    CoverageMetric.ALL_PAIRS: "du",
    CoverageMetric.STATEMENT: "st",
}


# VDA_ST_BUG = "VDA (ST) Bugs"
# VDA_BR_BUG = "VDA (BR) Bugs"
# VDA_ST_MUT = "VDA (ST) Mut"
# VDA_BR_MUT = "VDA (BR) Mut"


def a12slow(lst1, lst2):
    more = same = 0.0
    for x in sorted(lst1):
        for y in sorted(lst2):
            if x == y:
                same += 1
            elif x > y:
                more += 1
            else:
                break
    return (more + 0.5 * same) / (len(lst1) * len(lst2))


def vda_stat(metric_1, metric_2, cols, df):
    by_metric = df.groupby([METRIC])
    if metric_1.value in by_metric.groups.keys() \
            and metric_2.value in by_metric.groups.keys():
        gr1 = by_metric.get_group(metric_1.value)
        gr2 = by_metric.get_group(metric_2.value)
        vdas = []
        for col in cols:
            vda = a12slow(gr1[col], gr2[col])
            vdas.append(vda)
        return vdas
    else:
        return [None] * len(cols)


def _join(dfs, type, mean=False):
    if mean:
        dfs = [df.groupby([type, METRIC], as_index=False).mean() for df in dfs]
    dfs = pd.concat(dfs, axis=0, ignore_index=True, sort=False)
    return dfs


def _get_vda(df, group_by, cov_pairs):
    data = []
    for g_name, group in df.groupby([group_by], as_index=False):
        scores = [BUG_REVEALED_SCORE, MUTATION_SCORE]
        row = [g_name]
        for cov_pair in cov_pairs:
            bug, mut = vda_stat(cov_pair[0], cov_pair[1], scores, group)
            row += [bug, mut]
        data.append(row)
    columns = [group_by] + name_columns(cov_pairs)
    return pd.DataFrame(data=data, columns=columns)


def name_columns(cov_pairs):
    col_names = []
    for pair in cov_pairs:
        main, relative = map(SHORT_NAME.get, pair)
        col_names.append(f"VDA {main}/{relative} Bugs")
        col_names.append(f"VDA {main}/{relative} Muts")
    return col_names


def _add_lines(axs, small, medium, large, lim_0_1):
    s, m, l = 0.56, 0.64, 0.71
    for ax in axs:
        ax.axhline(0.5, ls='--', c="green", lw=2)
        if small:
            ax.axhline(s, ls=':', c="brown", lw=2)
            ax.axhline(1 - s, ls=':', c="brown", lw=2)
        if medium:
            ax.axhline(m, ls=':', c="red", lw=2)
            ax.axhline(1 - m, ls=':', c="red", lw=2)
        if large:
            ax.axhline(l, ls='--', c="orange", lw=2)
            ax.axhline(1 - l, ls='--', c="orange", lw=2)
        if lim_0_1:
            ax.set_ylim(0, 1)


def _draw(x, data, old, order, ys, mean):
    hue_order = list(sorted(old[METRIC].unique()))
    fig, axs = plt.subplots(len(ys) + 1, sharex=True, figsize=(16, 8))
    for y, ax in zip(ys, axs):
        sns.pointplot(x=x, y=y, data=data, ax=ax, lw=3, order=order)
    p = sns.countplot(x=x, hue=METRIC, data=old, palette="husl",
                      ax=axs[-1], lw=3, order=order, hue_order=hue_order)
    if mean:
        y_label = "Count projects"
    else:
        y_label = "Count suites"
    p.axes.yaxis.label.set_text(y_label)
    return fig, axs


def _generic_draw(root, repo_ids, df_type, mean,
                  cov_pairs,
                  img_folder="", image_file="",
                  small=True, medium=False, large=False, lim_0_1=False):
    group_by = SUITE_SIZE if df_type == DataFrameType.FIXED_SIZE else SUITE_COVERAGE_BIN
    dfs = [read_combined_df(root, repo_id, df_type) for repo_id in repo_ids]
    df = _join(dfs, group_by, mean=mean)

    vda_df = _get_vda(df, group_by, cov_pairs=cov_pairs)
    if df_type == DataFrameType.FIXED_SIZE:
        order = sorted(df[group_by].unique())
    else:
        order = list(sorted(df[group_by].unique(), key=cov_bin_key))
    ys = name_columns(cov_pairs)
    fig, axs = _draw(group_by, vda_df, df, order, ys, mean)
    _add_lines(axs[:-1], small, medium, large, lim_0_1)

    if not image_file:
        f = "fixed_size" if df_type == DataFrameType.FIXED_SIZE else "fixed_coverage"
        if mean:
            f += "_mean"
        image_file = Path(img_folder) / f"{f}_vda.png"
    plt.savefig(image_file, dpi=300)
    logger.info("Saved graph to {p}", p=image_file)


if __name__ == "__main__":

    use_fixed_version = False
    flag = "main"
    flag += "fixed" if use_fixed_version else "buggy"
    dataset_path = results_root / f"dataset_cumulative_off_{flag}"
    graphs_path = results_root / f"graphs_cumulative_off_{flag}"
    general_graphs = graphs_path / "graphs_vda"

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
        .order_by(Module.total_cases.desc())
    ms = list(ms)
    repos = []

    for m in ms:
        repo_id = m.repo.id
        repo_id = repo_id.replace("@", "_")
        df = read_combined_df(graphs_path, repo_id, DataFrameType.FIXED_SIZE)
        if df is not None:
            metrics = df[METRIC].unique()
            if len(metrics) < 3:
                continue
            by_metric = df.groupby(METRIC)[SUITE_COVERAGE].agg(["min", "max"])

            r = (
                repo_id,
                df[SUITE_SIZE].max(),
                # by_metric["max"][str(CoverageMetric.STATEMENT)],
                # by_metric["max"][str(CoverageMetric.BRANCH)],
                # by_metric["max"][str(CoverageMetric.ALL_PAIRS)],
                # by_metric["min"][str(CoverageMetric.STATEMENT)],
                # by_metric["min"][str(CoverageMetric.BRANCH)],
                # by_metric["min"][str(CoverageMetric.ALL_PAIRS)],
            )
            repos.append(r)

    data = pd.DataFrame(
        data=repos,
        columns=[
            REPO,
            MAX_SUITE_SIZE,
            # MAX_STATEMENT_COVERAGE, MAX_BRANCH_COVERAGE,
            # MAX_ALL_PAIRS_COVERAGE, MIN_STATEMENT_COVERAGE,
            # MIN_BRANCH_COVERAGE, MIN_ALL_PAIRS_COVERAGE
        ]
    )


    def get_modules_from_db(repo_ids):
        repo_ids = [r.replace("_", "@") for r in repo_ids]
        ms: List[Module] = Module.select() \
            .join(Repo) \
            .group_by(Repo.name) \
            .where(Repo.id << repo_ids)
        return ms


    def filter(data, min_suite_size=None, top=None, offset=None):
        # data = data.loc[
        #     #     # (data[MAX_STATEMENT_COVERAGE] > min_cov)
        #     #     # & (data[MAX_BRANCH_COVERAGE] > min_cov)
        #     #     # & (data[MAX_ALL_PAIRS_COVERAGE] > min_cov)
        #     #     # &
        #     (data[MAX_SUITE_SIZE] > 8)
        #     #     & (data[MAX_SUITE_SIZE] < 100 )
        # ]

        def add(q):
            if hasattr(filter, "query"):
                filter.query &= q
            else:
                filter.query = q

        if min_suite_size:
            add((data[MAX_SUITE_SIZE] > min_suite_size))

        flag = []

        if hasattr(filter, "query"):
            data = data[filter.query]
            flag += [str(len(filter.query))]
        else:
            flag += ["all"]

        if offset:
            data = data[offset:]
            flag += [f"offset{offset}"]

        if top:
            data = data[:top]
            flag += [f"top{top}"]

        return data, "_".join(flag)


    with pd.option_context('display.max_rows', None, 'display.max_columns',
                           None):  # more options can be specified also

        data = data.sort_values(MAX_SUITE_SIZE, ascending=False)
        data, flag = filter(data, top=10)
        repos = data[REPO]
        dataset_stats_folder = general_graphs / f"dataset_stats_{flag}"
        os.makedirs(dataset_stats_folder, exist_ok=True)

        visualize_dataset(get_modules_from_db(repos), dataset_stats_folder)

        # draw_fixed_size(data_path, repos, image_file=dataset_stats_folder / "im_size.png")
        # draw_fixed_coverage(data_path, repos, image_file=dataset_stats_folder / "im_coverage.png")
        cov_pairs_du = [
            (CoverageMetric.ALL_PAIRS, CoverageMetric.STATEMENT),
            (CoverageMetric.ALL_PAIRS, CoverageMetric.BRANCH),
        ]
        # mean
        _generic_draw(
            root=graphs_path, repo_ids=repos,
            df_type=DataFrameType.FIXED_COVERAGE,
            cov_pairs=cov_pairs_du,
            mean=True,
            img_folder=dataset_stats_folder,
            small=True
        )
        _generic_draw(
            root=graphs_path, repo_ids=repos,
            df_type=DataFrameType.FIXED_SIZE,
            cov_pairs=cov_pairs_du,
            mean=True,
            img_folder=dataset_stats_folder,
            small=True
        )
        # no mean
        _generic_draw(
            root=graphs_path, repo_ids=repos,
            df_type=DataFrameType.FIXED_SIZE,
            cov_pairs=cov_pairs_du,
            mean=False,
            img_folder=dataset_stats_folder,
            small=True
        )

        _generic_draw(
            root=graphs_path, repo_ids=repos,
            df_type=DataFrameType.FIXED_COVERAGE,
            cov_pairs=cov_pairs_du,
            mean=False,
            img_folder=dataset_stats_folder,
            small=True
        )
        # br cov relative to st cov
        cov_pairs_br = [
            (CoverageMetric.BRANCH, CoverageMetric.STATEMENT),
        ]
        br_rel_to_st_dir = dataset_stats_folder / "br"
        os.makedirs(br_rel_to_st_dir, exist_ok=True)
        _generic_draw(
            root=graphs_path, repo_ids=repos,
            df_type=DataFrameType.FIXED_COVERAGE,
            cov_pairs=cov_pairs_br,
            mean=True,
            img_folder=br_rel_to_st_dir,
            small=True
        )
        _generic_draw(
            root=graphs_path, repo_ids=repos,
            df_type=DataFrameType.FIXED_SIZE,
            cov_pairs=cov_pairs_br,
            mean=True,
            img_folder=br_rel_to_st_dir,
            small=True
        )
        # no mean
        _generic_draw(
            root=graphs_path, repo_ids=repos,
            df_type=DataFrameType.FIXED_COVERAGE,
            cov_pairs=cov_pairs_br,
            mean=False,
            img_folder=br_rel_to_st_dir,
            small=True
        )
        _generic_draw(
            root=graphs_path, repo_ids=repos,
            df_type=DataFrameType.FIXED_SIZE,
            cov_pairs=cov_pairs_br,
            mean=False,
            img_folder=br_rel_to_st_dir,
            small=True
        )
