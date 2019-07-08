import dataflow.def_use as du


class MethodCFG:
    def __init__(self, method_object, m_type):
        self.cfg = du.try_create_cfg_with_definitions_and_uses(method_object)
        self.m_type = m_type
