import dataflow.def_use as du
import dataflow.reaching_definitions as rd

from loguru import logger

from dataflow.c_and_p_uses import get_all_c_all_p_uses
from util.astroid_util import Function


class FunctionCFG:
    def __init__(
            self, cfg, pairs, line_start, line_end, filter_self=True,
            c_uses=frozenset(),
            p_uses=frozenset()
    ):
        self.cfg = cfg
        self.extended_cfg = None
        self.pairs = pairs
        self.c_uses = c_uses
        self.p_uses = p_uses
        self.line_start = line_start
        self.line_end = line_end
        self.definitions, self.uses = self.cfg.collect_definitions_and_uses(filter_self=filter_self)

    @staticmethod
    def create(function: Function, calls=None, filter_self=True):
        cfg = du.try_create_cfg_with_definitions_and_uses(
            function.func,
            definition_line=function.first_line,
            args=function.argument_names
        )
        if not cfg:
            logger.warning("Could not create cfg for function {f}", f=function.func.__name__)
            return None
        if calls:
            cfg.expose_call_sites(calls)
        pairs = rd.definition_use_pairs(cfg.g)
        c_uses, p_uses = get_all_c_all_p_uses(function.tree)
        m = FunctionCFG(cfg=cfg,
                        pairs=pairs,
                        c_uses=c_uses,
                        p_uses=p_uses,
                        line_start=function.first_line,
                        line_end=function.end_line,
                        filter_self=filter_self)
        return m

    def extend_cfg(self, simple_method_cfgs):
        self.extended_cfg = self.cfg.extended(simple_method_cfgs)

    def get_variables(self, line):
        if line < self.line_start:
            return None
        if self.line_end:
            if line >= self.line_end:
                return None
        defs = self.definitions[line]
        uses = self.uses[line]

        return defs, uses
