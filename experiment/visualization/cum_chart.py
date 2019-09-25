import pandas as pd
from experiment.cummulative_experiment import results_root
from combined_experiment_cli import DataFrameType
import seaborn as sns
from experiment.core.mutation_experiment import METRIC, SUITE_SIZE, SUITE_COVERAGE, SUITE_COVERAGE_BIN, MUTATION_SCORE
from experiment.core.real_bugs_experiment import METRIC, SUITE_SIZE, SUITE_COVERAGE, SUITE_COVERAGE_BIN, \
    BUG_REVEALED_SCORE
from experiment.visualization.other import read_data_frames_of_type, Plot, draw_plots_vertically, cov_bin_key

if __name__ == "__main__":
    df_root = results_root / "graphs_cumulative_off_{}_lim_{}".format(0, 20)

    # size
    all_m_size = read_data_frames_of_type(df_root, DataFrameType.MUTATION_FIXED_SIZE)
    all_b_size = read_data_frames_of_type(df_root, DataFrameType.BUGS_FIXED_SIZE)
    df_all = pd.concat(all_b_size + all_m_size, axis=0, ignore_index=True, sort=False)

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
    draw_plots_vertically("main_plot_size.png", sharedx=SUITE_SIZE, plots=plots)

    # coverage
    all_m_cov = read_data_frames_of_type(df_root, DataFrameType.MUTATION_FIXED_COVERAGE)
    all_b_cov = read_data_frames_of_type(df_root, DataFrameType.BUGS_FIXED_COVERAGE)
    df_all = pd.concat(all_m_cov + all_b_cov, axis=0, ignore_index=True, sort=False)
    df_all = df_all[pd.notnull(df_all[SUITE_COVERAGE_BIN])]

    count_plot = Plot(df=df_all, plt_type=sns.countplot, ordering=cov_bin_key, hue=METRIC, palette="husl", dodge=True)
    mutation_plot = Plot(df=df_all, plt_type=sns.pointplot, ordering=cov_bin_key, y=MUTATION_SCORE, hue=METRIC, palette="husl",
                         capsize=.2, kind="point", dodge=True)
    bugs_plot = Plot(df=df_all, plt_type=sns.pointplot, ordering=cov_bin_key, y=BUG_REVEALED_SCORE, hue=METRIC, palette="husl",
                     capsize=.2, kind="point", dodge=True)
    size_plot = Plot(df=df_all, plt_type=sns.pointplot, ordering=cov_bin_key, y=SUITE_SIZE, hue=METRIC, palette="husl",
                     capsize=.2, kind="point", dodge=True)
    plots = [
        bugs_plot,
        mutation_plot,
        size_plot,
        count_plot
    ]
    draw_plots_vertically("main_plot_cov.png", sharedx=SUITE_COVERAGE_BIN, plots=plots)
