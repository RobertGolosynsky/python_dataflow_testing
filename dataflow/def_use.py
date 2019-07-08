import networkx as nx

from draw import draw
from graphs.create import instructions_key, instruction_key, try_create_cfg, FILE_KEY
from graphs.draw import dump

DEFINITIONS_KEY = "definitions"
USES_KEY = "uses"


def try_create_cfg_with_definitions_and_uses(func):
    line_cfg = try_create_cfg(func)
    if line_cfg:
        return add_definitions_and_uses(line_cfg)
    return None


def add_definitions_and_uses(line_cfg):
    defs_and_uses = {}
    for line_node in line_cfg.nodes():
        deffs = list(_find_definitions_at_line(line_cfg, line_node))
        uses = list(_find_uses_at_line(line_cfg, line_node))
        defs_and_uses[line_node] = {}
        defs_and_uses[line_node][DEFINITIONS_KEY] = deffs
        defs_and_uses[line_node][USES_KEY] = uses

    nx.set_node_attributes(line_cfg, defs_and_uses)

    return line_cfg


def _resolve_target(g, node):
    pred = next(g.predecessors(node))
    pred_instr = g.nodes[pred][instruction_key]

    if pred_instr.opname == "LOAD_FAST":
        return pred_instr.argval
    elif pred_instr.opname == "LOAD_ATTR":
        pred_target = _resolve_target(g, pred)
        if pred_target:
            t = _resolve_target(g, pred) + "." + pred_instr.argval
            return t
        else:
            return None
    else:
        return None


def _get_def(g, node):
    if instruction_key in g.nodes[node]:
        instr = g.nodes[node][instruction_key]
        if instr.opname == "STORE_FAST":
            return instr.argval
        if instr.opname == "STORE_ATTR":
            target = _resolve_target(g, node)
            if target:
                return target + "." + instr.argval


def _get_use(g, node):
    if instruction_key in g.nodes[node]:
        instr = g.nodes[node][instruction_key]
        if instr.opname == "LOAD_FAST":
            return instr.argval
        if instr.opname == "LOAD_ATTR":
            target = _resolve_target(g, node)
            if target:
                return target + "." + instr.argval


def _find_definitions_at_line(line_cfg, node):
    node_attrs = line_cfg.nodes[node]
    var_names = []
    if instructions_key not in node_attrs:
        return var_names

    instructions_cfg_at_line = node_attrs[instructions_key]
    for byte_node in instructions_cfg_at_line.nodes:
        var_name = _get_def(instructions_cfg_at_line, byte_node)
        if var_name:
            var_names.append(var_name)

    return var_names


def _find_uses_at_line(line_cfg, node):
    node_attrs = line_cfg.nodes[node]
    var_names = []
    if instructions_key not in node_attrs:
        return var_names

    instructions_cfg_at_line = node_attrs[instructions_key]
    for byte_node in instructions_cfg_at_line.nodes:
        var_name = _get_use(instructions_cfg_at_line, byte_node)
        if var_name:
            var_names.append(var_name)

    return var_names
