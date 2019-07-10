from collections import defaultdict

import networkx as nx

import dataflow.def_use as du
import graphs.create as cr
from collections import namedtuple

Var = namedtuple("VariableDefinition", ["file", "line", "varname"])
Pair = namedtuple("DefinitionUsePair", ["def_file", "def_line", "use_file", "use_line", "varname"])


def definition_use_pairs(cfg: nx.DiGraph):
    pairs = []
    reaching_deffs = _reaching_definitions(cfg)
    for node in cfg.nodes():
        node_attrs = cfg.nodes[node]
        uses = node_attrs.get(du.USES_KEY, [])
        use_file = node_attrs.get(cr.FILE_KEY, "UNDEFINED")
        use_line = node_attrs.get(cr.LINE_KEY, -1)

        if len(uses) > 0:
            reach_in = reaching_deffs[node]
            for reaching_var in reach_in:
                for use_varname in uses:
                    if use_varname == reaching_var.varname:
                        pair = Pair(
                            reaching_var.file,
                            reaching_var.line,
                            use_file,
                            use_line,
                            reaching_var.varname
                        )
                        pairs.append(pair)
    return pairs


def _reaching_definitions(cfg: nx.DiGraph):

    reach_out = defaultdict(set)
    working_list = set(cfg.nodes())
    while len(working_list) > 0:
        a_node = working_list.pop()
        old_val = reach_out[a_node]
        node_reach_in = set()
        for a_pred in cfg.predecessors(a_node):
            node_reach_in.update(reach_out[a_pred])

        node_reach_out = set()
        node_attrs: dict = cfg.nodes[a_node]
        node_definitions = node_attrs.get(du.DEFINITIONS_KEY, [])
        node_file = node_attrs.get(du.FILE_KEY, "UNDEFINED")
        node_line = node_attrs.get(cr.LINE_KEY, -1)
        if len(node_definitions) > 0:
            for reaching_var in node_reach_in:
                for defined_variable_name in node_definitions:
                    if not reaching_var.varname == defined_variable_name:
                        node_reach_out.add(reaching_var)
            node_deffined_variables = [Var(node_file, node_line, var_name)
                                       for var_name in node_definitions]
            node_reach_out.update(node_deffined_variables)
        else:
            node_reach_out = node_reach_in

        reach_out[a_node] = node_reach_out

        if not node_reach_out == old_val:
            working_list.update(cfg.successors(a_node))

    return reach_out
