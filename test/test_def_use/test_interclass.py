import os
import sys
import unittest
import dataflow.inter_class as ic
import graphs.draw as gd
import util.reflection as reflection
import dataflow.def_use as du
from pathlib import Path

from model.project import Project

here = Path(os.path.realpath(__file__)).parent
this_project_root = here.parent.parent

linked_list_root = this_project_root / "dataset/linked_list"
linked_list = linked_list_root / "core/ll.py"

dictionary_root = this_project_root / "dataset/dictionary"
multi_dict = dictionary_root / "core/multi.py"


class TestInterClass(unittest.TestCase):

    def test_def_use_inter_class(self):
        sample_class = "LinkedList"
        sample_function1 = "remove"
        sample_function2 = "append"
        p = Project(linked_list_root)
        with p:
            module = reflection.try_load_module(module_path=linked_list, under_name="linked_list")

        func1 = reflection.get_class_function(module, sample_class, sample_function1)
        func2 = reflection.get_class_function(module, sample_class, sample_function2)

        cfg1 = du.try_create_cfg_with_definitions_and_uses(func1)
        cfg2 = du.try_create_cfg_with_definitions_and_uses(func2)

        pairs = ic.inter_class_def_use_pairs(cfg1, cfg2)
        self.assertEqual(len(pairs), 1)

    def test_def_use_inter_class_2(self):
        sample_class = "MultiDict"
        sample_function1 = "clear"
        sample_function2 = "items"
        p = Project(dictionary_root)

        with p:
            module = reflection.try_load_module(module_path=multi_dict, under_name="multidict")

        func1 = reflection.get_class_function(module, sample_class, sample_function1)
        func2 = reflection.get_class_function(module, sample_class, sample_function2)

        cfg1 = du.try_create_cfg_with_definitions_and_uses(func1)
        cfg2 = du.try_create_cfg_with_definitions_and_uses(func2)

        pairs = ic.inter_class_def_use_pairs(cfg1, cfg2)

        self.assertEqual(len(pairs), 2)

    def test_def_use_inter_class_inherited(self):
        sample_class = "MultiDict"
        sample_function1 = "clear"
        sample_function2 = "__len__"
        p = Project(dictionary_root)

        with p:
            module = reflection.try_load_module(module_path=multi_dict, under_name="multidict")

        func1 = reflection.get_class_function(module, sample_class, sample_function1)
        func2 = reflection.get_class_function(module, sample_class, sample_function2)

        cfg1 = du.try_create_cfg_with_definitions_and_uses(func1)
        cfg2 = du.try_create_cfg_with_definitions_and_uses(func2)

        pairs = ic.inter_class_def_use_pairs(cfg1, cfg2)

        self.assertEqual(len(pairs), 1)
