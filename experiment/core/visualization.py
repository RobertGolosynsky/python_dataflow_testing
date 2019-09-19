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

    plt.tight_layout()

    plt.savefig(filename)
    plt.close()
