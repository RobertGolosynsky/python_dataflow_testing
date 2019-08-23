import inspect
import unittest
import util.astroid_util as au
import ast


class TestCompile(unittest.TestCase):

    def test_compile(self):
        fns, clss, calls = au.compile_module(__file__)
        self.assertIn("TestCompile", clss.keys())
        this_cls_methods = clss["TestCompile"]
        this_cls_methods_names = [m.func.__name__ for m in this_cls_methods]
        self.assertIn("test_compile", this_cls_methods_names)