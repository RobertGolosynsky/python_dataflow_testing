import json
import os

import pandas as pd
import numpy as np
from pathlib import Path

from model.test_case import TestCase
from tracing.tracer import Tracer


def get_trace_files(root, suffix=Tracer.trace_file_ext, trace_name=None, file_index=None):
    trace_files = []
    for dirpath, dnames, fnames in os.walk(root):
        if trace_name is None or dirpath.endswith(trace_name):
            for f in fnames:
                if f.endswith(suffix):
                    if file_index is None:
                        trace_files.append(os.path.join(dirpath, f))
                    elif f.endswith(str(file_index) + "." + suffix):
                        return os.path.join(dirpath, f)
    if file_index:
        return None
    else:
        return trace_files


def read_files_index(trace_root):
    path = os.path.join(trace_root, Tracer.trace_folder, Tracer.files_index_file)
    with open(path) as f:
        file_dict = json.load(f)
        return {int(k): v for k, v in file_dict.items()}


def read_df(f, cut=-1):
    file_size = os.stat(f).st_size // (1024 * 1024)
    np_array = pd.read_csv(
        f,
        header=None,
        delimiter=",",
        dtype=int  # TODO: optimize
    ).values

    prev_len = len(np_array)
    new_len = prev_len
    if cut > -1:
        np_array = np_array[:cut]
        new_len = len(np_array)
    np_array = np.column_stack((np.arange(np_array.shape[0]), np_array))

    return np_array, file_size // (prev_len / new_len)


def read_scopes_for_trace_file(trace_file_path):
    p = Path(trace_file_path)
    parent = p.parent
    file_name_w_o_suffix = p.stem

    scopes_file_path = parent / (file_name_w_o_suffix + "." + Tracer.scopes_file_ext)
    np_array = pd.read_csv(
        scopes_file_path,
        header=None,
        delimiter=",",
        dtype=int  # TODO: optimize
    ).values

    return dict(np_array)


def get_test_cases(trace_root):
    path = os.path.join(trace_root, Tracer.trace_folder)
    print("asdasdasd", path)
    return next(os.walk(path))[1]


def get_traces_of_file(trace_root, file_index):
    file_name = str(file_index) + os.path.extsep + Tracer.trace_file_ext
    root = Path(trace_root) / Tracer.trace_folder
    paths = []
    for test_case in get_test_cases(trace_root):
        trace_file_path = root / test_case / file_name
        if trace_file_path.is_file():
            paths.append((test_case, trace_file_path))
    return paths


def trace_path_to_tracee_index_and_test_case(s):
    trace_path = Path(s)
    test_case_folder_name = trace_path.parent.name
    test_case = TestCase.from_folder_name(test_case_folder_name)
    tracee_index = int(trace_path.stem)
    return tracee_index, test_case
