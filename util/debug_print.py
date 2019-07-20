import networkx as nx
import dataflow.def_use as du
import graphs.create as gc


def variables(cfg: nx.DiGraph, self_only=False):
    print_data = _defs_uses_data(cfg)
    ds = set()
    us = set()
    for l, d, u in print_data:
        if d:
            if not self_only or (self_only and d.startswith("self.")):
                ds.add(d)
        if u:
            if not self_only or (self_only and u.startswith("self.")):
                us.add(u)

    print("Definitions: ", ds)
    print("Uses: ", us)


def _defs_uses_data(cfg: nx.DiGraph):
    print_data = []
    for n, d in cfg.nodes(data=True):
        line = d.get(gc.LINE_KEY)
        definition = d.get(du.DEFINITION_KEY)
        use = d.get(du.USE_KEY)
        if line:
            print_data.append((line, definition, use))
    return list(sorted(print_data, key=lambda x:x[0]))


def defs_uses(cfg: nx.DiGraph):
    print_data = _defs_uses_data(cfg)
    print("line, definition, use")
    for l, d, u in print_data:
        if d or u:
            print(l, d, u)

def defs_uses_table(cfg: nx.DiGraph):

    print_data = _defs_uses_data(cfg)
    for row in print_data:
        print("line: {}, def:{}, use:{}".format(*row))