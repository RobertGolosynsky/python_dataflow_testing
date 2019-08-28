from pprint import pprint

from cpp.cpp_import import load_cpp_extension
from model.cfg.project_cfg import read_du_index
from tracing.trace_reader import read_files_index
import numpy as np

cpp_def_use = load_cpp_extension("def_use_pairs_ext")
CPPVariableIndex = cpp_def_use.VariableIndex


class VarIndexFactory:
    @staticmethod
    def new_py_index(project_root, trace_root):
        return VarIndex.create(project_root, trace_root)

    @staticmethod
    def new_cpp_index(project_root, trace_root):
        vi = VarIndexFactory.new_py_index(project_root, trace_root)
        return CPPVariableIndex(vi.defs, vi.uses)


class VarToInt:

    def __init__(self):
        self.idx = {}
        self.local_var_counter = 0
        self.object_var_counter = 1

    def as_int(self, var_name):
        as_int = self.idx.get(var_name, None)
        if as_int:
            return as_int
        else:
            if var_name.startswith("self."):
                self.object_var_counter += 2
                self.idx[var_name] = self.object_var_counter
                return self.object_var_counter
            else:
                self.local_var_counter += 2
                self.idx[var_name] = self.local_var_counter
                return self.local_var_counter


class VarIndex:

    @staticmethod
    def create(project_root, traces_root):
        return VarIndex(
            read_du_index(project_root),
            read_files_index(traces_root)
        )

    def __init__(self, variables_index_json, file_index_json):
        self.var_to_int = VarToInt()
        self.index = self.as_int_index(variables_index_json, file_index_json)
        self.defs = self.index["definitions"]
        self.uses = self.index["uses"]

    def get_object_vars(self, np_array):
        defs = []
        uses = []
        for r in np_array:
            file, line = r[1], r[2]
            defs_on_line = []
            uses_on_line = []

            d = self.defs.get(file, None)

            if d:
                for var_name in d.get(line, []):
                    if var_name % 2 == 1:
                        defs_on_line.append(var_name)
            defs.append(defs_on_line)

            u = self.uses.get(file, None)
            if u:
                for var_name in u.get(line, []):
                    if var_name % 2 == 1:
                        uses_on_line.append(var_name)
            uses.append(uses_on_line)

        return defs, uses

    def get_vars(self, np_array):
        defs = []
        uses = []
        for r in np_array:
            file, line = r[1], r[2]
            d = self.defs.get(file, None)
            if d:
                defs.append(d.get(line, []))
            u = self.uses.get(file, None)
            if u:
                uses.append(u.get(line, []))

        return defs, uses

    def as_int_index(self, index, file_index):
        file_index = {v: k for k, v in file_index.items()}
        int_index = {}
        for vtype in index:
            int_index[vtype] = {}
            for file in index[vtype]:
                file_key = file_index.get(file, -1)
                if file_key > -1:

                    int_index[vtype][file_key] = {}
                    for line in index[vtype][file]:
                        variables = index[vtype][file][line]
                        ints = [self.var_to_int.as_int(v) for v in variables]
                        int_index[vtype][file_key][int(line)] = ints

        return int_index
