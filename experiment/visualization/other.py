from pathlib import Path
from typing import List
import matplotlib.pyplot as plt
import pandas as pd

from experiment.dataframe_type import DataFrameType


def all_data_frames_of_type(path: Path, df_type: DataFrameType):
    dfs = []
    for file in path.iterdir():
        if file.is_file() and file.suffix == ".csv" and file.stem.endswith(df_type.value):
            dfs.append(file)
    return dfs


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


def cov_bin_key(a_bin):
    return int(a_bin[1:-1].split("-")[0])


def draw_plots_vertically(fname, sharedx, plots: List[Plot]):
    fig, ax = plt.subplots(len(plots), sharex=True, figsize=(16, 8))
    for plot, ax in zip(plots, ax):
        if plot.ordering:
            order = list(sorted(plot.df[sharedx].unique(), key=plot.ordering))
            plot.plt_type(data=plot.df, x=sharedx, order=order, ax=ax, **plot.kw)
        else:
            plot.plt_type(data=plot.df, x=sharedx, ax=ax, **plot.kw)

    # plt.title(title)
    fig.savefig(fname)
