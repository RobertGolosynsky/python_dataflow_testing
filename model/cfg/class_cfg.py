from collections import defaultdict
from typing import List

import dataflow.inter_class as ic
import dataflow.reaching_definitions as rd
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
            m = FunctionCFG.create(f, calls=calls)
            if m:
                self.methods[m_name] = m
        simple_method_cfgs = {m_name: function_cfg.cfg for m_name, function_cfg in self.methods.items()}
        for function_cfg in self.methods.values():
            function_cfg.extend_cfg(simple_method_cfgs)
        # self.super_cfg = sg.create_super_cfg(self.methods)

        self.intramethod_pairs = self._calculate_intra_method()
        self.intermethod_pairs = self._calculate_intermethod()
        self.interclass_pairs = self._calculate_interclass()

        self.definitions = {}
        self.uses = {}

        for _, f_cfg in self.methods.items():
            self.definitions.update(f_cfg.definitions)
            self.uses.update(f_cfg.uses)

    def _calculate_interclass(self):
        without_init = {n: o for n, o in self.methods.items() if not n.startswith("_")}
        public_methods = without_init.copy()
        if "__init__" in self.methods:
            public_methods["__init__"] = self.methods["__init__"]
        interclass_pairs = set()

        for (n1, m1), (n2, m2) in product(public_methods.items(), without_init.items()):
            pairs = ic.inter_class_def_use_pairs_cfg(m1.extended_cfg, m2.extended_cfg)
            interclass_pairs.update(only_lines(pairs))

        return interclass_pairs

    def _calculate_intermethod(self):
        total_intermethod_pairs = set()
        for name, method_cfg in self.methods.items():
            intermethod_pairs = rd.definition_use_pairs(
                method_cfg.extended_cfg.g,
                intermethod_only=True,
                object_vars_only=True
            )
            total_intermethod_pairs.update(only_lines(intermethod_pairs))
        return total_intermethod_pairs

    def _calculate_intra_method(self):
        total_intramethod_pairs = set()
        for name, method_cfg in self.methods.items():
            intramethod_pairs = rd.definition_use_pairs(method_cfg.cfg.g)
            total_intramethod_pairs.update(only_lines(intramethod_pairs))
        return total_intramethod_pairs

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


def only_lines(s):
    return {(pair.definition.line, pair.use.line) for pair in s}
