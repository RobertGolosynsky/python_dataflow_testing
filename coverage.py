import importlib.util
import sys
from collections import defaultdict

from pathlib import Path

from networkx.drawing.nx_agraph import graphviz_layout
import matplotlib.pyplot as plt

import persistance
import module_cfg
import networkx as nx

managers = persistance.load_test_managers()

test_manager = managers[0]
project = test_manager.project

a_module = test_manager.tests[0]
module_path = a_module.file_path
sys.path.insert(0, project.project_path)

spec = importlib.util.spec_from_file_location("test_module", module_path)
test_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(test_module)

test_class = a_module.test_classes[0]
cfg = module_cfg.ModuleCFG(Path("dataset/linked_list/core/ll.py"))

def print_instructions(instrs):
    for i in instrs:
        print(i)


def rename_var(var,id, scope):
    if var.startswith("self"):
        var = var.replace("self", str(id))
    else:
        var = scope+"/"+var
    return var


def has_def(g, node):
    return "defs" in g.nodes[node] and len(g.nodes[node]["defs"])>0


def has_use(g, node):
    return "uses" in g.nodes[node]


def get_def(g, node):
    if has_def(g, node):
        return g.nodes[node]["defs"]


def get_use(g, node):
    if has_use(g, node):
        return g.nodes[node]["uses"]


class Def:
    def __init__(self, line, var, node, file):
        self.line = line
        self.var = var
        self.node = node
        self.file = file

    def __eq__(self, other):
        return self.line == other.line \
               and self.var == other.var \
               and self.file == other.file \
               and self.node == other.node

    def __hash__(self) -> int:
        return hash(self.line+self.var+self.node+str(self.file))


def reaching_definitions(g):
    reach_out = defaultdict(set)
    working_list = set(g.nodes())
    a_node_label = next(iter(working_list))
    # is_super_cfg = type(a_node_label) is not int

    # is_super_cfg = len().split(label_delimiter) > 1

    while len(working_list) > 0:
        a_node = working_list.pop()
        old_val = reach_out[a_node]
        reach_in = set()
        for succ in g.predecessors(a_node):
            # if is_super_cfg:
            #     if scope_for(succ) == scope_for(a_node):
            #         reach_in.update(reach_out[succ])
            #     else:
            #         for defining_node in reach_out[succ]:
            #             if has_attr_def(g, defining_node):
            #                 reach_in.add(defining_node)
            # else:
            reach_in.update(reach_out[succ])

        r_out = set()
        if has_def(g, a_node):
            node_defs = get_def(g, a_node)

            for deff in reach_in:
                for node_def in node_defs:
                    if not deff.var == node_def:
                        r_out.add(deff)
            for node_def in node_defs:
                node_line = g.nodes[a_node]["line"]
                node_file = g.nodes[a_node]["file"]

                r_out.add(Def(node_line, node_def, a_node, node_file))
            print("bbbbbbbbb")
        else:
            print("aaaaaaaaaaa")
            r_out = reach_in

        reach_out[a_node] = r_out
        if not r_out == old_val:
            working_list.update(g.successors(a_node))

    return reach_out


def definition_use_pairs(g):
    pairs = []
    reaching_defs = reaching_definitions(g)
    for node in g:
        if has_use(g, node):
            reach_in = reaching_defs[node]
            uses = get_use(g, node)
            for deff in reach_in:
                for use in uses:
                    if use == deff.var:
                        pairs.append((deff, node))

    return pairs

trace = []

for manager in managers:
    for test_module in manager.tests:
        for test_class in test_module.test_classes:
            for fn in test_class.function_nodes:
                g = nx.MultiDiGraph()
                prev = None
                for line, file, id_ in test_class.trace[fn]:
                    # print(line, id_, file)

                    line_key = str(line)
                    location = line_key + "@" + str(file)
                    cfg_name, nodes = cfg.line_context(line_key)
                    if cfg_name:
                        defs = cfg.defs_for_line(str(line))
                        uses = cfg.uses_for_line(str(line))

                        defs = [rename_var(adef, id_, cfg_name) for adef in defs]
                        uses = [rename_var(ause, id_, cfg_name) for ause in uses]

                        g.add_node(location, line=line_key, file=file, defs=defs, uses=uses)
                        if prev:
                            g.add_edge(prev, location)
                        prev = location
                        # print("g", g.nodes(data=True))
                        # print("defs:", list(defs))
                        # print("uses:", list(uses))
                    else:
                        print("no instructions on line", line)

                print("--------------"*5)
                # print(g.nodes(data=True))
                # for node in g.nodes:
                #     print(has_def(g,node))

                reach = reaching_definitions(g)
                # for node in reach:
                #     print(node, reach[node])
                print(fn.name)
                for deff, node in definition_use_pairs(g):
                    print("definition:", deff.file, deff.line, deff.var)
                    print("used at:", g.nodes[node]["file"], g.nodes[node]["line"])

                pos = graphviz_layout(g, prog='dot')
                nx.draw_networkx(g, pos, node_size=150, node_color="#ccddff", node_shape="s")
                # plt.show()



"""
1. 
self.a = new_a
c = self.a
2.
self.a = new_a
x = self.a.b 
3. 
self.a = new_a
if m:
    self.a.b = 3 <
x = self.a.b <
4.
self.a = new_a <
self.a.x() <
5. 
self.a = new_a <
self.a.b = new_b - this will be checked on the level of that class
self.a.x() <
6.
self.a = new_a
self.a.b = new_b
self.a = new_a <
x = self.a.b <
7.



// unresolved

node = self.get_next()

if x:
    v = node.a
    v.b = 3

x = node.a.b

"""