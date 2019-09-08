import os
import unittest
import dataflow.reaching_definitions as rd
import dataflow.inter_class as ic
from pathlib import Path
from model.cfg.module_cfg import ModuleCFG

here = Path(os.path.realpath(__file__)).parent
this_project_root = here.parent.parent

inter_method_root = this_project_root / "dataset/inter_method"
inter_method = inter_method_root / "module.py"

linked_list_root = this_project_root / "dataset/linked_list"
linked_list = linked_list_root / "core/ll.py"


class TestMethodCFGIntermethodPairs(unittest.TestCase):

    def setUp(self) -> None:
        module = str(inter_method)
        self.module_cfg = ModuleCFG(module)
        self.cls_cfg = self.module_cfg.class_cfgs["HasIntermethod"]

    def test_intermethod_pairs_include_some_interclass_pairs(self):
        interclass_only_method_cfg = self.cls_cfg.methods["interclass_only"]
        ic1_method_cfg = self.cls_cfg.methods["ic1"]
        ic2_method_cfg = self.cls_cfg.methods["ic2"]
        inter_method_pairs = rd.definition_use_pairs(interclass_only_method_cfg.extended_cfg.g,
                                                     object_vars_only=True,
                                                     intermethod_only=True
                                                     )
        inter_class_pairs = ic.inter_class_def_use_pairs_cfg(ic1_method_cfg.extended_cfg,
                                                         ic2_method_cfg.extended_cfg
                                                         )
        self.assertEqual(1, len(inter_class_pairs))
        self.assertEqual(2, len(inter_method_pairs))
        self.assertEqual(2, len(set(inter_method_pairs) - set(inter_class_pairs)))

    def test_intermethod_in_init_linked_list(self):
        self.module_cfg = ModuleCFG(str(linked_list))
        self.cls_cfg = self.module_cfg.class_cfgs["LinkedList"]

        interclass_only_method_cfg = self.cls_cfg.methods["__init__"]
        inter_method_pairs = rd.definition_use_pairs(interclass_only_method_cfg.extended_cfg.g,
                                                     intermethod_only=True,
                                                     object_vars_only=True
                                                     )

        self.assertEqual(3, len(inter_method_pairs))
