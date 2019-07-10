import inspect
import os
import subprocess
from tempfile import TemporaryFile, mkstemp

from networkx.drawing.nx_agraph import graphviz_layout
import matplotlib.pyplot as plt

import networkx as nx

import graphs.create as gc
import graphs.util as gu


def draw_byte_cfg(g):
    pos = graphviz_layout(g, prog='dot')
    nx.draw_networkx(g, pos, node_size=150, node_color="#ccddff", node_shape="s")
    plt.show()


def draw_line_cfg(g):
    pos = graphviz_layout(g, prog='dot')
    nx.draw_networkx(g, pos, node_size=150, node_color="#ccddff", node_shape="s")
    plt.show()


def draw_with_code(g, pairs, func, control_edge_color="black", flow_edge_color="green", file=None):

    cfg = nx.MultiDiGraph(g)
    for e in cfg.edges:
        cfg.edges[e]["color"] = control_edge_color
        cfg.edges[e]["label"] = ""

    code, start_line = inspect.getsourcelines(func)
    code = [line[:-1] for line in code]

    for i, p in enumerate(pairs):
        def_node, data = gu.node_where(cfg, gc.LINE_KEY, p.def_line)
        use_node, data = gu.node_where(cfg, gc.LINE_KEY, p.use_line)
        cfg.add_edge(use_node, def_node, label=p.varname, color="red")

    mapping = {}
    for node in cfg.nodes:
        attrs = cfg.nodes[node]
        line = attrs.get(gc.LINE_KEY, None)
        if line:
            code_line = code[line-start_line]
            new_label = str(line) + ": " + code_line.strip()
            mapping[node] = new_label

    cfg = nx.relabel_nodes(cfg, mapping)
    dot = nx.nx_agraph.to_agraph(cfg)
    if file:
        dot.draw(file, prog='dot')
    else:
        _, temp_file = mkstemp(suffix=".png", prefix="cfg_")
        dot.draw(temp_file, prog='dot')
        subprocess.run(["xdg-open", temp_file])


def dump(line_cfg, source_start, source_lines, attr_keys=None):
    for i, l in enumerate(source_lines):
        line_num = i+source_start

        line_node, data = gu.node_where(line_cfg, gc.LINE_KEY, line_num)
        s = ""
        if data:
            if attr_keys:
                a = [": ".join((attr_key, str(data.get(attr_key, "Not found")))) for attr_key in attr_keys]
                s = ", ".join(a)
            else:
                s = data
        print(line_num, l[:-1].split("#")[0], "#", s)
