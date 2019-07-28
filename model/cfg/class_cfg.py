import dataflow.inter_class as ic
from itertools import product

from model.cfg.function_cfg import FunctionCFG


class ClassCFG(object):

    def __init__(self, class_name, methods):
        self.class_name = class_name

        self.methods = {}
        self.start_line = None
        self.end_line = None
        if methods:
            self.start_line = methods[0][1]
            self.end_line = 0

        for f in methods:
            st_line = f[1]
            end_line = f[3]
            if st_line < self.start_line:
                self.start_line = st_line
            if end_line and self.end_line:
                if self.end_line < end_line:
                    self.end_line = end_line
            if not end_line:
                self.end_line = None
            m_name = f[0].__name__
            m = FunctionCFG.create(*f)
            if m:
                self.methods[m_name] = m

        self.interclass_pairs = []
        self._calculate_interclass()

    def _calculate_interclass(self):

        without_init = {n: o for n, o in self.methods.items() if not n == "__init__"}
        self.interclass_pairs = []

        for (n1, m1), (n2, m2) in product(self.methods.items(), without_init.items()):
            pairs = ic.inter_class_def_use_pairs(m1.cfg, m2.cfg)
            self.interclass_pairs.extend(pairs)

    def get_variables(self, line):
        if line < self.start_line:
            return None
        if self.end_line:
            if line > self.end_line:
                return None
        for name, method_cfg in self.methods.items():
            variables = method_cfg.get_variables(line)
            if variables is not None:
                return variables
        return None

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
