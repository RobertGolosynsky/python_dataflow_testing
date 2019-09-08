import dataflow.reaching_definitions as rd
from graphs.create import CFG


def inter_class_def_use_pairs_cfg(cfg1: CFG, cfg2: CFG):
    reach_out_1 = rd.reaching_definitions(cfg1.g, object_vars_only=True)

    cfg1_exit = cfg1.exit_label
    cfg2_entry = cfg2.entry_label

    reach_out_cfg1_exit = reach_out_1[cfg1_exit]

    # reach_out_cfg1_exit = {definition for definition in reach_out_cfg1_exit
    #                        if definition.varname[:5] == "self."}

    initial_set = {cfg2_entry: reach_out_cfg1_exit}

    pairs = rd.definition_use_pairs(cfg2.g, initial_set=initial_set, object_vars_only=True)

    return pairs
