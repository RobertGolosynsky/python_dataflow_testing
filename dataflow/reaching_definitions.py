from collections import defaultdict

import networkx as nx

import dataflow.def_use as du
from pprint import pformat
from collections import namedtuple

from graphs.keys import FILE_KEY, LINE_KEY, FUNCTION_KEY, REMOVED_KEY, CALL_KEY, RETURN_KEY


class Var:
    def __init__(self, line, varname, flow_mark=None,
                 flow_mark_log=None,
                 not_intermethod=False,
                 defined_in=None, passed_through_return_or_call=False):

        self.line = line
        self.varname = varname
        self.defined_in = defined_in
        self.passed_through_return_or_call = passed_through_return_or_call
        self.not_intermethod = not_intermethod
        if flow_mark_log is None:
            self.flow_mark_log = []
        else:
            self.flow_mark_log = flow_mark_log
        if flow_mark is None:
            self.flow_mark = []
        else:
            self.flow_mark = flow_mark

    def can_return_to(self, function_name):
        return not self.flow_mark or self.flow_mark[-1] == function_name

    def __hash__(self):
        return hash(self.line) + hash(self.varname)

    def __eq__(self, other):
        return self.line == other.line and self.varname == other.varname

    def __repr__(self):
        return pformat(vars(self))

    def copy(self):
        return Var(line=self.line,
                   varname=self.varname,
                   defined_in=self.defined_in,
                   not_intermethod=self.not_intermethod,
                   flow_mark=self.flow_mark.copy(),
                   flow_mark_log=self.flow_mark_log.copy(),
                   passed_through_return_or_call=self.passed_through_return_or_call
                   )


# Var = namedtuple("Var", ["line", "varname"])
Pair = namedtuple("Pair", ["definition", "use"])


def definition_use_pairs(cfg: nx.DiGraph,
                         initial_set=None,
                         intermethod_only=False,
                         object_vars_only=False):
    pairs = []
    reaching_deffs = reaching_definitions(cfg,
                                          initial_set=initial_set,
                                          object_vars_only=object_vars_only)

    # for node in sorted(reaching_deffs):
    #     print("node:",node," -> "," ".join(str(var) for var in reaching_deffs[node]))
    for node in cfg.nodes():
        node_attrs = cfg.nodes[node]
        use = node_attrs.get(du.USE_KEY, None)
        use_line = node_attrs.get(LINE_KEY, -1)

        if use:
            reach_in = reaching_deffs[node]
            for reaching_var in reach_in:
                if use == reaching_var.varname:
                    if not intermethod_only or (reaching_var.passed_through_return_or_call and
                                                not reaching_var.not_intermethod):
                        pair = Pair(
                            reaching_var,
                            Var(use_line, use)
                        )
                        pairs.append(pair)
    return pairs


def edge_removed(data):
    return data.get(REMOVED_KEY, False)


def is_call_edge(data):
    return CALL_KEY in data


def is_return_edge(data):
    return RETURN_KEY in data


def reaching_definitions(cfg: nx.DiGraph, initial_set=None, object_vars_only=False):
    reach_out = defaultdict(set)
    working_list = set(cfg.nodes())
    while len(working_list) > 0:
        a_node = working_list.pop()
        node_attrs: dict = cfg.nodes[a_node]
        current_function = node_attrs.get(FUNCTION_KEY)

        old_val = reach_out[a_node]

        node_reach_in = set()

        if initial_set:
            node_reach_in = initial_set.get(a_node, set())

        for source, dest, edge_data in cfg.in_edges(a_node, data=True):

            if not edge_removed(edge_data):
                if is_call_edge(edge_data):
                    caller_function = cfg.nodes[source][FUNCTION_KEY]
                    callee_function = cfg.nodes[a_node][FUNCTION_KEY]
                    variables = {var.copy() for var in reach_out[source]}

                    for var in variables:
                        var.flow_mark.append(caller_function)
                        var.flow_mark_log.append(caller_function + " calls " + callee_function)
                        var.passed_through_return_or_call = True
                        node_reach_in.add(var)
                    pass

                elif is_return_edge(edge_data):
                    return_from_function = cfg.nodes[source][FUNCTION_KEY]
                    return_to_function = cfg.nodes[a_node][FUNCTION_KEY]

                    variables = {var.copy() for var in reach_out[source] if var.can_return_to(return_to_function)}
                    for var in variables:
                        var.flow_mark_log.append(return_from_function + " returns " + return_to_function)

                        if var.flow_mark:
                            var.flow_mark.pop()
                        if return_from_function == var.defined_in:
                            var.not_intermethod = True
                        else:
                            var.passed_through_return_or_call = True
                        node_reach_in.add(var)
                    pass

                else:
                    node_reach_in.update({var.copy() for var in reach_out[source]})

        node_reach_out = set()

        node_definition = node_attrs.get(du.DEFINITION_KEY, None)
        node_line = node_attrs.get(LINE_KEY, -1)
        if node_definition:
            for reaching_var in node_reach_in:
                if not reaching_var.varname == node_definition:
                    node_reach_out.add(reaching_var)
            if not initial_set:
                if not object_vars_only or node_definition.startswith("self."):
                    defined_var = Var(node_line, node_definition, defined_in=current_function)
                    node_reach_out.add(defined_var)
        else:
            node_reach_out = node_reach_in

        reach_out[a_node] = node_reach_out
        # print("after ", node_reach_out)
        # print(node_reach_out, old_val)
        # print("node:", a_node, " -> ", " ".join(str(var) for var in node_reach_out))

        if not node_reach_out == old_val:
            working_list.update(cfg.successors(a_node))

    return reach_out
