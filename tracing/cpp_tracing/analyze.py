
from time import time
import gc

from cpp.cpp_import import load_cpp_extension
import numpy as np

from tracing.trace_reader import read_df
from util.misc import timing

def_use_pairs_ext = load_cpp_extension("def_use_pairs_ext")


@timing
def analyze_trace(trace_file, py_var_index):
    np_array, file_size = read_df(trace_file, cut=-1)


    st = time()
    defs, uses = py_var_index.get_vars(np_array)
    # pairs_cpp_new = cpp_pairs_new(*_drop_where_no_def_no_use(np_array, defs, uses))
    pairs_cpp_new = cpp_pairs_new(np_array, defs, uses)
    total_new = time() - st

    pairs_count_new = _count_pairs(pairs_cpp_new)

    print("total cpp new", total_new)
    print("Speed: {}Mb/s".format(file_size // total_new))

    # print("New variant is {} times faster".format(int(total_old / total_new)))
    # print("Old found {} pairs, new found {} pairs".format(pairs_count_old, pairs_count_new))
    print("New found {} pairs".format(pairs_count_new))
    unique_pairs = _unique_pairs(pairs_cpp_new)
    print("Unique pairs {}".format(len(unique_pairs)))

    # print_pairs(pairs_cpp_new)

    del pairs_cpp_new
    del np_array
    del defs
    del uses
    gc.collect()

    return unique_pairs


@timing
def analyze_trace_w_index(trace_file, cpp_var_index, cut=-1):
    np_array, file_size = read_df(trace_file, cut=cut)
    # with np.printoptions(precision=3, linewidth=100):
    #     print(np_array)
    # st = time()
    pairs_cpp_new = cpp_pairs_w_index(np_array, cpp_var_index)
    # print_rows(pairs_cpp_new)
    # total_new = time() - st

    # pairs_count_new = _count_pairs(pairs_cpp_new)

    # print("total with index", total_new)
    # print("Speed: {}Mb/s".format(file_size // total_new))

    # print("New variant is {} times faster".format(int(total_old / total_new)))
    # print("Old found {} pairs, new found {} pairs".format(pairs_count_old, pairs_count_new))
    # print("With index found {} pairs".format(pairs_count_new))
    unique_pairs = _unique_pairs(pairs_cpp_new)
    # print("Unique pairs {}".format(len(unique_pairs)))

    # print_pairs(pairs_cpp_new)

    # del pairs_cpp_new
    # del np_array
    # gc.collect()

    return unique_pairs


def _drop_where_no_def_no_use(np_array, defs, uses):
    to_remove = set()
    for i, (ds, us) in enumerate(zip(defs, uses)):
        if len(ds) == 0 and len(us) == 0:
            to_remove.add(i)

    np_array = np.delete(np_array, list(to_remove), axis=0)

    defs = [ds for i, ds in enumerate(defs) if i not in to_remove]
    uses = [us for i, us in enumerate(uses) if i not in to_remove]

    return np_array, defs, uses


def _unique_pairs(bunch_rows):
    unique = set()
    for rows in bunch_rows:
        for r in rows:
            for pair in r.pairs:
                unique.add((pair.def_line, pair.use_line)) #, pair.var_name))
    return unique


def _count_pairs(bunch_rows):
    c = 0
    for rows in bunch_rows:
        for r in rows:
            c += len(r.pairs)
    return c


def cpp_pairs_new(np_array, defs, uses):
    t = np_array.T
    return def_use_pairs_ext.wrapper(
        t[0],
        t[1],
        t[2],
        t[3],
        t[4],
        defs,
        uses
    )


def cpp_pairs_w_index(np_array, cppvi):
    t = np_array.T
    return def_use_pairs_ext.findPairsIndex(
        t[0],
        t[1],
        t[2],
        t[3],
        t[4],
        cppvi
    )


def print_rows(rows_grouped):
    for group in rows_grouped:
        print("New scope")
        for row in group:
            # print(row)
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
