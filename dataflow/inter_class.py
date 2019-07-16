import networkx as nx
import dataflow.reaching_definitions as rd
import graphs.util as gu
import graphs.draw as gd


def inter_class_def_use_pairs(cfg1: nx.DiGraph, cfg2: nx.DiGraph):
    reach_out_1 = rd._reaching_definitions(cfg1)
    print("Reach out cfg1:", reach_out_1)
    gd.draw_line_cfg(cfg1)
    cfg1_exit = gu.nodes_with_out_degree(cfg1, 0)[0]
    cfg2_entry = gu.nodes_with_in_degree(cfg2, 0)[0]

    reach_out_cfg1_exit = reach_out_1[cfg1_exit]
    print("Reach out cfg1 exit:", reach_out_cfg1_exit)
    initial_set = {cfg2_entry: reach_out_cfg1_exit}
    reach_out_2 = rd._reaching_definitions(
        cfg2,
        initial_set=initial_set
    )
    return reach_out_2
