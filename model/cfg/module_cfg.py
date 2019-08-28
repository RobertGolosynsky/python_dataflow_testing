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

        self.intramethod_pairs = self._calculate_intra_method()
        self.intermethod_pairs = self._calculate_intermethod()
        self.interclass_pairs = self._calculate_interclass()

        self.branches = set()
        for cls_cfg in self.class_cfgs.values():
            for func_cfg in cls_cfg.methods.values():
                self.branches |= func_cfg.branches

        for func_cfg in self.function_cfgs.values():
            self.branches |= func_cfg.branches

    def _calculate_interclass(self):
        interclass_pairs = set()
        for name, cls_cfg in self.class_cfgs.items():
            interclass_pairs.update(cls_cfg.interclass_pairs)
        return interclass_pairs

    def _calculate_intermethod(self):
        total_intermethod_pairs = set()

        for name, cls_cfg in self.class_cfgs.items():
            total_intermethod_pairs.update(cls_cfg.intermethod_pairs)
        return total_intermethod_pairs

    def _calculate_intra_method(self):
        total_intramethod_pairs = set()
        for name, cls_cfg in self.class_cfgs.items():
            total_intramethod_pairs.update(cls_cfg.intramethod_pairs)
        for name, function_cfg in self.function_cfgs.items():
            total_intramethod_pairs.update(function_cfg.pairs)
        return total_intramethod_pairs

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

    def walk(self):
        for fname, cfg in self.function_cfgs.items():
            yield fname, cfg
        for cls_cfg in self.class_cfgs.values():
            for fname, func_cfg in cls_cfg.methods.items():
                yield fname, func_cfg
