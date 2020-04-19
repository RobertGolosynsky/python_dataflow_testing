import os
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.ticker as mtick

from experiment.visualize_selection.selection_visualization import RC, make_box_plot_white


def visualize_dataset(ms, plots_location, for_presentation=True):
    data = []
    for m in ms:
        data.append(
            (m.statements, m.branches, m.m_pairs, m.im_pairs, m.ic_pairs,
             m.mutants, m.bugs,
             m.st_cov, m.br_cov, m.du_cov)
        )

    df = pd.DataFrame(data=data,
                      columns=["Statements", "Branches",
                               "Intramethod pairs", "Intermethod pairs", "Interclass pairs",
                               "Mutants", "Bugs", "Statement", "Branch", "Pairs"])

    df["All pairs"] = df["Intramethod pairs"] + df["Intermethod pairs"] + df["Interclass pairs"]
    # plot_type = sns.violinplot
    plot_type = sns.boxplot

    sns.set_context("paper")
    if for_presentation:
        sns.set_context("talk")

    with sns.axes_style(rc=RC if for_presentation else {}):
        fig, ax = plt.subplots(1, 1, figsize=(10, 5))
        plot_type(data=df.loc[:, ["Statements", "Branches", "All pairs"]], palette="husl", ax=ax)
        ax.set(ylabel="Number of goals")
        if for_presentation:
            make_box_plot_white(ax)
        plt.savefig(os.path.join(plots_location, "goals_available.png"), dpi=300, transparent=for_presentation)
        plt.close(fig)

        fig, ax = plt.subplots(1, 1, figsize=(10, 5))
        plot_type(data=df.loc[:, ["Statement", "Branch", "Pairs"]], palette="husl", ax=ax)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
        ax.set(ylabel="Coverage")
        if for_presentation:
            make_box_plot_white(ax)

        plt.savefig(os.path.join(plots_location, "coverage.png"), dpi=300, transparent=for_presentation)
        plt.close(fig)

        fig, ax = plt.subplots(1, 1, figsize=(10, 5))
        plot_type(data=df.loc[:, ["Intramethod pairs", "Intermethod pairs", "Interclass pairs"]], palette="husl", ax=ax)
        ax.set(ylabel="Number of pairs")
        if for_presentation:
            make_box_plot_white(ax)

        plt.savefig(os.path.join(plots_location, "pairs.png"), dpi=300, transparent=for_presentation)
        plt.close(fig)

        fig, ax = plt.subplots(1, 2, figsize=(10, 5))
        # fig.suptitle("Mutants and bugs")
        plot_type(data=df.loc[:, ["Mutants"]], palette="husl", ax=ax[0])
        ax[0].set(ylabel="Number of mutants")
        if for_presentation:
            make_box_plot_white(ax[0])

        plot_type(data=df.loc[:, ["Bugs"]], palette="husl", ax=ax[1])
        ax[1].set(ylabel="Number of defects")
        if for_presentation:
            make_box_plot_white(ax[1])
        plt.tight_layout()
        plt.savefig(os.path.join(plots_location, "mutants_bugs.png"), dpi=300, transparent=for_presentation)
        plt.close(fig)
