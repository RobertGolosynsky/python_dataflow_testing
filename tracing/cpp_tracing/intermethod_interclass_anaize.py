from tracing.index_factory import VarIndex
from tracing.trace_reader import read_df
from graphs.draw import source_w_pairs


def analyze(trace_path, index: VarIndex, scopes_ends):
    df, size_mb = read_df(trace_path)
    defs, uses = index.get_object_vars(df)
    # print(defs, uses)
    reach_in = []
    intermethod_pairs = []
    intraclass_pairs = []
    for this_row, this_ds, this_us, in zip(df, defs, uses):
        # join reachins to pairs
        for def_idx, def_var_name in reach_in:
            that_row = df[def_idx]
            that_scope = that_row[4]
            if that_scope != this_row[4]:
                if def_var_name in this_us:
                    this_row_idx = this_row[0]
                    that_scope_end = scopes_ends[that_scope]
                    du_pair = (that_row[2], this_row[2])
                    if that_scope_end > this_row_idx:
                        intermethod_pairs.append(du_pair)
                    else:
                        intraclass_pairs.append(du_pair)

        # filter reach ins
        reach_in = [(def_idx, var_name) for def_idx, var_name in reach_in if var_name not in this_ds]

        # add this row definitions
        for this_definition in this_ds:
            reach_in.append((this_row[0], this_definition))
    return intermethod_pairs, intraclass_pairs
