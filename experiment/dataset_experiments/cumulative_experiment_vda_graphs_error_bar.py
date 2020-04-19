import operator
import os
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects
import pandas as pd
import seaborn as sns
from typing import List

from loguru import logger
from matplotlib.figure import SubplotParams

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
from experiment.visualize_selection.selection_visualization import RC

MIN_ALL_PAIRS_COVERAGE = "Min all pairs coverage"
MAX_ALL_PAIRS_COVERAGE = "Max all pairs coverage"
MIN_BRANCH_COVERAGE = "Min branch coverage"
MAX_BRANCH_COVERAGE = "Max branch coverage"
MIN_STATEMENT_COVERAGE = "Min statement coverage"
MAX_STATEMENT_COVERAGE = "Max statement coverage"
MAX_SUITE_SIZE = "Max suite size"
REPO = "Repo"

SHORT_NAME = {
    CoverageMetric.BRANCH: "branch",
    CoverageMetric.ALL_PAIRS: "du-pairs",
    CoverageMetric.STATEMENT: "statement",
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


def vda_stat(metric_1, metric_2, cols, df, eq_len=True):
    by_metric = df.groupby([METRIC])
    if metric_1.value not in by_metric.groups.keys() \
            or metric_2.value not in by_metric.groups.keys():
        return [None] * len(cols)
    gr1 = by_metric.get_group(metric_1.value)
    gr2 = by_metric.get_group(metric_2.value)
    vdas = []
    for col in cols:
        a = len(gr1[col])
        b = len(gr2[col])
        d = abs(a - b)
        if (a > 1 and b > 1) and (not eq_len or d < a and d < b):
            vda = a12slow(gr1[col], gr2[col])
            vdas.append(vda)
        else:
            vdas.append(None)
    return vdas


def _join(dfs):
    df = pd.concat(dfs, axis=0, ignore_index=True, sort=False)
    df = df.dropna(thresh=2)
    return df


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


def name_columns(cov_pairs, for_presentation=True):
    col_names = []
    for pair in cov_pairs:
        main, relative = map(SHORT_NAME.get, pair)
        if for_presentation:
            col_names.append(f"Bugs")
            col_names.append(f"Muts")
        else:
            col_names.append(f"{main} vs {relative}\nBugs revealing score")
            col_names.append(f"{main} vs {relative}\nMutation score")
    return col_names


def _add_lines(axs, small, medium, large, lim_0_1, auto_lines=False):
    s, m, l = 0.56, 0.64, 0.71

    n_seg = 'no diff.'
    s_seg = 'small'
    m_seg = 'medium'
    l_seg = 'large'
    font_size = 10

    def draw_x_line(y, color, text, ls=":"):
        transparent = (0.0, 0.0, 0.0, 0.0)
        ax.axhline(y, ls=ls, c=color, lw=2)
        txt = ax.text(0, y, text, fontsize=font_size, va='center', ha='left', backgroundcolor=transparent, color=color)
        txt.set_path_effects([PathEffects.withStroke(linewidth=5, foreground='w')])

    for ax in axs:
        bot, top = ax.get_ylim()
        # ax.axhline(0.5, ls='--', c="green", lw=2)
        draw_x_line(0.5, "green", n_seg, ls='--')
        if auto_lines:
            if bot < 1 - s:
                draw_x_line(1 - s, "brown", s_seg)
            if top > s:
                draw_x_line(s, "brown", s_seg)
            if bot < 1 - m:
                draw_x_line(1 - m, "red", m_seg)
            if top > m:
                draw_x_line(m, "red", m_seg)
            if bot < 1 - l:
                draw_x_line(1 - l, "orange", l_seg)
            if top > l:
                draw_x_line(l, "orange", l_seg)
        else:
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


def _draw(x, data, order, ys, plot_type="bps"):
    # hue_order = list(sorted(data[METRIC].unique()))
    fig, axs = plt.subplots(len(ys) + 1,
                            sharex=True,
                            figsize=(16, 9),
                            gridspec_kw={'hspace': 0}
                            )
    for idx, (y, ax) in enumerate(zip(ys, axs)):

        data[y] = data[y].astype(float)
        if "b" in plot_type:
            sns.boxplot(x=x, y=y, data=data, ax=ax, order=order)
        if "p" in plot_type:
            sns.pointplot(x=x, y=y, data=data, ax=ax, order=order, capsize=.2)
        if "s" in plot_type:
            sns.swarmplot(x=x, y=y, data=data, ax=ax, order=order)

        # if not idx == len(axs) - 1:
        #     ax.set_xlabel("")
        #     ax.xaxis.set_major_formatter(plt.NullFormatter())

        # ax.set_yticklabels(ax.get_yticklabels(), rotation=45)
        # plt.yticks(rotation=45)
    # palette="husl",
    p = sns.countplot(x=x, data=data, ax=axs[-1], lw=3, order=order, color=sns.color_palette()[0])

    y_label = "Support"

    p.axes.yaxis.label.set_text(y_label)
    # p.set_yticklabels(p.get_yticklabels(), rotation=45)
    plt.xticks(rotation=45)
    for ax in axs:
        ax.label_outer()
    # plt.tight_layout()

    return fig, axs


def _generic_draw(root, repo_ids, df_type,
                  cov_pairs,
                  img_folder="", image_file="",
                  small=True, medium=False, large=False, lim_0_1=False,
                  auto_lines=False,
                  plot_type="p",
                  for_presentation=True
                  ):
    group_by = SUITE_SIZE if df_type == DataFrameType.FIXED_SIZE else SUITE_COVERAGE_BIN
    dfs = [read_combined_df(root, repo_id, df_type) for repo_id in repo_ids]
    dfs = [_get_vda(df, group_by, cov_pairs=cov_pairs) for df in dfs]
    # with pd.option_context('display.max_rows', None, 'display.max_columns',
    #                        None):  # more options can be specified also
    #     for df in dfs:
    #         print(df)

    vda_df = _join(dfs)
    if df_type == DataFrameType.FIXED_SIZE:
        order = sorted(vda_df[group_by].unique())
    else:
        order = list(sorted(vda_df[group_by].unique(), key=cov_bin_key))
    ys = name_columns(cov_pairs)

    sns.set_context("paper")
    if for_presentation:
        sns.set_context("talk")

    with sns.axes_style(rc=RC if for_presentation else {}):
        fig, axs = _draw(group_by, vda_df, order, ys, plot_type=plot_type)
        _add_lines(axs[:-1], small, medium, large, lim_0_1, auto_lines=auto_lines)

        if not image_file:
            f = ["fixed_size" if df_type == DataFrameType.FIXED_SIZE else "fixed_coverage"]
            f += [_explain_plot(plot_type)]
            f += ["vda"]
            stem = "_".join(f)
            image_file = Path(img_folder) / f"{stem}.png"
        plt.tight_layout()
        plt.savefig(image_file, dpi=300, transparent=for_presentation)
        logger.info("Saved graph to {p}", p=image_file)


def _explain_plot(plot_type):
    types = []
    if "b" in plot_type:
        types.append("boxplot")
    if "p" in plot_type:
        types.append("pointplot")
    if "s" in plot_type:
        types.append("swarmplot")
    return "[" + "|".join(types) + "]"


def get_modules_from_db(repo_ids):
    to_id = lambda s: s[:-41] + "@" + s[-40:]
    repo_ids = [to_id(r) for r in repo_ids]
    print(repo_ids)
    ms: List[Module] = Module.select() \
        .join(Repo) \
        .where(Repo.id << repo_ids)
    return ms


def filter_data(data, min_suite_size=None, top=None, offset=None):
    def add(q):
        if hasattr(filter_data, "query"):
            filter_data.query &= q
        else:
            filter_data.query = q

    if min_suite_size:
        add((data[MAX_SUITE_SIZE] > min_suite_size))

    flag = []

    if hasattr(filter_data, "query"):
        data = data[filter_data.query]
        flag += [str(len(filter_data.query))]
    else:
        flag += ["all"]

    if offset:
        data = data[offset:]
        flag += [f"offset{offset}"]

    if top:
        data = data[:top]
        flag += [f"top{top}"]

    return data, "_".join(flag)


if __name__ == "__main__":
    plot_types = ["p"]
    use_fixed_version = True
    flag = "main"
    flag += "fixed" if use_fixed_version else "buggy"
    dataset_path = results_root / f"dataset_cumulative_off_{flag}"
    graphs_path = results_root / f"graphs_cumulative_off_{flag}"
    general_graphs = graphs_path / "graphs_vda_error_bar"

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
    ms: List[Module] = Module.select() \
        .where(Module.st_cov > 70) \
        .where(Module.du_cov > 70) \
        .where(Module.br_cov > 70) \
        .where(Module.bugs < 8) \
        .where(Module.statements > 50) \
        .where(Module.total_cases > 20) \
        .where(Module.total_cases < 1000) \
        .where(Module.is_full_cfg == 1) \
        .group_by(Module.path) \
        .order_by(Module.total_cases.desc()) \
        # .limit(10)
    print(len(list(ms)))
    # exit()
    print("\n".join(list(
        map(lambda t: " ".join(t),
            zip(
                map(str, map(operator.attrgetter("path"), ms)),
                map(str, map(operator.attrgetter("path"), ms)),
                map(str, map(operator.attrgetter("total_cases"), ms)),
                map(str, map(operator.attrgetter("statements"), ms))
            )
            )
    )))
    # exit()

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
        else:
            logger.warning("No experiment data for project {p} {n}", p=m.id, n=m.repo)

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

    with pd.option_context('display.max_rows', None, 'display.max_columns',
                           None):  # more options can be specified also

        data = data.sort_values(MAX_SUITE_SIZE, ascending=False)
        # data, flag = filter_data(data, top=10, offset=0)
        data, flag = filter_data(data, offset=0)

        repos = data[REPO]
        dataset_stats_folder = general_graphs / f"dataset_stats_{flag}"
        os.makedirs(dataset_stats_folder, exist_ok=True)
        visualize_dataset(get_modules_from_db(repos), dataset_stats_folder)

        comparisons = (
            (CoverageMetric.ALL_PAIRS, CoverageMetric.STATEMENT),
            (CoverageMetric.ALL_PAIRS, CoverageMetric.BRANCH),
            (CoverageMetric.BRANCH, CoverageMetric.STATEMENT),
        )


        def folder_name(comparison):
            return "_vs_".join(map(lambda m: "_".join(str(m).lower().split()), comparison))


        for comparison in comparisons:
            comparison_dir = dataset_stats_folder / folder_name(comparison)
            os.makedirs(comparison_dir, exist_ok=True)

            for plot_type in plot_types:
                _generic_draw(
                    root=graphs_path, repo_ids=repos,
                    df_type=DataFrameType.FIXED_SIZE,
                    cov_pairs=[comparison],
                    img_folder=comparison_dir,
                    small=True,
                    plot_type=plot_type,
                    auto_lines=True
                )
                _generic_draw(
                    root=graphs_path, repo_ids=repos,
                    df_type=DataFrameType.FIXED_COVERAGE,
                    cov_pairs=[comparison],
                    img_folder=comparison_dir,
                    small=True,
                    plot_type=plot_type,
                    auto_lines=True
                )
                # br cov relative to st cov

            # br_rel_to_st_dir = dataset_stats_folder / "branch_vs_statement"
            # os.makedirs(br_rel_to_st_dir, exist_ok=True)
            # _generic_draw(
            #     root=graphs_path, repo_ids=repos,
            #     df_type=DataFrameType.FIXED_COVERAGE,
            #     cov_pairs=br_vs_st,
            #     img_folder=br_rel_to_st_dir,
            #     small=True,
            #     plot_type=plot_type,
            #     auto_lines=False
            # )
            # _generic_draw(
            #     root=graphs_path, repo_ids=repos,
            #     df_type=DataFrameType.FIXED_SIZE,
            #     cov_pairs=br_vs_st,
            #     img_folder=br_rel_to_st_dir,
            #     small=True,
            #     plot_type=plot_type,
            #     auto_lines=False
            # )
            #
            # file = '/home/robert/Documents/master/code/1experiments_results/graphs_cumulative_off_mainfixed/tinydb_b412d8d76c5da87d9d951b1e371bd820a1d2d7c2@tinydb::database.py::FIXED_SIZE.csv'
            # import pandas as pd
            # from combined_experiment_cli import *
            #
            # df = pd.read_csv(file, index_col=0)
            # df["Mutants\nkilled"] *= 100
            # df["Bugs\nrevealed"] *= 100
            # draw_vertically(df, SUITE_SIZE, "tinydb.png")
