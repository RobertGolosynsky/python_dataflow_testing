import glob
import unittest
import os

import dataflow.def_use as du
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

            fns, clss, _ = au.compile_module(file)
            function = [f for f in fns if f.func.__name__ == sample_function_name][0]

            cfg = gc.try_create_cfg(function.func, function.first_line, function.argument_names)

            file_name = os.path.basename(file)
            img_file = testing_root / functions_root / (file_name + "_byte.png")
            block_graph = testing_root / functions_root / (file_name + "_block.png")

            gd.draw_byte_cfg_dot(cfg.g, [], function.func, file=str(img_file))
            gd.draw_block_cfg(function.func, img_file=str(block_graph))

    def test_create_astroid_util_cfg(self):
        astroid_util = str(testing_root.parent / "util" / "astroid_util.py")

        fns, clss, _ = au.compile_module(astroid_util)
        for function in fns:
            if not function.func:
                continue
            cfg = du.try_create_cfg_with_definitions_and_uses(function.func, function.first_line, function.argument_names)
            if not cfg:
                print("cant create cfg", function.func)
                continue
        self.assertEqual(len(fns), 13)
        self.assertEqual(len(clss), 1)
            # file_name = f[0].__name__
            # img_file = Path("astroid_cfgs") / (file_name + "_byte.png")
            # block_graph = Path("astroid_cfgs") / (file_name + "_block.png")
            # os.makedirs("astroid_cfgs", exist_ok=True)
            # gd.draw_byte_cfg_dot(cfg, [], f[0], file=str(img_file))
            # gd.draw_block_cfg(f[0], img_file=str(block_graph))

