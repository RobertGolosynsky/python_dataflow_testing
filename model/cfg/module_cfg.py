from model.cfg.class_cfg import ClassCFG
from model.cfg.function_cfg import FunctionCFG
import util.astroid_util as au


class ModuleCFG(object):
    def __init__(self, module_path):
        self.module_path = module_path
        self.function_cfgs = {}
        self.class_cfgs = {}

        fns, clss, calls = au.compile_module(module_path)

        self.definitions = {}
        self.uses = {}

        for cls_name, methods in clss.items():
            cls_cfg = ClassCFG(cls_name, methods, calls)
            self.class_cfgs[cls_name] = cls_cfg

            self.definitions.update(cls_cfg.definitions)
            self.uses.update(cls_cfg.uses)

        for f in fns:
            fn_name = f.func.__name__
            func_cfg = FunctionCFG.create(f)
            if func_cfg:
                self.function_cfgs[fn_name] = func_cfg
                self.definitions.update(func_cfg.definitions)
                self.uses.update(func_cfg.uses)

    def get_variables(self, line):

        for func_cfg in self.function_cfgs:
            variables = self.function_cfgs[func_cfg].get_variables(line)
            if variables is not None:
                return variables

        for cls_cfg in self.class_cfgs:
            variables = self.class_cfgs[cls_cfg].get_variables(line)
            if variables is not None:
                return variables
        return None
