from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from experiment.cummulative_experiment import graphs_path
from combined_experiment_cli import DataFrameType
import matplotlib.pyplot as plt
import seaborn as sns
from experiment.core.mutation_experiment import METRIC, SUITE_SIZE, SUITE_COVERAGE, SUITE_COVERAGE_BIN, MUTATION_SCORE
from experiment.core.real_bugs_experiment import METRIC, SUITE_SIZE, SUITE_COVERAGE, SUITE_COVERAGE_BIN, \
    BUG_REVEALED_SCORE


def all_data_frames_of_type(df_type: DataFrameType):
    dfs = []
    for file in res_path.iterdir():
        if file.is_file() and file.suffix == ".csv" and file.stem.endswith(df_type.value):
            dfs.append(file)
    return dfs


def load_data_frames(list_files):
    dfs = []
    for file in list_files:
        df = pd.read_csv(filepath_or_buffer=file, index_col=0)
        dfs.append(df)
    return dfs


def read_data_frames_of_type(df_type: DataFrameType):
    return load_data_frames(all_data_frames_of_type(df_type))


class Plot:
    def __init__(self, df, plt_type, ordering, **kw):
        self.df = df
        self.plt_type = plt_type
        self.kw = kw
        self.ordering = ordering


def key(a_bin):
    return int(a_bin[1:-1].split("-")[0])


def draw(fname, sharedx, plots: List[Plot]):
    fig, ax = plt.subplots(len(plots), sharex=True, figsize=(16, 8))
    # if not isinstance(ax, tuple):
    #     ax = (ax, )
    for plot, ax in zip(plots, ax):
        if plot.ordering:
            order = list(sorted(plot.df[sharedx].unique(), key=plot.ordering))
            plot.plt_type(data=plot.df, x=sharedx, order=order, ax=ax, **plot.kw)
        else:
            plot.plt_type(data=plot.df, x=sharedx, ax=ax, **plot.kw)



    # plt.title(title)
    fig.savefig(fname)
    # plt.show()
    # plt.close()


if __name__ == "__main__":
    res_path = Path(graphs_path)
    # print(all_data_frames_of_type(DataFrameType.MUTATION_FIXED_SIZE))

    all_m_size = read_data_frames_of_type(DataFrameType.MUTATION_FIXED_SIZE)
    print(len(all_m_size))
    all_b_size = read_data_frames_of_type(DataFrameType.BUGS_FIXED_SIZE)
    print(len(all_b_size))
    # one_f_size = pd.concat(all_f_size, axis=0, ignore_index=True)
    # one_f_cov = pd.concat(all_f_cov, axis=0, ignore_index=True)
    df_all = pd.concat(all_b_size + all_m_size, axis=0, ignore_index=True)
    print(df_all)

    count_plot = Plot(df=df_all, plt_type=sns.countplot, ordering=None, hue=METRIC, palette="husl", dodge=True)
    mutation_plot = Plot(df=df_all, plt_type=sns.pointplot, ordering=None, y=MUTATION_SCORE, hue=METRIC, palette="husl",
                         capsize=.2, kind="point", dodge=True)
    bugs_plot = Plot(df=df_all, plt_type=sns.pointplot, ordering=None, y=BUG_REVEALED_SCORE, hue=METRIC, palette="husl",
                     capsize=.2, kind="point", dodge=True)
    size_plot = Plot(df=df_all, plt_type=sns.pointplot, ordering=None, y=SUITE_COVERAGE, hue=METRIC, palette="husl",
                         capsize=.2, kind="point", dodge=True)
    plots = [count_plot, mutation_plot,
             bugs_plot,
             size_plot]
    draw("main_plot_size.png", sharedx=SUITE_SIZE, plots=plots)

    # coverage
    all_m_cov = read_data_frames_of_type(DataFrameType.MUTATION_FIXED_COVERAGE)
    print(len(all_m_cov))
    all_b_cov = read_data_frames_of_type(DataFrameType.BUGS_FIXED_COVERAGE)
    print(len(all_b_cov))
    df_all = pd.concat(all_m_cov + all_b_cov, axis=0, ignore_index=True)
    df_all = df_all[pd.notnull(df_all[SUITE_COVERAGE_BIN])]
    print(df_all.keys())

    count_plot = Plot(df=df_all, plt_type=sns.countplot, ordering=key, hue=METRIC, palette="husl", dodge=True)
    mutation_plot = Plot(df=df_all, plt_type=sns.pointplot, ordering=key, y=MUTATION_SCORE, hue=METRIC, palette="husl",
                         capsize=.2, kind="point", dodge=True)
    bugs_plot = Plot(df=df_all, plt_type=sns.pointplot, ordering=key, y=BUG_REVEALED_SCORE, hue=METRIC, palette="husl",
                     capsize=.2, kind="point", dodge=True)
    size_plot = Plot(df=df_all, plt_type=sns.pointplot, ordering=key, y=SUITE_SIZE, hue=METRIC, palette="husl",
                     capsize=.2, kind="point", dodge=True)
    plots = [
        count_plot,
        mutation_plot,
        bugs_plot,
        size_plot
    ]
    draw("main_plot_cov.png", sharedx=SUITE_COVERAGE_BIN, plots=plots)
