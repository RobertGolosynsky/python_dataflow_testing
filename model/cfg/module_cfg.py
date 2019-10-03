from typing import Generator, Tuple

from model.cfg.class_cfg import ClassCFG, only_lines
from model.cfg.function_cfg import FunctionCFG
import util.astroid_util as au
from loguru import logger


class ModuleCFG(object):
    def __init__(self, module_path):
        logger.debug("Creating module cfg for module {m}", m=module_path)
        self.module_path = module_path
        self.function_cfgs = {}
        self.class_cfgs = {}
        self.is_full_cfg = True
        fns, clss, calls = au.compile_module(module_path)

        self.definitions = {}
        self.uses = {}
        logger.debug("Adding classes of the module")
        for cls_name, methods in clss.items():
            cls_cfg = ClassCFG(cls_name, methods, calls)
            self.class_cfgs[cls_name] = cls_cfg

            self.definitions.update(cls_cfg.definitions)
            self.uses.update(cls_cfg.uses)
        logger.debug("Adding functions of the module")
        for f in fns:
            fn_name = f.func.__name__
            func_cfg = FunctionCFG.create(f)
            if func_cfg:
                self.function_cfgs[fn_name] = func_cfg
                self.definitions.update(func_cfg.definitions)
                self.uses.update(func_cfg.uses)
            else:
                self.is_full_cfg = False
        self.intramethod_pairs = self._calculate_intra_method()
        self.intermethod_pairs = self._calculate_intermethod()
        self.interclass_pairs = self._calculate_interclass()
        self.c_uses, self.p_uses = self._calculate_all_c_all_p_uses()

        logger.debug("Finding branching points of the module")
        from coverage_metrics.branch_coverage import find_branches
        self.branches = find_branches(module_path)

        logger.debug("Done creating module cfg for module {m}", m=self.module_path)

    def _calculate_interclass(self):
        logger.debug("Finding inter class pairs in module {m}", m=self.module_path)
        interclass_pairs = set()
        for name, cls_cfg in self.class_cfgs.items():
            interclass_pairs.update(cls_cfg.interclass_pairs)
        return interclass_pairs

    def _calculate_intermethod(self):
        logger.debug("Finding inter method pairs in module {m}", m=self.module_path)
        total_intermethod_pairs = set()

        for name, cls_cfg in self.class_cfgs.items():
            total_intermethod_pairs.update(cls_cfg.intermethod_pairs)
        return total_intermethod_pairs

    def _calculate_intra_method(self):
        logger.debug("Finding intra method pairs in module {m}", m=self.module_path)
        total_intramethod_pairs = set()
        for name, cls_cfg in self.class_cfgs.items():
            total_intramethod_pairs.update(cls_cfg.intramethod_pairs)
        for name, function_cfg in self.function_cfgs.items():
            total_intramethod_pairs.update(only_lines(function_cfg.pairs))
        return total_intramethod_pairs

    def _calculate_all_c_all_p_uses(self):
        all_c = set()
        all_p = set()
        for name, function in self.walk():
            all_c |= function.c_uses
            all_p |= function.p_uses

        return all_p, all_p

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

    def walk(self) -> Generator[Tuple[str, FunctionCFG], None, None]:
        for fname, cfg in self.function_cfgs.items():
            yield fname, cfg
        for cls_cfg in self.class_cfgs.values():
            for fname, func_cfg in cls_cfg.methods.items():
                yield fname, func_cfg
