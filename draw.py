from networkx.drawing.nx_agraph import graphviz_layout
import matplotlib.pyplot as plt

import networkx as nx


def draw(g, extra_edges=None, extra_edges_labels=None):

    colors = ['#35332C', '#E1DAC2', '#D1B04B', '#3C2E00', '#C19200', '#242C24', '#A1B99F', '#48AB3D', '#053200', '#0F9E00', '#352D2C', '#E1C6C2', '#D15A4B', '#3C0700', '#C11600', '#201F25', '#8B8B9D', '#454292', '#02002A', '#0C0787']



    pos = graphviz_layout(g, prog='dot')
    labels = {l: str(l) for l in g.nodes}
    nx.draw(g, pos, node_size=150, node_color="#ccddff", node_shape="s", labels=labels)
    # nx.draw_networkx_edges(g, pos, node_size=150, node_color="#ccddff", node_shape="s", labels=labels)
    if extra_edges:
        color_list = []
        for varname in extra_edges_labels:
            color_list.append(colors[hash(varname) % len(colors)])

        print(color_list)


        collection = nx.draw_networkx_edges(g, pos, arrows=True, edgelist=extra_edges, edge_color=color_list)
        print(extra_edges)
        if extra_edges_labels:
            nx.draw_networkx_edge_labels(g, pos,
                                         arrows=True,
                                         edge_labels=dict(zip(extra_edges, extra_edges_labels)),
                                         font_size=8,
                                         alpha=1,
                                         bbox={"alpha":0})

    #     for patch in collection:
    #         patch.set_linestyle('dashed')

    plt.show()
