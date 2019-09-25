from tracing.index_factory import VarIndex
from tracing.trace_reader import read_as_np_array
from tracing.tracer import SCOPE_INDEX, IDX_INDEX, LINE_INDEX


# TODO: group by self
def analyze(trace_path, index: VarIndex, scopes_ends):
    df, size_mb = read_as_np_array(trace_path)
    defs, uses = index.get_object_vars(df)
    reach_in = []
    intermethod_pairs = []
    intraclass_pairs = []
    for this_row, this_ds, this_us, in zip(df, defs, uses):
        # join reachins to pairs
        for def_idx, def_var_name in reach_in:
            that_row = df[def_idx]
            that_scope = that_row[SCOPE_INDEX]
            if that_scope != this_row[SCOPE_INDEX]:
                if def_var_name in this_us:
                    this_row_idx = this_row[IDX_INDEX]
                    that_scope_end = scopes_ends[that_scope]
                    du_pair = (that_row[LINE_INDEX], this_row[LINE_INDEX])
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
