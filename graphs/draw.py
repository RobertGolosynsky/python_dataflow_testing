import inspect
import subprocess
from collections import defaultdict
from tempfile import mkstemp

from networkx.drawing.nx_agraph import graphviz_layout
import matplotlib.pyplot as plt

import networkx as nx

from graphs import create as gc
import graphs.util as gu
from graphs.keys import REMOVED_KEY, CALL_KEY, RETURN_KEY, LINE_KEY


def draw_byte_cfg(g):
    pos = graphviz_layout(g, prog='dot')
    nx.draw_networkx(g, pos, node_size=150, node_color="#ccddff", node_shape="s")
    plt.show()


def draw_byte_cfg_dot(g, pairs, func,
                      control_edge_color="black",
                      flow_edge_color="green",
                      file=None):
    cfg = g.copy()

    for e in cfg.edges:
        edge_data = cfg.edges[e]
        if "color" not in edge_data:
            edge_data["color"] = control_edge_color

    # code, start_line = inspect.getsourcelines(func)
    # code = [line[:-1] for line in code]

    for i, p in enumerate(pairs):
        def_node, data = gu.node_where(cfg, gc.LINE_KEY, p.definition.line)
        use_node, data = gu.node_where(cfg, gc.LINE_KEY, p.use.line)

        cfg.add_edge(use_node, def_node, label=p.use.varname, color=flow_edge_color)

    mapping = {}
    for node in cfg.nodes:
        attrs = cfg.nodes[node]
        line = attrs.get(gc.LINE_KEY, None)
        inst = attrs.get(gc.INSTRUCTION_KEY, None)
        if inst and line:
            # code_line = code[line-start_line]
            # new_label = str(line) + ": " + code_line.strip().replace("\\","\\\\")
            # if instrs_range:
            #     new_label+=" @ "+instrs_range
            # code_line = code[line - start_line]
            # code_line = code_line.strip().replace("\\", "\\\\")
            code_line = ""
            new_label = "%i: %s %s @ %i: %s" % (inst.offset, inst.opname, str(inst.argval), line, code_line)
            mapping[node] = new_label

    # cfg = nx.relabel_nodes(cfg, mapping)
    node_lines = {node: str(data.get(LINE_KEY)) for node, data in cfg.nodes(data=True)}
    cfg = nx.relabel_nodes(cfg, {node: node + "@ln" + node_lines[node] + ":" +
                                       cfg.nodes[node].get(gc.INSTRUCTION_KEY, None).opname + " " +
                                       str(cfg.nodes[node].get(gc.INSTRUCTION_KEY, None).argval)
    if gc.INSTRUCTION_KEY in cfg.nodes[node] else node + ":" + "None"
                                 for node in cfg})

    for fr, to, data in cfg.edges(data=True):
        if data.get(REMOVED_KEY):
            data["color"] = None
        if CALL_KEY in data:
            data["color"] = "blue"
            data["label"] = "Call to " + data[CALL_KEY]

        if RETURN_KEY in data:
            data["color"] = "red"
            data["label"] = "Return from " + data[RETURN_KEY]

    dot = nx.nx_agraph.to_agraph(cfg)
    clusters = defaultdict(list)
    for node in cfg.nodes:
        function_name = node.split("@")[0]
        clusters[function_name].append(node)
    for cluster in clusters:
        dot.add_subgraph(clusters[cluster], name="cluster_" + cluster, label="method " + cluster, bgcolor=Color.next())

    if file:
        dot.draw(file, prog='dot')
    else:
        _, temp_file = mkstemp(suffix=".png", prefix="cfg_")
        dot.draw(temp_file, prog='dot')
        subprocess.run(["xdg-open", temp_file])


def draw_block_cfg(func, img_file=None):
    from xdis import PYTHON_VERSION, IS_PYPY
    from control_flow.bb import basic_blocks
    from control_flow.cfg import ControlFlowGraph

    import dis
    import os
    name = "some_name"

    bb_mgr = basic_blocks(PYTHON_VERSION, IS_PYPY, func)

    # dis.dis(func)
    cfg = ControlFlowGraph(bb_mgr)
    dot_path = '/tmp/flow-%s.dot' % name
    if not img_file:
        png_path = '/tmp/flow-%s.png' % name
    else:
        png_path = img_file
    with open(dot_path, 'w') as f:
        f.write(cfg.graph.to_dot(False))
    # print("%s written" % dot_path)

    os.system("dot -Tpng %s > %s" % (dot_path, png_path))
    if not img_file:
        subprocess.run(["xdg-open", png_path])


def dump(line_cfg, source_start, source_lines, attr_keys=None):
    for i, l in enumerate(source_lines):
        line_num = i + source_start

        line_node, data = gu.node_where(line_cfg, gc.LINE_KEY, line_num)
        s = ""
        if data:
            if attr_keys:
                a = [": ".join((attr_key, str(data.get(attr_key, "Not found")))) for attr_key in attr_keys]
                s = ", ".join(a)
            else:
                s = data
        print(line_num, l[:-1].split("#")[0], "#", s)


def source_w_pairs(source_file, pairs, trace=()):
    hit_lines = set(trace)
    pair_suffs = defaultdict(list)
    c = 0
    with open(source_file) as f:
        source_lines = f.readlines()
    for i, l in enumerate(source_lines):
        line_num = i + 1
        for pair in pairs:
            if pair[0] == line_num:
                c += 1
                pair_suffs[pair[0]].append(">${}".format(c))
                pair_suffs[pair[1]].append("<${}".format(c))
    for i, l in enumerate(source_lines):
        line_num = i + 1
        s = ", ".join(pair_suffs[line_num])

        if line_num in hit_lines:
            marker = ">>>"
        else:
            marker = "   "
        print(line_num, marker, l[:-1].split("#")[0], s)


class Color:
    colors = ['#C1D989', '#E9F4CE', '#DDF0B2', '#A5C262', '#87A73B', '#6BA980', '#AECEB9', '#8BBB9B', '#4C9765',
              '#2E824B', '#E79F92', '#FFDDD7', '#FFC8BE', '#CE7868', '#B2513F', '#B4729C', '#D7B5CA', '#C794B4',
              '#A15183', '#8B316A']
    c = 0

    @classmethod
    def next(cls):
        color = cls.colors[cls.c]
        cls.c += 5
        if cls.c >= len(cls.colors):
            cls.c = cls.c % 5 + 1
        return color
