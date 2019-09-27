import os
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd


def visualize_dataset(ms, plots_location):
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
                               "Mutants", "Bugs", "Statement(%)", "Branch(%)", "Pairs(%)"])

    df["All pairs"] = df["Intramethod pairs"] + df["Intermethod pairs"] + df["Interclass pairs"]
    # plot_type = sns.violinplot
    plot_type = sns.boxplot
    fig, ax = plt.subplots(1, 2, figsize=(16, 8))
    plot_type(data=df.loc[:, ["Statements", "Branches", "All pairs"]], palette="husl", ax=ax[0]) \
        .set_title("Total coverage goals")
    plot_type(data=df.loc[:, ["Statement(%)", "Branch(%)", "Pairs(%)"]], palette="husl", ax=ax[1]) \
        .set_title("Coverage")

    plt.savefig(os.path.join(plots_location, "coverage.png"))

    fig, ax = plt.subplots(1, 1, figsize=(16, 8))
    plot_type(data=df.loc[:, ["Intramethod pairs", "Intermethod pairs", "Interclass pairs"]], palette="husl", ax=ax) \
        .set_title("Pairs detailed")
    plt.savefig(os.path.join(plots_location, "pairs.png"))

    fig, ax = plt.subplots(1, 2, figsize=(16, 8))
    fig.suptitle("Mutants and bugs")
    plot_type(data=df.loc[:, ["Mutants"]], palette="husl", ax=ax[0])
    plot_type(data=df.loc[:, ["Bugs"]], palette="husl", ax=ax[1])
    plt.savefig(os.path.join(plots_location, "mutants_bugs.png"))
