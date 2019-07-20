import dataflow.def_use as du
import dataflow.reaching_definitions as rd


class MethodCFG:
    def __init__(self, cfg, m_type, pairs):
        self.cfg = cfg
        self.m_type = m_type
        self.pairs = pairs

    @classmethod
    def create(cls, method_object, m_type):
        cfg = du.try_create_cfg_with_definitions_and_uses(method_object)
        if not cfg:
            print("Could not create cfg for", method_object)
            return None

        pairs = rd.definition_use_pairs(cfg)
        m = MethodCFG(cfg, m_type, pairs)
        return m
