import dataflow.inter_class as ic
from itertools import product

from model.cfg.function_cfg import FunctionCFG


class ClassCFG(object):

    def __init__(self, class_name, methods):
        self.class_name = class_name

        self.methods = {}
        self.start_line = None
        self.end_line = None
        if methods:
            self.start_line = methods[0][1]
            self.end_line = 0

        for f in methods:
            st_line = f[1]
            end_line = f[3]
            if st_line < self.start_line:
                self.start_line = st_line
            if end_line and self.end_line:
                if self.end_line < end_line:
                    self.end_line = end_line
            if not end_line:
                self.end_line = None
            m_name = f[0].__name__
            m = FunctionCFG.create(*f)
            if m:
                self.methods[m_name] = m

        self.interclass_pairs = []
        self._calculate_interclass()
        self.definitions = {}
        self.uses = {}
        for _, f_cfg in self.methods.items():
            self.definitions.update(f_cfg.definitions)
            self.uses.update(f_cfg.uses)

    def _calculate_interclass(self):

        without_init = {n: o for n, o in self.methods.items() if not n == "__init__"}
        self.interclass_pairs = []

        for (n1, m1), (n2, m2) in product(self.methods.items(), without_init.items()):
            pairs = ic.inter_class_def_use_pairs(m1.cfg, m2.cfg)
            self.interclass_pairs.extend(pairs)

    def get_variables(self, line):
        if line < self.start_line:
            return None
        if self.end_line:
            if line > self.end_line:
                return None
        for name, method_cfg in self.methods.items():
            variables = method_cfg.get_variables(line)
            if variables is not None:
                return variables
        return None
