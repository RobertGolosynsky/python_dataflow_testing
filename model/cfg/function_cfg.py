from collections import defaultdict

import dataflow.def_use as du
import dataflow.reaching_definitions as rd
import graphs.create as cr

from loguru import logger

from util.astroid_util import Function


class FunctionCFG:
    def __init__(self, cfg, pairs, line_start, line_end, filter_self=True):
        self.cfg = cfg
        self.pairs = pairs
        self.line_start = line_start
        self.line_end = line_end
        definitions, uses = self.cfg.collect_definitions_and_uses(filter_self=filter_self)
        self.definitions = definitions
        self.uses = uses

    @staticmethod
    def create(function: Function, filter_self=True):
        cfg = du.try_create_cfg_with_definitions_and_uses(
            function.func,
            definition_line=function.first_line,
            args=function.argument_names
        )
        if not cfg:
            logger.warning("Could not create cfg for function {f}", f=function.func.__name__)
            return None

        pairs = rd.definition_use_pairs(cfg.g)
        m = FunctionCFG(cfg, pairs, function.first_line, function.end_line, filter_self=filter_self)
        return m

    def get_variables(self, line):
        if line < self.line_start:
            return None
        if self.line_end:
            if line >= self.line_end:
                return None
        defs = self.definitions[line]
        uses = self.uses[line]

        return defs, uses
