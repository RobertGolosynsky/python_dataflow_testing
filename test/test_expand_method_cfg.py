import os
import unittest
from itertools import chain
from pathlib import Path
from model.cfg.module_cfg import ModuleCFG

here = Path(os.path.realpath(__file__)).parent
this_project_root = here.parent

inter_method_root = this_project_root / "dataset/inter_method"
inter_method = inter_method_root / "module.py"


class TestExpandMethodCFG(unittest.TestCase):

    def setUp(self) -> None:
        module = str(inter_method)
        self.module_cfg = ModuleCFG(module)
        self.cls_cfg = self.module_cfg.class_cfgs["HasIntermethod"]

    def test_expand_method_with_no_calls_returns_same_cfg(self):
        method_cfg = self.cls_cfg.methods["y"]
        nodes = set(method_cfg.cfg.g.nodes)
        extended_nodes = set(method_cfg.extended_cfg.g.nodes)
        self.assertEqual(nodes, extended_nodes)

        # pairs = definition_use_pairs(method_cfg.extended_cfg.g)
        # print(pairs)
        # gd.draw_byte_cfg_dot(method_cfg.extended_cfg.g, [], None)

    def test_expand_method_cfg_with_one_call_return_expanded_cfg(self):
        method_cfg = self.cls_cfg.methods["x"]
        callee_method_cfg = self.cls_cfg.methods["y"]
        callee_nodes = callee_method_cfg.cfg.g.nodes
        nodes = method_cfg.cfg.g.nodes
        extended_nodes = method_cfg.extended_cfg.g.nodes
        self.assertEqual(set().union(*[nodes,callee_nodes]), set(extended_nodes))

    def test_expand_method_cfg_with_recursive_calls_return_same_cfg(self):
        method_cfg = self.cls_cfg.methods["recursive"]
        nodes = method_cfg.cfg.g.nodes
        extended_nodes = method_cfg.extended_cfg.g.nodes
        self.assertEqual(set(nodes), set(extended_nodes))

    def test_expand_method_cfg_with_expanding_callee_calls_return_cfg_with_all_called_functions(self):
        call_sequence = ["f1", "f2", "f3"]
        method_cfg = self.cls_cfg.methods[call_sequence[0]]
        nodes = [self.cls_cfg.methods[fn_name].cfg.g.nodes for fn_name in call_sequence]
        nodes = [node for node in chain(*nodes)]
        extended_nodes = method_cfg.extended_cfg.g.nodes
        self.assertEqual(set(nodes), set(extended_nodes))

