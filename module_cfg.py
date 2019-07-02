import def_use
import reflection
import ctrl_flow
import new_def_use
import networkx as nx

from draw import draw


class ClassCFG(object):

    def __init__(self, cls_object, class_name, class_):
        self.class_name = class_name
        self.class_ = class_
        self.trees = {}
        for fn_name, fn_descriptor in reflection.class_functions(self.class_):
            if reflection.method_type(self.class_, fn_name) == "inherited" \
                    and fn_name.startswith("__"):
                continue
            # name = class_name + "." + fn_name
            method_obj = getattr(cls_object, fn_name)
            byte_code_cfg = ctrl_flow.create_cfg(method_obj, class_name + "." + fn_name)
            line_cfg = ctrl_flow.to_line_cfg(byte_code_cfg)
            nx.set_node_attributes(line_cfg, class_name + "." + fn_name, ctrl_flow.scope_key)
            self.trees[fn_name] = new_def_use.LineTree(line_cfg)

    def _tree_for_line(self, line_num):
        for method_name in self.trees:
            tree = self.trees[method_name]
            if line_num in tree.g.nodes:
                return tree
        return None

    def defs_at(self, line_num: str):
        tree = self._tree_for_line(line_num)
        if tree:
            return tree.get_definitions(line_num)
        return []

    def uses_at(self, line_num: str):
        tree = self._tree_for_line(line_num)
        if tree:
            return tree.get_uses(line_num)
        return []

    def as_one(self):
        g = nx.MultiDiGraph()
        for cfg_name, tree in self.trees.items():
            g = nx.union(g, tree.g)  # , rename=("", cfg_name))
        return g

    def def_use(self):
        class_level_pairs = []
        method_level_pairs = []
        """
            self = id_ -> self.a -> 120383498.a - unique scope for class vars
            local variable -> create scope = random_scope -> a = 3 -> func_name_393948493.a
        """
        for cfg_name1, tree1 in self.trees.items():
            local_pairs = new_def_use.definition_use_pairs(tree1)
            method_level_pairs.extend(local_pairs)
            for cfg_name2, tree2 in self.trees.items():
                if not tree1 == tree2:  # TODO fix if the same cfgs
                    two = ctrl_flow.merge_cfgs(
                        [tree1.g, tree2.g],
                        [cfg_name1, cfg_name2],
                        # local_scope=[]
                    )
                    line_tree = new_def_use.LineTree(two)
                    ps = new_def_use.definition_use_pairs(line_tree)
                    # print(ps)
                    class_level_pairs.extend(ps)
                # print(two.nodes)
                # draw(two, extra_edges=[(x.line, y.line) for x, y in ps])
        return class_level_pairs + method_level_pairs


class ModuleCFG(object):
    def __init__(self, module_path):
        module = reflection.load_module(module_path, "amodule")

        self.function_trees = {}

        self.class_cfgs = []
        self.module_function_names = [name for name, _ in reflection.module_functions(module)]
        self.module = module

        for cls_name, cls in reflection.module_classes(module):
            self.class_cfgs.append(
                ClassCFG(
                    getattr(module, cls_name),
                    cls_name,
                    cls
                )
            )

        for function_name in self.module_function_names:
            function_obj = getattr(module, function_name)
            function_byte_cfg = ctrl_flow.create_cfg(function_obj, function_name)
            function_line_cfg = ctrl_flow.to_line_cfg(function_byte_cfg)
            nx.set_node_attributes(function_line_cfg, module.__name__ + "." + function_name, ctrl_flow.scope_key)
            self.function_trees[function_name] = new_def_use.LineTree(function_line_cfg)

    def defs_for_line(self, line_num: str):
        for class_cfg in self.class_cfgs:
            defs = class_cfg.defs_at(line_num)
            if len(defs) > 0:
                return defs

        for fn_name, tree in self.function_trees.items():
            if line_num in tree.g:
                defs = tree.get_definitions(line_num)
                if len(defs) > 0:
                    return defs
        return []

    def uses_for_line(self, line_num: str):
        for class_cfg in self.class_cfgs:
            uses = class_cfg.uses_at(line_num)
            if len(uses) > 0:
                return uses

        for fn_name, tree in self.function_trees.items():
            if line_num in tree.g:
                uses = tree.get_uses(line_num)
                if len(uses) > 0:
                    return uses
        return []

    def as_one(self):
        g = nx.MultiDiGraph()
        to_merge = [class_cfg.as_one() for class_cfg in self.class_cfgs]
        for func_name, func_tree in self.function_trees.items():
            to_merge.append(func_tree.g)
        for h in to_merge:
            g = nx.union(g, h)  # , rename=("", cfg_name))
        return g

    def def_use(self):
        """
            self = id_ -> self.a -> 120383498.a - unique scope for class vars
            local variable -> create scope = random_scope -> a = 3 -> func_name_393948493.a
        """

        pairs = []
        for class_cfg in self.class_cfgs:
            pairs.extend(class_cfg.def_use())

        for _, function_tree in self.function_trees.items():
            ps = new_def_use.definition_use_pairs(function_tree)
            pairs.extend(ps)
            # draw(two, extra_edges=[(x.line, y.line) for x, y in ps])
        return pairs
