import matplotlib.pyplot as plt
import seaborn as sns


def create_box_plot(df, title, filename,
                    x, y, hue,
                    xlabel, ylabel,
                    swarm=False
                    ):
    plt.figure(figsize=(16, 8))
    sns.boxplot(x=x, y=y, hue=hue, data=df, palette="husl")
    if swarm:
        sns.swarmplot(x=x, y=y, hue=hue, data=df, color=".25", size=2)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))

    plt.savefig(filename)
    plt.close()


def create_cat_plot(df, title, filename,
                    x, y, hue,
                    xlabel, ylabel
                    ):

    sns.catplot(x=x, y=y, hue=hue, data=df, palette="husl",
                capsize=.2, kind="point", height=8, aspect=2, dodge=True)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    plt.savefig(filename)
    plt.close()


def create_cat_plot_with_count(df, title, filename,
                               x, y, hue,
                               xlabel, ylabel,
                               no_ordering=False
                               ):
    fig, (ax1, ax2) = plt.subplots(2, sharex=True, figsize=(16, 8))
    if no_ordering:
        sns.catplot(x=x, y=y, hue=hue, data=df, palette="husl", capsize=.2, kind="point", dodge=True, ax=ax1)
        sns.countplot(x=x, hue=hue, data=df, palette="husl", dodge=True, ax=ax2)
    else:
        def key(a_bin):
            return int(a_bin[1:-1].split("-")[0])

        order = list(sorted(df[x].unique(), key=key))
        sns.catplot(x=x, y=y, hue=hue, data=df, palette="husl", capsize=.2, kind="point", dodge=True,
                    order=order, ax=ax1)
        sns.countplot(x=x, hue=hue, data=df, palette="husl", dodge=True,
                      order=order, ax=ax2)
    plt.title(title)

    fig.savefig(filename)
    plt.close(fig)

