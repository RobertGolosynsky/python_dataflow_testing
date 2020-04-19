from pathlib import Path
from typing import List

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
import matplotlib.ticker as mtick

from experiment.core.columns import METRIC, MUTATION_SCORE, BUG_REVEALED_SCORE, SUITE_COVERAGE, SUITE_COVERAGE_BIN, \
    DataFrameType, SUITE_SIZE
from experiment.visualize_selection.selection_visualization import RC


def all_data_frames_of_type(path: Path, df_type: DataFrameType):
    dfs = []
    for file in path.iterdir():
        if file.is_file() and file.suffix == ".csv" and file.stem.endswith(df_type.value):
            dfs.append(file)
    return dfs


def read_combined_df(root: Path, repo_id: str, df_type: DataFrameType):
    for file in root.iterdir():
        if file.is_file() \
                and file.suffix == ".csv" \
                and file.stem.endswith(df_type.value) \
                and repo_id in file.name:
            return load_combined_data_df(file)
    return None


def cov_bin_key(a_bin):
    return int(a_bin[1:-1].split("-")[0])


def draw_vertically(df, sharedx, image_file, dodge=0.5, title=None, for_presentation=False):
    ordering = None
    if sharedx == SUITE_COVERAGE_BIN:
        ordering = cov_bin_key

    count_plot = Plot(df=df, plt_type=sns.countplot, ordering=ordering, palette="husl", dodge=dodge)
    mutation_plot = Plot(df=df, plt_type=sns.pointplot, ordering=ordering, y=MUTATION_SCORE, palette="husl",
                         capsize=.2, kind="point", dodge=dodge, y_formatter=mtick.PercentFormatter())
    bugs_plot = Plot(df=df, plt_type=sns.pointplot, ordering=ordering, y=BUG_REVEALED_SCORE, palette="husl",
                     capsize=.2, kind="point", dodge=dodge, y_formatter=mtick.PercentFormatter())
    if sharedx == SUITE_COVERAGE_BIN:
        size_plot = Plot(df=df, plt_type=sns.pointplot, ordering=ordering, y=SUITE_SIZE, palette="husl",
                         capsize=.2, kind="point", dodge=dodge)
    else:
        size_plot = Plot(df=df, plt_type=sns.pointplot, ordering=ordering, y=SUITE_COVERAGE, palette="husl",
                         capsize=.2, kind="point", dodge=dodge, y_formatter=mtick.PercentFormatter())
    plots = [
        bugs_plot,
        mutation_plot,
        size_plot,
        count_plot
    ]
    draw_plots_vertically(image_file, sharedx=sharedx, hue=METRIC, plots=plots, title=title,
                          for_presentation=for_presentation)


def load_combined_data_df(path: Path):
    return pd.read_csv(filepath_or_buffer=path, index_col=0)


def load_data_frames(list_files):
    dfs = []
    for file in list_files:
        df = load_combined_data_df(file)
        dfs.append(df)
    return dfs


def read_data_frames_of_type(path: Path, df_type: DataFrameType):
    return load_data_frames(all_data_frames_of_type(path, df_type))


class Plot:
    def __init__(self, df, plt_type, ordering, y_formatter=None, **kw):
        self.df = df
        self.plt_type = plt_type
        self.kw = kw
        self.ordering = ordering
        self.y_formatter = y_formatter


def draw_plots_vertically(fname, sharedx, hue, plots: List[Plot], title=None, for_presentation=False):
    sns.set_context("paper")
    if for_presentation:
        sns.set_context("talk")
    with sns.axes_style(rc=RC if for_presentation else {}):

        fig, axs = plt.subplots(len(plots), sharex=True, figsize=(18, 9), gridspec_kw={'hspace': 0})

        for idx, (plot, ax) in enumerate(zip(plots, axs)):
            hue_order = list(sorted(plot.df[hue].unique()))
            if plot.ordering:
                order = list(sorted(plot.df[sharedx].unique(), key=plot.ordering))
                plot.plt_type(data=plot.df, x=sharedx, order=order, hue=hue, hue_order=hue_order, ax=ax, **plot.kw)
            else:
                plot.plt_type(data=plot.df, x=sharedx, hue=hue, hue_order=hue_order, ax=ax, **plot.kw)
            if plot.plt_type == sns.countplot:
                plt.ylabel("Support")
            if plot.y_formatter:
                ax.yaxis.set_major_formatter(plot.y_formatter)
            ax.get_legend().remove()

        handles, labels = ax.get_legend_handles_labels()
        leg = fig.legend(handles, labels, loc='upper center', ncol=len(labels))
        if for_presentation:
            for h, t in zip(leg.legendHandles, leg.get_texts()):
                t.set_color('0.0')

        if title:
            fig.suptitle(title)
        plt.xticks(rotation=45)
        for a in axs:
            a.label_outer()
        plt.tight_layout()
        fig.savefig(fname, dpi=600, transparent=for_presentation)
        plt.close(fig)


def normalize(df):
    return (df - df.min()) / (df.max() - df.min())


def normalize_columns(df, columns):
    for column in columns:
        df[column] = normalize(df[column])
    return df
