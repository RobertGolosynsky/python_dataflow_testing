from collections import defaultdict

import dataflow.def_use as du
import dataflow.reaching_definitions as rd
import graphs.create as cr

from loguru import logger


class FunctionCFG:
    def __init__(self, cfg, pairs, line_start, line_end, filter_self=True):
        self.cfg = cfg
        self.pairs = pairs
        self.line_start = line_start
        self.line_end = line_end
        definitions, uses = self._collect_definitions_and_uses(filter_self=filter_self)
        self.definitions = definitions
        self.uses = uses

    @classmethod
    def create(cls, method_object, definition_line=None, args=None, line_end=None, filter_self=True):
        cfg = du.try_create_cfg_with_definitions_and_uses(
            method_object,
            definition_line=definition_line,
            args=args
        )
        if not cfg:
            logger.warning("Could not create cfg for function {f}", f=method_object.__name__)
            return None

        pairs = rd.definition_use_pairs(cfg)
        m = FunctionCFG(cfg, pairs, definition_line, line_end, filter_self=filter_self)
        return m

    def _collect_definitions_and_uses(self, filter_self=True):
        definitions = defaultdict(list)
        uses = defaultdict(list)
        for node, node_attrs in self.cfg.nodes(data=True):
            use = node_attrs.get(du.USE_KEY, None)
            definition = node_attrs.get(du.DEFINITION_KEY, None)
            line = node_attrs.get(cr.LINE_KEY, -1)
            if line > -1:
                if definition:
                    definitions[line].append(definition)
                if use:
                    uses[line].append(use)
        return definitions, uses

    def get_variables(self, line):
        if line < self.line_start:
            return None
        if self.line_end:
            if line >= self.line_end:
                return None
        defs = self.definitions[line]
        uses = self.uses[line]

        return defs, uses
