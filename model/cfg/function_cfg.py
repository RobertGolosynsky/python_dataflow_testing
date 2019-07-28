import dataflow.def_use as du
import graphs.create as gc
import dataflow.reaching_definitions as rd
import graphs.util as gu


class FunctionCFG:
    def __init__(self, cfg, pairs, line_start, line_end):
        self.cfg = cfg
        self.pairs = pairs
        self.line_start = line_start
        self.line_end = line_end

    @classmethod
    def create(cls, method_object, definition_line=None, args=None, line_end=None):
        cfg = du.try_create_cfg_with_definitions_and_uses(method_object, definition_line=definition_line, args=args)
        if not cfg:
            print("Could not create cfg for", method_object)
            return None

        pairs = rd.definition_use_pairs(cfg)
        m = FunctionCFG(cfg, pairs, definition_line, line_end)
        return m

    def get_variables(self, line):
        if line < self.line_start:
            return None
        if self.line_end:
            if line >= self.line_end:
                return None
        defs = []
        uses = []
        found = False
        for node, data in gu.nodes_where(self.cfg, gc.LINE_KEY, line):
            found = True
            deff = data.get(du.DEFINITION_KEY)
            use = data.get(du.USE_KEY)
            if deff:
                defs.append(deff)
            if use:
                uses.append(use)
        if not found:
            return None
        return defs, uses