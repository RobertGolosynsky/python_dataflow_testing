import os
import unittest
import dataflow.inter_class as ic
import graphs.draw as gd
import util.reflection as reflection
import dataflow.def_use as du
from pathlib import Path

test_module = "sample_code/linked_list.py"


class TestInterClass(unittest.TestCase):

    def test_def_use_inter_class(self):
        sample_class = "LinkedList"
        sample_function1 = "remove"
        sample_function2 = "append"

        here = Path(os.path.realpath(__file__)).parent
        module = reflection.try_load_module(module_path=here/test_module, under_name="linked_list")

        func1 = reflection.get_class_function(module, sample_class, sample_function1)
        func2 = reflection.get_class_function(module, sample_class, sample_function2)

        cfg1 = du.try_create_cfg_with_definitions_and_uses(func1)
        cfg2 = du.try_create_cfg_with_definitions_and_uses(func2)

        pairs = ic.inter_class_def_use_pairs(cfg1, cfg2)
        self.assertEqual(len(pairs), 1)
