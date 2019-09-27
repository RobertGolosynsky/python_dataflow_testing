from pathlib import Path
from typing import List

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from experiment.core.columns import METRIC, MUTATION_SCORE, BUG_REVEALED_SCORE, SUITE_COVERAGE, SUITE_COVERAGE_BIN, \
    DataFrameType, SUITE_SIZE


def all_data_frames_of_type(path: Path, df_type: DataFrameType):
    dfs = []
    for file in path.iterdir():
        if file.is_file() and file.suffix == ".csv" and file.stem.endswith(df_type.value):
            dfs.append(file)
    return dfs


def cov_bin_key(a_bin):
    return int(a_bin[1:-1].split("-")[0])


def draw_vertically(df, sharedx, image_file, dodge=0.5, title=None):
    ordering = None
    if sharedx == SUITE_COVERAGE_BIN:
        ordering = cov_bin_key

    count_plot = Plot(df=df, plt_type=sns.countplot, ordering=ordering, palette="husl", dodge=dodge)
    mutation_plot = Plot(df=df, plt_type=sns.pointplot, ordering=ordering, y=MUTATION_SCORE, palette="husl",
                         capsize=.2, kind="point", dodge=dodge)
    bugs_plot = Plot(df=df, plt_type=sns.pointplot, ordering=ordering, y=BUG_REVEALED_SCORE, palette="husl",
                     capsize=.2, kind="point", dodge=dodge)
    if sharedx == SUITE_COVERAGE_BIN:
        size_plot = Plot(df=df, plt_type=sns.pointplot, ordering=ordering, y=SUITE_SIZE, palette="husl",
                         capsize=.2, kind="point", dodge=dodge)
    else:
        size_plot = Plot(df=df, plt_type=sns.pointplot, ordering=ordering, y=SUITE_COVERAGE, palette="husl",
                         capsize=.2, kind="point", dodge=dodge)
    plots = [
        bugs_plot,
        mutation_plot,
        size_plot,
        count_plot
    ]
    draw_plots_vertically(image_file, sharedx=sharedx, hue=METRIC, plots=plots, title=title)


def load_data_frames(list_files):
    dfs = []
    for file in list_files:
        df = pd.read_csv(filepath_or_buffer=file, index_col=0)
        dfs.append(df)
    return dfs


def read_data_frames_of_type(path: Path, df_type: DataFrameType):
    return load_data_frames(all_data_frames_of_type(path, df_type))


class Plot:
    def __init__(self, df, plt_type, ordering, **kw):
        self.df = df
        self.plt_type = plt_type
        self.kw = kw
        self.ordering = ordering


def draw_plots_vertically(fname, sharedx, hue, plots: List[Plot], title=None):
    fig, ax = plt.subplots(len(plots), sharex=True, figsize=(16, 8))
    for plot, ax in zip(plots, ax):
        hue_order = list(sorted(plot.df[hue].unique()))
        if plot.ordering:
            order = list(sorted(plot.df[sharedx].unique(), key=plot.ordering))
            plot.plt_type(data=plot.df, x=sharedx, order=order, hue=hue, hue_order=hue_order, ax=ax, **plot.kw)
        else:
            plot.plt_type(data=plot.df, x=sharedx, hue=hue, hue_order=hue_order, ax=ax, **plot.kw)
    if title:
        fig.suptitle(title)
    fig.savefig(fname)


def normalize(df):
    return (df - df.min()) / (df.max() - df.min())


def normalize_columns(df, columns):
    for column in columns:
        df[column] = normalize(df[column])
    return df
