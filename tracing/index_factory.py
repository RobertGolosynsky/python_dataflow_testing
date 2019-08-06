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
        pass

    @staticmethod
    def new_cpp_index(project_root, trace_root):
        vi = VarIndexFactory.new_py_index(project_root, trace_root)
        return CPPVariableIndex(vi.defs, vi.uses)
        pass

#
# class VarIndex:
#
#     @staticmethod
#     def create(project_root, traces_root):
#         return VarIndex(
#             read_du_index(project_root),
#             read_files_index(traces_root)
#         )
#
#     def __init__(self, variables_index_json, file_index_json):
#         self.variables_index = variables_index_json
#         self.file_index = file_index_json
#         self.mapping = {}
#
#     def get_vars_as_ints(self, file_idx, line, var_type):
#         var_names = self.get_vars_as_strings(file_idx, line, var_type)
#         if not var_names:
#             return np.zeros(0, dtype=int)
#
#         var_indexes = np.zeros(len(var_names), dtype=int)
#         for i, v in enumerate(var_names):
#             if v not in self.mapping:
#                 l = len(self.mapping)
#                 self.mapping[v] = l
#                 var_indexes[i] = l
#             else:
#                 var_indexes[i] = self.mapping[v]
#         return var_indexes
#
#     def get_vars_as_strings(self, file_idx, line, var_type):
#         file_name = self.file_index.get(file_idx, None)
#         if not file_name:
#             return []
#
#         modules = self.variables_index.get(var_type, None)
#         if not modules:
#             return []
#
#         module_vars = modules.get(file_name, None)
#         if not module_vars:
#             return []
#
#         return module_vars.get(line, [])
#
#     def get_vars(self, np_array, as_ints=False):
#         if as_ints:
#             get_vars_func = self.get_vars_as_ints
#         else:
#             get_vars_func = self.get_vars_as_strings
#
#         return [get_vars_func(r[1], r[2], "definitions") for r in np_array], \
#                [get_vars_func(r[1], r[2], "uses") for r in np_array]
#

class VarIndex:

    @staticmethod
    def create(project_root, traces_root):
        return VarIndex(
            read_du_index(project_root),
            read_files_index(traces_root)
        )

    def __init__(self, variables_index_json, file_index_json):
        self.index = self.as_int_index(variables_index_json, file_index_json)
        self.defs = self.index["definitions"]
        self.uses = self.index["uses"]
        self.mapping = {}

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

    @staticmethod
    def as_int(s, idx):
        as_int = idx.get(s, None)
        if as_int:
            return as_int
        else:
            idx[s] = len(idx)
        return len(idx) - 1

    @staticmethod
    def as_int_index(index, file_index):
        file_index = {v: k for k, v in file_index.items()}
        int_index = {}
        idx = {}
        for vtype in index:
            int_index[vtype] = {}
            for file in index[vtype]:
                file_key = file_index.get(file, -1)
                if file_key > -1:

                    int_index[vtype][file_key] = {}
                    for line in index[vtype][file]:
                        variables = index[vtype][file][line]
                        ints = [VarIndex.as_int(v, idx) for v in variables]
                        int_index[vtype][file_key][int(line)] = ints

        return int_index
