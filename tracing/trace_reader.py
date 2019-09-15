import json
import os

import pandas as pd
import numpy as np
from pathlib import Path

from loguru import logger
from pandas.errors import EmptyDataError

from tracing.string_to_int_index import StringToIntIndex
from tracing.tracer import Tracer


def _filename(file_index):
    return str(file_index) + os.path.extsep + Tracer.trace_file_ext


class TraceReader:
    def __init__(self, trace_root):
        if not isinstance(trace_root, Path):
            trace_root = Path(trace_root)
        self.trace_root = trace_root
        self.main_root = self.trace_root / Tracer.trace_folder

        self.files_mapping = self.read_files_mapping()
        self.folders_mapping = self.read_folders_mapping()

    def read_files_mapping(self) -> StringToIntIndex:
        return StringToIntIndex.load(self.main_root / Tracer.trace_index_file_name)

    def read_folders_mapping(self) -> StringToIntIndex:
        return StringToIntIndex.load(self.main_root / Tracer.folder_index_file_name)

    def read_failed_test_cases(self):
        path = self.main_root / Tracer.failed_test_cases_file
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def get_node_ids(self):
        return self.folders_mapping.keys()

    def get_traces_for(self, module_path, selected_node_ids=None):
        file_index = self.files_mapping.get_int(module_path)
        file_name = _filename(file_index)
        paths = []
        node_ids = []
        if not selected_node_ids:
            selected_node_ids = self.get_node_ids()

        for node_id in selected_node_ids:
            folder_id = self.folders_mapping.get_int(node_id)
            trace_file_path = self.main_root / str(folder_id) / file_name
            if trace_file_path.is_file():
                paths.append(trace_file_path)
                node_ids.append(node_id)

        return node_ids, paths

    def trace_path_to_tracee_index_and_node_id(self, s):
        trace_path = Path(s)
        test_case_folder_name = trace_path.parent.name
        node_id = self.folders_mapping.get_string(test_case_folder_name)
        tracee_index = int(trace_path.stem)
        return tracee_index, node_id

    def trace_path(self, node_id: str, module_under_test_path: str):
        folder_id = self.folders_mapping.get_int(node_id)
        file_id = self.files_mapping.get_int(module_under_test_path)
        return self.main_root/str(folder_id)/(str(file_id)+os.extsep+Tracer.trace_file_ext)


def read_df(f, cut=-1, max_size_mb=None):
    logger.debug("Reading trace {f}", f=f)
    file_size = os.stat(f).st_size // (1024 * 1024)
    if max_size_mb and file_size > max_size_mb:
        return None, file_size
    np_array = pd.read_csv(
        f,
        header=None,
        delimiter=",",
        # dtype={
        #     # IDX_INDEX: "int64",
        #     FILE_INDEX: "int16",
        #     LINE_INDEX: "int16",
        #     SELF_INDEX: "int",
        #     SCOPE_INDEX: "int64"
        # },
        low_memory=True
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
    if not scopes_file_path.is_file():
        return None
    try:
        np_array = pd.read_csv(
            scopes_file_path,
            header=None,
            delimiter=",",
            dtype=int  # TODO: optimize
        ).values
    except EmptyDataError as e:
        logger.warning("Scopes file appears to be empty")
        return dict()
    return dict(np_array)
