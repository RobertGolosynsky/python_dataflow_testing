import os
import unittest
import dataflow.inter_class as ic
import dataflow.def_use as du
from pathlib import Path

from model.project import Project
import util.astroid_util as au

here = Path(os.path.realpath(__file__)).parent
this_project_root = here.parent.parent

linked_list_root = this_project_root / "dataset/linked_list_clean"
linked_list = linked_list_root / "core/ll.py"

dictionary_root = this_project_root / "dataset/dictionary"
multi_dict = dictionary_root / "core/multi.py"


class TestInterClass(unittest.TestCase):

    def test_def_use_inter_class(self):
        sample_class = "LinkedList"
        sample_function1 = "remove"
        sample_function2 = "append"
        p = Project(linked_list_root)

        fns, clss, _ = au.compile_module(linked_list)

        cls_funcs = clss[sample_class]

        func1 = [f for f in cls_funcs if f.func.__name__ == sample_function1][0]
        func2 = [f for f in cls_funcs if f.func.__name__ == sample_function2][0]

        cfg1 = du.try_create_cfg_with_definitions_and_uses(func1.func, func1.first_line, func1.argument_names)
        cfg2 = du.try_create_cfg_with_definitions_and_uses(func2.func, func2.first_line, func2.argument_names)

        pairs = ic.inter_class_def_use_pairs_cfg(cfg1, cfg2)
        self.assertEqual(len(pairs), 1)

    def test_def_use_inter_class_2(self):
        sample_class = "MultiDict"
        sample_function1 = "clear"
        sample_function2 = "items"

        fns, clss, _ = au.compile_module(multi_dict)

        cls_funcs = clss[sample_class]

        func1 = [f for f in cls_funcs if f.func.__name__ == sample_function1][0]
        func2 = [f for f in cls_funcs if f.func.__name__ == sample_function2][0]

        cfg1 = du.try_create_cfg_with_definitions_and_uses(func1.func, func1.first_line, func1.argument_names)
        cfg2 = du.try_create_cfg_with_definitions_and_uses(func2.func, func2.first_line, func2.argument_names)

        pairs = ic.inter_class_def_use_pairs_cfg(cfg1, cfg2)
        self.assertEqual(len(pairs), 2)

