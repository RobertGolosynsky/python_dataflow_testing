import pandas as pd
from combined_experiment_cli import DataFrameType

import seaborn as sns
from experiment.core.mutation_experiment import METRIC, SUITE_SIZE, SUITE_COVERAGE, SUITE_COVERAGE_BIN, MUTATION_SCORE
from experiment.core.real_bugs_experiment import METRIC, SUITE_SIZE, SUITE_COVERAGE, SUITE_COVERAGE_BIN, \
    BUG_REVEALED_SCORE
from experiment.folders import results_root
from experiment.visualization.other import read_data_frames_of_type, Plot, draw_plots_vertically, cov_bin_key

if __name__ == "__main__":
    df_root = results_root / "graphs_cumulative_off_{}_lim_{}".format(0, 20)

    # size
    all_m_size = read_data_frames_of_type(df_root, DataFrameType.MUTATION_FIXED_SIZE)
    all_b_size = read_data_frames_of_type(df_root, DataFrameType.BUGS_FIXED_SIZE)

    df_all = [df.groupby([SUITE_SIZE, METRIC], as_index=False).mean() for df in all_b_size + all_m_size]
    df_all = pd.concat(df_all, axis=0, ignore_index=True, sort=False)

    all_m_size = [df.groupby([SUITE_SIZE, METRIC]).mean() for df in all_m_size]

    count_plot = Plot(df=df_all, plt_type=sns.countplot, ordering=None, hue=METRIC, palette="husl", dodge=True)
    mutation_plot = Plot(df=df_all, plt_type=sns.pointplot, ordering=None, y=MUTATION_SCORE, hue=METRIC, palette="husl",
                         capsize=.2, kind="point", dodge=True)
    bugs_plot = Plot(df=df_all, plt_type=sns.pointplot, ordering=None, y=BUG_REVEALED_SCORE, hue=METRIC, palette="husl",
                     capsize=.2, kind="point", dodge=True)
    size_plot = Plot(df=df_all, plt_type=sns.pointplot, ordering=None, y=SUITE_COVERAGE, hue=METRIC, palette="husl",
                     capsize=.2, kind="point", dodge=True)
    plots = [
        bugs_plot,
        mutation_plot,
        size_plot,
        count_plot
    ]
    draw_plots_vertically("main_plot_size_grouped.png", sharedx=SUITE_SIZE, plots=plots)

    # coverage
    all_m_cov = read_data_frames_of_type(df_root, DataFrameType.MUTATION_FIXED_COVERAGE)
    all_b_cov = read_data_frames_of_type(df_root, DataFrameType.BUGS_FIXED_COVERAGE)
    df_all = [df.groupby([SUITE_COVERAGE_BIN, METRIC], as_index=False).mean() for df in all_m_cov + all_b_cov]
    df_all = pd.concat(df_all, axis=0, ignore_index=True, sort=False)

    count_plot = Plot(df=df_all, plt_type=sns.countplot, ordering=cov_bin_key, hue=METRIC, palette="husl", dodge=True)
    mutation_plot = Plot(df=df_all, plt_type=sns.pointplot, ordering=cov_bin_key, y=MUTATION_SCORE, hue=METRIC,
                         palette="husl",
                         capsize=.2, kind="point", dodge=True)
    bugs_plot = Plot(df=df_all, plt_type=sns.pointplot, ordering=cov_bin_key, y=BUG_REVEALED_SCORE, hue=METRIC,
                     palette="husl",
                     capsize=.2, kind="point", dodge=True)
    size_plot = Plot(df=df_all, plt_type=sns.pointplot, ordering=cov_bin_key, y=SUITE_SIZE, hue=METRIC, palette="husl",
                     capsize=.2, kind="point", dodge=True)
    plots = [
        bugs_plot,
        mutation_plot,
        size_plot,
        count_plot
    ]
    draw_plots_vertically("main_plot_cov_grouped.png", sharedx=SUITE_COVERAGE_BIN, plots=plots)
