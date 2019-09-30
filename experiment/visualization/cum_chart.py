import pandas as pd
from experiment.core.columns import SUITE_SIZE, SUITE_COVERAGE_BIN, METRIC, MUTATION_SCORE, BUG_REVEALED_SCORE, \
    DataFrameType
from experiment.folders import results_root
from experiment.visualization.other import draw_vertically, read_data_frames_of_type, normalize_columns


def draw_biased(df_root, out_folder):
    # size
    size_dfs = read_data_frames_of_type(df_root, DataFrameType.FIXED_SIZE)
    size_dfs = pd.concat(size_dfs, axis=0, ignore_index=True, sort=False)
    image_file = out_folder / "fixed_size.png"
    draw_vertically(size_dfs, SUITE_SIZE, image_file)

    # coverage
    coverage_dfs = read_data_frames_of_type(df_root, DataFrameType.FIXED_COVERAGE)
    coverage_dfs = pd.concat(coverage_dfs, axis=0, ignore_index=True, sort=False)
    coverage_dfs = coverage_dfs[pd.notnull(coverage_dfs[SUITE_COVERAGE_BIN])]
    image_file = out_folder / "fixed_coverage.png"
    draw_vertically(coverage_dfs, SUITE_COVERAGE_BIN, image_file)


def draw_grouped(df_root, out_folder):
    # size
    size_dfs = read_data_frames_of_type(df_root, DataFrameType.FIXED_SIZE)
    size_dfs = [df.groupby([SUITE_SIZE, METRIC], as_index=False).mean() for df in size_dfs]
    size_dfs = pd.concat(size_dfs, axis=0, ignore_index=True, sort=False)

    image_file = out_folder / "fixed_size_grouped.png"
    draw_vertically(size_dfs, SUITE_SIZE, image_file)

    # coverage
    coverage_dfs = read_data_frames_of_type(df_root, DataFrameType.FIXED_COVERAGE)

    coverage_dfs = [df.groupby([SUITE_COVERAGE_BIN, METRIC], as_index=False).mean() for df in coverage_dfs]
    coverage_dfs = pd.concat(coverage_dfs, axis=0, ignore_index=True, sort=False)

    image_file = out_folder / "fixed_coverage_grouped.png"
    draw_vertically(coverage_dfs, SUITE_COVERAGE_BIN, image_file)


def draw_grouped_normalized(df_root, out_folder):
    # size
    size_dfs = read_data_frames_of_type(df_root, DataFrameType.FIXED_SIZE)
    size_dfs = [normalize_columns(df, [MUTATION_SCORE, BUG_REVEALED_SCORE]) for df in size_dfs]

    df_all = [df.groupby([SUITE_SIZE, METRIC], as_index=False).mean() for df in size_dfs]
    df_all = pd.concat(df_all, axis=0, ignore_index=True, sort=False)

    image_file = out_folder / "fixed_size_grouped_normalized.png"
    draw_vertically(df_all, SUITE_SIZE, image_file)

    # coverage
    coverage_dfs = read_data_frames_of_type(df_root, DataFrameType.FIXED_COVERAGE)

    coverage_dfs = [normalize_columns(df, [MUTATION_SCORE, BUG_REVEALED_SCORE]) for df in coverage_dfs]

    df_all = [df.groupby([SUITE_COVERAGE_BIN, METRIC], as_index=False).mean() for df in coverage_dfs]
    df_all = pd.concat(df_all, axis=0, ignore_index=True, sort=False)

    image_file = out_folder / "fixed_coverage_grouped_normalized.png"
    draw_vertically(df_all, SUITE_COVERAGE_BIN, image_file)


if __name__ == "__main__":
    graphs_path = results_root / "graphs_cumulative_off_{}_lim_{}".format(0, 10)
    general_graphs = graphs_path / "graphs"
    draw_grouped_normalized(graphs_path, general_graphs)
