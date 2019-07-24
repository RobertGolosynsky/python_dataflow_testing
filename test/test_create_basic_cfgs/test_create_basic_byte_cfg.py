import glob
import unittest
import os

import graphs.create as gc
import graphs.draw as gd
import util.astroid_util as au

from pathlib import Path


functions_root = "basic_functions"
sample_function_name = "testing"
testing_root = Path(os.path.realpath(__file__)).parent.parent


class TestCreateByteCFG(unittest.TestCase):

    def test_create_byte_cfg(self):
        search_path = str(testing_root / functions_root / "*.py")

        for file in glob.glob(search_path):

            fns, clss = au.compile_module(file)
            fn = [f for f in fns if f[0].__name__ == sample_function_name][0]

            cfg = gc._try_create_byte_offset_cfg(*fn)

            file_name = os.path.basename(file)
            img_file = testing_root / functions_root / (file_name + "_byte.png")
            block_graph = testing_root / functions_root / (file_name + "_block.png")

            # gd.draw_byte_cfg_dot(cfg, [], func, file=str(img_file))
            gd.draw_block_cfg(fn[0], img_file=str(block_graph))

