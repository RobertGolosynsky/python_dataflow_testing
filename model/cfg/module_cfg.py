from model.cfg.class_cfg import ClassCFG
from model.cfg.function_cfg import FunctionCFG
from util import reflection


class ModuleCFG(object):
    def __init__(self, module_path):
        module = reflection.try_load_module(module_path)

        self.function_cfgs = {}

        self.class_cfgs = {}

        for cls_name, class_descriptor in reflection.module_classes(module):
            self.class_cfgs[cls_name] = (
                ClassCFG(
                    getattr(module, cls_name),
                    cls_name,
                    class_descriptor
                )
            )

        for function_name in reflection.module_functions(module):
            func_object = getattr(module, function_name)
            self.function_cfgs[function_name] = FunctionCFG(func_object)

            # def defs_for_line(self, line_num: str):
    #     for class_cfg in self.class_cfgs:
    #         defs = class_cfg.defs_at(line_num)
    #         if len(defs) > 0:
    #             return defs
    #
    #     for fn_name, tree in self.function_trees.items():
    #         if line_num in tree.g:
    #             defs = tree.get_definitions(line_num)
    #             if len(defs) > 0:
    #                 return defs
    #     return []
    #
    # def uses_for_line(self, line_num: str):
    #     for class_cfg in self.class_cfgs:
    #         uses = class_cfg.uses_at(line_num)
    #         if len(uses) > 0:
    #             return uses
    #
    #     for fn_name, tree in self.function_trees.items():
    #         if line_num in tree.g:
    #             uses = tree.get_uses(line_num)
    #             if len(uses) > 0:
    #                 return uses
    #     return []
    #
    # def as_one(self):
    #     g = nx.MultiDiGraph()
    #     to_merge = [class_cfg.as_one() for class_cfg in self.class_cfgs]
    #     for func_name, func_tree in self.function_trees.items():
    #         to_merge.append(func_tree.g)
    #     for h in to_merge:
    #         g = nx.union(g, h)  # , rename=("", cfg_name))
    #     return g
    #
    # def def_use(self):
    #     """
    #         self = id_ -> self.a -> 120383498.a - unique scope for class vars
    #         local variable -> create scope = random_scope -> a = 3 -> func_name_393948493.a
    #     """
    #
    #     pairs = []
    #     for class_cfg in self.class_cfgs:
    #         pairs.extend(class_cfg.def_use())
    #
    #     for _, function_tree in self.function_trees.items():
    #         ps = new_def_use.definition_use_pairs(function_tree)
    #         pairs.extend(ps)
    #         # draw(two, extra_edges=[(x.line, y.line) for x, y in ps])
    #     return pairs
