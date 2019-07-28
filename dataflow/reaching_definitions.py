from collections import defaultdict

import networkx as nx

import dataflow.def_use as du
import graphs.create as cr
from collections import namedtuple

Var = namedtuple("Var", ["file", "line", "varname"])
Pair = namedtuple("Pair", ["definition", "use"])


def definition_use_pairs(cfg: nx.DiGraph, initial_set=None):
    pairs = []
    reaching_deffs = _reaching_definitions(cfg, initial_set=initial_set)
    for node in cfg.nodes():
        node_attrs = cfg.nodes[node]
        use = node_attrs.get(du.USE_KEY, None)
        use_file = node_attrs.get(cr.FILE_KEY, "UNDEFINED")
        use_line = node_attrs.get(cr.LINE_KEY, -1)

        if use:
            reach_in = reaching_deffs[node]
            for reaching_var in reach_in:
                if use == reaching_var.varname:
                    pair = Pair(
                        reaching_var,
                        Var(use_file, use_line, use)
                    )
                    pairs.append(pair)
    return pairs


def _reaching_definitions(cfg: nx.DiGraph, initial_set=None):
    reach_out = defaultdict(set)
    working_list = set(cfg.nodes())
    while len(working_list) > 0:
        a_node = working_list.pop()
        # print(a_node)
        old_val = reach_out[a_node]
        # print("before ", old_val)
        node_reach_in = set()
        if initial_set:
            node_reach_in = initial_set.get(a_node, set())
        for a_pred in cfg.predecessors(a_node):
            node_reach_in.update(reach_out[a_pred])

        node_reach_out = set()
        node_attrs: dict = cfg.nodes[a_node]
        node_definition = node_attrs.get(du.DEFINITION_KEY, None)
        node_file = node_attrs.get(du.FILE_KEY, "UNDEFINED")
        node_line = node_attrs.get(cr.LINE_KEY, -1)
        if node_definition:
            for reaching_var in node_reach_in:
                if not reaching_var.varname == node_definition:
                    node_reach_out.add(reaching_var)
            if not initial_set:
                defined_var = Var(node_file, node_line, node_definition)
                node_reach_out.add(defined_var)
        else:
            node_reach_out = node_reach_in

        reach_out[a_node] = node_reach_out
        # print("after ", node_reach_out)
        if not node_reach_out == old_val:
            working_list.update(cfg.successors(a_node))

    return reach_out
