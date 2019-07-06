from networkx.drawing.nx_agraph import graphviz_layout
import matplotlib.pyplot as plt

import networkx as nx


def draw_byte_cfg(g):
    pos = graphviz_layout(g, prog='dot')
    nx.draw_networkx(g, pos, node_size=150, node_color="#ccddff", node_shape="s")
    plt.show()


def draw_line_cfg(g):
    pos = graphviz_layout(g, prog='dot')
    nx.draw_networkx(g, pos, node_size=150, node_color="#ccddff", node_shape="s")
    plt.show()

