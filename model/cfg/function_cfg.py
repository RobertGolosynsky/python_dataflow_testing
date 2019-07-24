import dataflow.def_use as du
import dataflow.reaching_definitions as rd


class FunctionCFG:
    def __init__(self, cfg, pairs):
        self.cfg = cfg
        self.pairs = pairs

    @classmethod
    def create(cls, method_object, definition_line=None, args=None):
        cfg = du.try_create_cfg_with_definitions_and_uses(method_object, definition_line=definition_line, args=args)
        if not cfg:
            print("Could not create cfg for", method_object)
            return None

        pairs = rd.definition_use_pairs(cfg)
        m = FunctionCFG(cfg, pairs)
        return m
