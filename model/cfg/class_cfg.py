from model.cfg.method_cfg import MethodCFG
from util import reflection
import dataflow.inter_class as ic
from itertools import product


class ClassCFG(object):

    def __init__(self, cls_object, class_name, class_descriptor):
        self.class_name = class_name
        self.class_descriptor = class_descriptor

        self.defined_methods = {}

        for defined_method in reflection.class_functions(cls_object, m_type=reflection.DEFINED):
            method_obj = getattr(cls_object, defined_method)
            m = MethodCFG.create(method_obj, reflection.DEFINED)
            if m:
                self.defined_methods[defined_method] = m

        self.overridden_methods = {}

        for overridden_method in reflection.class_functions(cls_object, m_type=reflection.OVERRIDDEN):
            method_obj = getattr(cls_object, overridden_method)
            m = MethodCFG.create(method_obj, reflection.OVERRIDDEN)
            if m:
                self.overridden_methods[overridden_method] = m

        self.inherited_methods = {}

        for inherited_method in reflection.class_functions(cls_object, m_type=reflection.INHERITED):
            method_obj = getattr(cls_object, inherited_method)
            m = MethodCFG.create(method_obj, reflection.INHERITED)
            if m:
                self.inherited_methods[inherited_method] = m

        self.interclass_pairs = []
        self.interclass_pairs_inherited = []

        self._calculate_interclass()
        self._calculate_inherited_interclass()

    def local_methods(self):
        methods = {**self.defined_methods, **self.overridden_methods}
        return methods

    def _calculate_interclass(self):
        local = self.local_methods()
        without_init = {n: o for n, o in self.local_methods().items() if not n == "__init__"}
        self.interclass_pairs = []

        for (n1, m1), (n2, m2) in product(local.items(), without_init.items()):
            pairs = ic.inter_class_def_use_pairs(m1.cfg, m2.cfg)
            self.interclass_pairs.extend(pairs)

    def _calculate_inherited_interclass(self):
        local = self.local_methods()
        inherited = self.inherited_methods
        self.interclass_pairs = []

        for (n1, m1), (n1, m2) in product(local.items(), inherited.items()):
            pairs = ic.inter_class_def_use_pairs(m1.cfg, m2.cfg)
            self.interclass_pairs.extend(pairs)

        for (n1, m1), (n1, m2) in product(inherited.items(), local.items()):
            pairs = ic.inter_class_def_use_pairs(m1.cfg, m2.cfg)
            self.interclass_pairs.extend(pairs)

    #
    #
    # def _tree_for_line(self, line_num):
    #     for method_name in self.trees:
    #         tree = self.trees[method_name]
    #         if line_num in tree.g.nodes:
    #             return tree
    #     return None
    #
    # def defs_at(self, line_num: str):
    #     tree = self._tree_for_line(line_num)
    #     if tree:
    #         return tree.get_definitions(line_num)
    #     return []
    #
    # def uses_at(self, line_num: str):
    #     tree = self._tree_for_line(line_num)
    #     if tree:
    #         return tree.get_uses(line_num)
    #     return []
    #
    # def as_one(self):
    #     g = nx.MultiDiGraph()
    #     for cfg_name, tree in self.trees.items():
    #         g = nx.union(g, tree.g)  # , rename=("", cfg_name))
    #     return g
    #
    # def def_use(self):
    #     class_level_pairs = []
    #     method_level_pairs = []
    #     """
    #         self = id_ -> self.a -> 120383498.a - unique scope for class vars
    #         local variable -> create scope = random_scope -> a = 3 -> func_name_393948493.a
    #     """
    #     for cfg_name1, tree1 in self.trees.items():
    #         local_pairs = new_def_use.definition_use_pairs(tree1)
    #         method_level_pairs.extend(local_pairs)
    #         for cfg_name2, tree2 in self.trees.items():
    #             if not tree1 == tree2:  # TODO fix if the same cfgs
    #                 two = ctrl_flow.merge_cfgs(
    #                     [tree1.g, tree2.g],
    #                     [cfg_name1, cfg_name2],
    #                     # local_scope=[]
    #                 )
    #                 line_tree = new_def_use.LineTree(two)
    #                 ps = new_def_use.definition_use_pairs(line_tree)
    #                 # print(ps)
    #                 class_level_pairs.extend(ps)
    #             # print(two.nodes)
    #             # draw(two, extra_edges=[(x.line, y.line) for x, y in ps])
    #     return class_level_pairs + method_level_pairs
