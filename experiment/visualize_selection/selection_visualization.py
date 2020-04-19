from typing import List
import matplotlib.pyplot as plt
import seaborn as sns
from playhouse.sqlite_ext import SqliteExtDatabase
import pandas as pd
from experiment.db_model.repo import DATABASE_PROXY, Module, Repo
from experiment.repo_selection import STATUS_NO_REVEALING_NODE_IDS, STATUS_DYNAMIC_NODE_IDS, STATUS_GOOD, \
    STATUS_NO_MODULE_CFG, \
    STATUS_NO_FAILED_ON_ASSERTION, STATUS_BAD
import numpy as np

rename_repo_status = {
    STATUS_GOOD: "OK",
    STATUS_BAD: "Failed to fetch",
    STATUS_NO_REVEALING_NODE_IDS: "No test cases failed",
    STATUS_NO_FAILED_ON_ASSERTION: "No test cases failed on assertion",
    STATUS_DYNAMIC_NODE_IDS: "Dynamic test case names",
    STATUS_NO_MODULE_CFG: "Failed to create module CFG"
}
HUMAN_READABLE_LABELS = {
    'm_pairs': "Intra-method pairs",
    'im_pairs': "Inter-method pairs",
    'ic_pairs': "Inter-class pairs",
    "all_pairs": "All pairs",
    'statements': "Statements",
    'branches': "Branches",
    'mutants': "Mutants",
    'bugs': "Bugs",
    'total_cases': "Test cases",
    'st_cov': "Statement coverage",
    'br_cov': "Branch coverage",
    'du_cov': "All pairs coverage",
    'time': "Testing time"
}
STATUS_ORDER = [STATUS_GOOD, STATUS_BAD, STATUS_NO_REVEALING_NODE_IDS, STATUS_DYNAMIC_NODE_IDS,
                STATUS_NO_FAILED_ON_ASSERTION, STATUS_NO_MODULE_CFG]
STATUS_ORDER = map(rename_repo_status.get, STATUS_ORDER)

c = "1.0"
RC = {'axes.edgecolor': c,
      'axes.labelcolor': c,
      'figure.facecolor': c,
      'text.color': c,
      'xtick.color': c,
      'ytick.color': c,
      "boxplot.flierprops.color": c,
      'boxplot.flierprops.markeredgecolor': c}


def draw_repos_status(pie=False):
    x_label = "Repositories"
    status_field = "status"
    display_status_name = "Repository status"

    repos: List[Repo] = Repo.select()

    df = pd.DataFrame(list(repos.dicts()))

    df[status_field] = df[status_field].apply(lambda st: rename_repo_status[st])
    df.rename(columns={status_field: display_status_name}, inplace=True)
    total = len(df)
    color = sns.color_palette()[0]
    f, ax = plt.subplots(figsize=(8, 3))
    if not pie:
        sns.countplot(y=display_status_name, data=df, order=STATUS_ORDER, color=color)
        ax.set(xlabel=x_label)
    else:
        # labels = df[display_status_name]
        print(df.keys())
        sizes = df[display_status_name].value_counts()
        labels, vals = list(zip(*dict(sizes).items()))
        ok_idx = labels.index("OK")
        explode = [0.0] * len(labels)  # only "explode" the 2nd slice (i.e. 'Hogs')
        explode[ok_idx] = 0.1
        fig1, ax1 = plt.subplots()
        # explode=explode, labels=labels, autopct='%1.1f%%',
        #                 shadow=False, startangle=0
        wedges, texts = ax1.pie(vals, wedgeprops=dict(width=0.5))

        bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
        kw = dict(arrowprops=dict(arrowstyle="-"),
                  bbox=bbox_props, zorder=0, va="center")

        for i, p in enumerate(wedges):
            print("asd", i)
            ang = (p.theta2 - p.theta1) / 2. + p.theta1
            y = np.sin(np.deg2rad(ang))
            x = np.cos(np.deg2rad(ang))
            horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
            connectionstyle = "angle,angleA=0,angleB={}".format(ang)
            kw["arrowprops"].update({"connectionstyle": connectionstyle})
            ax.annotate(labels[i], xy=(x, y), xytext=(1.35 * np.sign(x), 1.4 * y),
                        horizontalalignment=horizontalalignment, **kw)

        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        plt.show()
    # plt.title(f"Repositories by evaluation outcome (total: {total})")
    # plt.tight_layout()
    plt.savefig("selected_repos_count_by_status.png", dpi=300, transparent=transparent_bg)


def draw_count_test_cases():
    ms: List[Module] = Module.select() \
        .join(Repo) \
        .group_by(Repo.name) \
        .order_by(Module.total_cases.desc())
    df = pd.DataFrame(list(ms.dicts()))

    f, ax = plt.subplots(figsize=(10, 5))

    bin_column_name = "bin_tc"
    column_to_bin = "total_cases"
    bins = [1, 2, 6, 10, 20, 50, 100, 2000]
    bin_labels = [f"[{l}-{r}]" for l, r in zip(bins[:-1], bins[1:])]
    kw = {bin_column_name: lambda x: pd.cut(x[column_to_bin], bins=bins, labels=bin_labels)}

    df: pd.DataFrame = df.assign(**kw)
    color = sns.color_palette()[0]
    sns.countplot(data=df, x=bin_column_name, color=color)
    x_label = "Suite size"
    y_label = "Repositories count"
    ax.set(xlabel=x_label, ylabel=y_label)
    total = len(df)
    # plt.title(f"Repositories by test suite size (total: {total})")
    plt.tight_layout()
    plt.savefig("good_repos_by_suite_size_bin.png", dpi=300, transparent=transparent_bg)


def draw_coverage_goals():
    ms: List[Module] = Module.select() \
        .join(Repo) \
        .group_by(Repo.name) \
        .order_by(Module.total_cases.desc())
    df = pd.DataFrame(list(ms.dicts()))

    humanize = lambda l: HUMAN_READABLE_LABELS[l]

    df["all_pairs"] = df[["m_pairs", "im_pairs", "ic_pairs"]].sum(axis=1)

    for col, readable_col in HUMAN_READABLE_LABELS.items():
        df[readable_col] = df[col]
        df[col] = None

    coverage_goals_cols = ["statements", "branches", "all_pairs"]
    pairs_cols = ["m_pairs", "im_pairs", "ic_pairs"]

    coverage_goals_cols = list(map(humanize, coverage_goals_cols))

    # coverage goals
    f, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(data=df.loc[:, coverage_goals_cols])
    if for_presentation:
        make_box_plot_white(ax)

    x_label = "Goal types"
    y_label = "Goals count"
    ax.set(xlabel=x_label, ylabel=y_label)
    plt.tight_layout()
    plt.savefig("coverage_goals_all_unique.png", dpi=300, transparent=transparent_bg)

    # pair detailed
    pairs_cols = list(map(humanize, pairs_cols))
    f, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(data=df.loc[:, pairs_cols])
    if for_presentation:
        make_box_plot_white(ax)

    x_label = "Definition-use pair types"
    y_label = "Pairs count"
    ax.set(xlabel=x_label, ylabel=y_label)
    plt.tight_layout()
    plt.savefig("pairs_detailed_all_unique.png", dpi=300, transparent=transparent_bg)


def make_box_plot_white(ax):
    for i, artist in enumerate(ax.artists):
        # Set the linecolor on the artist to the facecolor, and set the facecolor to None
        col = '1.0'
        artist.set_edgecolor(col)
        # artist.set_facecolor('None')

        # Each box has 6 associated Line2D objects (to make the whiskers, fliers, etc.)
        # Loop over them here, and use the same colour as above
        for j in range(i * 6, i * 6 + 6):
            line = ax.lines[j]
            line.set_color(col)
            line.set_mfc(col)
            line.set_mec(col)


if __name__ == "__main__":

    for_presentation = True

    sns.set_context("paper")
    transparent_bg = False

    if for_presentation:
        transparent_bg = True
        sns.set_context("talk")

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

    with sns.axes_style(rc=RC if for_presentation else {}):
        draw_repos_status()
        draw_count_test_cases()
        draw_coverage_goals()
