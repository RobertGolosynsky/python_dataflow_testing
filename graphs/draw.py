import inspect
import os
import subprocess
from tempfile import TemporaryFile, mkstemp

from networkx.drawing.nx_agraph import graphviz_layout
import matplotlib.pyplot as plt

import networkx as nx


from graphs import create as gc
import graphs.util as gu


def draw_byte_cfg(g):
    pos = graphviz_layout(g, prog='dot')
    nx.draw_networkx(g, pos, node_size=150, node_color="#ccddff", node_shape="s")
    plt.show()


def draw_with_code(g, pairs, func, control_edge_color="black", flow_edge_color="green", file=None):

    cfg = g.copy() # nx.MultiDiGraph()
    # cfg.add_nodes_from(g)
    # cfg.add_edges_from(g.edges)

    for e in cfg.edges:
        edge_data = cfg.edges[e]
        if "color" not in edge_data:
            edge_data["color"] = control_edge_color
        # cfg.edges[e]["color"] = control_edge_color
        # cfg.edges[e]["label"] = ""

    code, start_line = inspect.getsourcelines(func)
    code = [line[:-1] for line in code]

    for i, p in enumerate(pairs):
        def_node, data = gu.node_where(cfg, gc.LINE_KEY, p.definition.line)
        use_node, data = gu.node_where(cfg, gc.LINE_KEY, p.use.line)
        cfg.add_edge(use_node, def_node, label=p.use.varname, color=flow_edge_color)

    mapping = {}
    for node in cfg.nodes:
        attrs = cfg.nodes[node]
        line = attrs.get(gc.LINE_KEY, None)
        inst_g = attrs.get(gc.INSTRUCTIONS_KEY, None)
        instrs_range = None
        if inst_g:
            codes = [d.get(gc.INSTRUCTION_KEY, None) for n, d in inst_g.nodes(data=True) ]
            codes = [c.offset for c in codes if c]
            mn = min(codes)
            mx = max(codes)
            instrs_range = "%i-%i" % (mn, mx)
        if line:
            code_line = code[line-start_line]
            new_label = str(line) + ": " + code_line.strip().replace("\\","\\\\")
            if instrs_range:
                new_label+=" @ "+instrs_range
            mapping[node] = new_label

    cfg = nx.relabel_nodes(cfg, mapping)
    dot = nx.nx_agraph.to_agraph(cfg)
    if file:
        dot.draw(file, prog='dot')
    else:
        _, temp_file = mkstemp(suffix=".png", prefix="cfg_")
        dot.draw(temp_file, prog='dot')
        subprocess.run(["xdg-open", temp_file])


def draw_byte_cfg_dot(g, pairs, func,
                      control_edge_color="black",
                      flow_edge_color="green",
                      file=None):

    cfg = g.copy()


    for e in cfg.edges:
        edge_data = cfg.edges[e]
        if "color" not in edge_data:
            edge_data["color"] = control_edge_color

    code, start_line = inspect.getsourcelines(func)
    code = [line[:-1] for line in code]

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
            code_line = code[line - start_line]
            code_line = code_line.strip().replace("\\", "\\\\")
            new_label = "%i: %s %s @ %i: %s" % (inst.offset, inst.opname, str(inst.argval), line, code_line)
            mapping[node] = new_label

    cfg = nx.relabel_nodes(cfg, mapping)
    dot = nx.nx_agraph.to_agraph(cfg)
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
