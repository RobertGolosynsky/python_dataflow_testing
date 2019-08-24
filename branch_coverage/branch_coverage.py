import networkx as nx

from graphs.keys import LINE_KEY


def first_lines_of_branches(g: nx.DiGraph):
    first_lines = []
    for node in g.nodes():
        if g.out_degree[node] > 1:
            for successor in g.successors(node):
                line = g.nodes[successor].get(LINE_KEY)
                if line:
                    first_lines.append(line)

    return first_lines
