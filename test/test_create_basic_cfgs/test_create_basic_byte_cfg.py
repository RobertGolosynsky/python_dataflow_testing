import glob
import unittest
import os
import dataflow.inter_class as ic
import dataflow.def_use as du
import dataflow.reaching_definitions as rd
import graphs.create as gc
import graphs.draw as gd
import util.reflection as reflection
from pathlib import Path

functions_root = "basic_functions"
sample_function_name = "testing"


class TestCreateByteCFG(unittest.TestCase):

    def test_create_byte_cfg(self):

        testing_root = Path(os.path.realpath(__file__)).parent.parent
        search_path = str(testing_root / functions_root / "*.py")
        for file in glob.glob(search_path):
            if not os.path.basename(file) == "for_try_else1.py":
                continue
            module = reflection.try_load_module(module_path=file, under_name="module")
            func = getattr(module, sample_function_name)
            # cfg = gc.try_create_cfg(sample_func)
            cfg = gc._try_create_byte_offset_cfg(func) #du.try_create_cfg_with_definitions_and_uses(func)
            # pairs = rd.definition_use_pairs(cfg)
            img_file = os.path.basename(file)
            img_file = testing_root / functions_root / (img_file + "_byte.png")

            gd.draw_byte_cfg_dot(cfg, [], func, file=str(img_file))
            gd.draw_block_cfg(func)
