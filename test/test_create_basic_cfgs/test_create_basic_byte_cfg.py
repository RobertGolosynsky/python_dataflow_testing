import glob
import inspect
import unittest
import os

# from rpython.flowspace.objspace import build_flow
# from rpython.flowspace.pygraph import PyGraph



import dataflow.inter_class as ic
import dataflow.def_use as du
import dataflow.reaching_definitions as rd
import graphs.create as gc
import graphs.draw as gd
import util.reflection as reflection
from pathlib import Path


functions_root = "basic_functions"
sample_function_name = "testing"
testing_root = Path(os.path.realpath(__file__)).parent.parent


class TestCreateByteCFG(unittest.TestCase):

    def test_create_byte_cfg(self):
        search_path = str(testing_root / functions_root / "*.py")

        for file in glob.glob(search_path):

            module = reflection.try_load_module(module_path=file, under_name="module")
            func = getattr(module, sample_function_name)

            cfg = gc._try_create_byte_offset_cfg(func)

            file_name = os.path.basename(file)
            img_file = testing_root / functions_root / (file_name + "_byte.png")
            block_graph = testing_root / functions_root / (file_name + "_block.png")

            # gd.draw_byte_cfg_dot(cfg, [], func, file=str(img_file))
            gd.draw_block_cfg(func, img_file=str(block_graph))

