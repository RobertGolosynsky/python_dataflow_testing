from collections import defaultdict
from typing import List

import dataflow.inter_class as ic
from itertools import product

from model.cfg.function_cfg import FunctionCFG

# import graphs.super_cfg as sg
from util.astroid_util import Function


class ClassCFG(object):

    def __init__(self, class_name, methods: List[Function], calls):
        self.class_name = class_name

        self.call_dict = defaultdict(list)
        for line, idx, fname in calls:
            self.call_dict[line].append((idx, fname))

        self.methods = {}
        self.start_line = None
        self.end_line = None

        if methods:
            self.start_line = methods[0].first_line
            self.end_line = 0

        for f in methods:
            if f.first_line < self.start_line:
                self.start_line = f.first_line
            if f.end_line and self.end_line:
                if self.end_line < f.end_line:
                    self.end_line = f.end_line
            if not f.end_line:
                self.end_line = None
            m_name = f.func.__name__
            m = FunctionCFG.create(f)
            if m:
                self.methods[m_name] = m

        # self.super_cfg = sg.create_super_cfg(self.methods)

        self.interclass_pairs = self._calculate_interclass()
        self.intermethod_pairs = self._calculate_intermethod()
        self._calculate_interclass()
        self.definitions = {}
        self.uses = {}
        for _, f_cfg in self.methods.items():
            self.definitions.update(f_cfg.definitions)
            self.uses.update(f_cfg.uses)

    def _calculate_interclass(self):

        without_init = {n: o for n, o in self.methods.items() if not n == "__init__"}
        interclass_pairs = []

        for (n1, m1), (n2, m2) in product(self.methods.items(), without_init.items()):
            pairs = ic.inter_class_def_use_pairs(m1.cfg.g, m2.cfg.g)
            interclass_pairs.extend(pairs)

        return interclass_pairs

    def _calculate_intermethod(self):
        return []

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
