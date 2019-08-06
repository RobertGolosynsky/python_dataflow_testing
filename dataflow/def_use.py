import networkx as nx

from graphs.create import INSTRUCTION_KEY, try_create_cfg, FILE_KEY

DEFINITION_KEY = "definition"
USE_KEY = "use"


def try_create_cfg_with_definitions_and_uses(func, definition_line=None, args=None,
                                             filter_self=True):
    cfg = try_create_cfg(func, definition_line=definition_line, args=args)
    if cfg:
        return _add_definitions_and_uses(cfg, filter_self=filter_self)
    return None


def _add_definitions_and_uses(cfg, filter_self=True):
    defs_and_uses = {}
    for node in cfg.nodes():
        defs_and_uses[node] = {}

        def_name = _get_def(cfg, node)
        use_name = _get_use(cfg, node)

        defs_and_uses[node][DEFINITION_KEY] = _should_add_var_name(def_name, filter_self=filter_self)
        defs_and_uses[node][USE_KEY] = _should_add_var_name(use_name, filter_self=filter_self)

    nx.set_node_attributes(cfg, defs_and_uses)
    return cfg


def _should_add_var_name(maybe_var, filter_self=True):
    if maybe_var:
        if not filter_self:
            return maybe_var
        else:
            if not maybe_var == "self":
                return maybe_var


def _resolve_target(g, node):
    pred = next(g.predecessors(node))
    pred_instr = g.nodes[pred][INSTRUCTION_KEY]

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
    if INSTRUCTION_KEY in g.nodes[node]:
        instr = g.nodes[node][INSTRUCTION_KEY]
        if instr.opname == "STORE_FAST":
            return instr.argval
        if instr.opname == "STORE_ATTR":
            target = _resolve_target(g, node)
            if target:
                return target + "." + instr.argval


def _get_use(g, node):
    if INSTRUCTION_KEY in g.nodes[node]:
        instr = g.nodes[node][INSTRUCTION_KEY]
        if instr.opname == "LOAD_FAST":
            return instr.argval
        if instr.opname == "LOAD_ATTR":
            target = _resolve_target(g, node)
            if target:
                return target + "." + instr.argval
