import cppimport.import_hook

import hello_ext

from model.cfg.project_cfg import read_du_index
from tracing.cpp_tracing.analize import VarIndex
from tracing.trace_reader import read_files_index, get_trace_files, read_df

import numpy as np


from time import time

import gc
from pathlib import Path

from util.misc import timing


@timing
def _analyze(project_root, trace_root):
    trace_files = get_trace_files(trace_root)

    file_index = read_du_index(project_root)
    variables_index = read_files_index(trace_root)

    var_index = VarIndex(variables_index, file_index)

    for i, f in enumerate(trace_files[:]):
        # if not f.endswith("__i_n_t_e_r___c_l_a_s_s___2/7.trace"):
        #     continue
        np_array, file_size = read_df(f, cut=-1)
        # print(np_array)
        # print(df_raw)
        # print("before adding vars")
        # df_raw.info(memory_usage='deep')

        defs, uses = var_index.get_vars(np_array, as_ints=True)
        # print(defs)
        # print(uses)
        # st = time()
        #
        # pairs_cpp_old = cpp_pairs_old(np_array, defs, uses)
        # total_old = time() - st
        #
        # pairs_count_old = count_pairs(pairs_cpp_old)
        #
        # print("total cpp old", total_old)
        # print("Speed: {}Mb/s".format(file_size // total_old))
        #
        # del pairs_cpp_old
        # gc.collect()

        st = time()
        pairs_cpp_new = cpp_pairs_new(*drop_where_no_def_no_use(np_array, defs, uses))
        total_new = time() - st

        pairs_count_new = count_pairs(pairs_cpp_new)

        print("total cpp new", total_new)
        print("Speed: {}Mb/s".format(file_size // total_new))



        # print("New variant is {} times faster".format(int(total_old / total_new)))
        # print("Old found {} pairs, new found {} pairs".format(pairs_count_old, pairs_count_new))
        print("New found {} pairs".format(pairs_count_new))
        print("Unique pairs {}".format(count_unique_pairs(pairs_cpp_new)))
        print("Progress:", (i + 1) * 100 // len(trace_files))
        # print_pairs(pairs_cpp_new)

        del pairs_cpp_new
        del np_array
        del defs
        del uses
        gc.collect()
        break

def count_unique_pairs(bunch_rows):
    unique = set()
    for rows in bunch_rows:
        for r in rows:
            for pair in r.pairs:
                # if ((pair.def_line,pair.use_line, pair.var_name) in unique):
                #     print("Repetition found: ", dump(pair))
                # else:
                    unique.add((pair.def_line,pair.use_line, pair.var_name))
    return len(unique)


def count_pairs(bunch_rows):
    c = 0
    for rows in bunch_rows:
        for r in rows:
            c += len(r.pairs)
    return c


def print_pairs(bunch_rows):

    for rows in bunch_rows:
        for r in rows:
            print(dump(r.pairs))


def drop_where_no_def_no_use(np_array, defs, uses):
    to_remove = set()
    for i, (ds, us) in enumerate(zip(defs, uses)):
        if len(ds) == 0 and len(us) == 0:
            to_remove.add(i)

    np_array = np.delete(np_array, list(to_remove), axis=0)

    defs = [ds for i, ds in enumerate(defs) if not i in to_remove]
    uses = [us for i, us in enumerate(uses) if not i in to_remove]
    return np_array, defs, uses


@timing
def cpp_pairs_old(np_array, defs, uses):
    return hello_ext.findDefUsePairs(to_vlads_data(np_array, defs, uses))


@timing
def to_vlads_data(np_array, defs, uses):
    return [hello_ext.Row(*row, list(ds), list(us)) for row, ds, us in
            zip(*drop_where_no_def_no_use(np_array, defs, uses))]


@timing
def cpp_pairs_new(np_array, defs, uses):
    t = np_array.T
    return hello_ext.wrapper(
        t[0],
        t[1],
        t[2],
        t[3],
        t[4],
        defs,
        uses
    )


def print_rows(rows_grouped):
    for group in rows_grouped:
        print("New scope")
        for row in group:
            print(dump(row))
            # print(repr_row(row))


def dump(obj):
    if isinstance(obj, (int, float, str, dict, set)):
        return str(obj)
    if isinstance(obj, list):
        s = "["
        for el in obj:
            s += dump(el) + ","
        return s + "]"
    s = obj.__class__.__name__ + "{"
    for attr in dir(obj):
        if attr[0] == "_":
            continue
        val = getattr(obj, attr)
        if isinstance(val, (int, float, str, dict, set)):
            s += attr + ":" + str(val) + ","
        elif isinstance(val, list):
            s += attr + ":" + dump(val) + ","
        else:
            s += dump(val) + ""
    return s + "}"


PROJECT_ROOT = Path(__file__).parent.parent.parent

_analyze(PROJECT_ROOT, PROJECT_ROOT)
