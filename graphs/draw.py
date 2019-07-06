from networkx.drawing.nx_agraph import graphviz_layout
import matplotlib.pyplot as plt

import networkx as nx

from graphs.create import line_key
from graphs.util import node_where


def draw_byte_cfg(g):
    pos = graphviz_layout(g, prog='dot')
    nx.draw_networkx(g, pos, node_size=150, node_color="#ccddff", node_shape="s")
    plt.show()


def draw_line_cfg(g):
    pos = graphviz_layout(g, prog='dot')
    nx.draw_networkx(g, pos, node_size=150, node_color="#ccddff", node_shape="s")
    plt.show()


def dump(line_cfg, source_start, source_lines, attr_keys=None):
    for i, l in enumerate(source_lines):
        line_num = i+source_start

        line_node, data = node_where(line_cfg, line_key, line_num)
        s = ""
        if data:
            if attr_keys:
                a = [": ".join((attr_key, str(data.get(attr_key, "Not found")))) for attr_key in attr_keys]
                s = ", ".join(a)
            else:
                s = data
        print(line_num, l[:-1].split("#")[0], "#", s)
