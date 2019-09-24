import os
import unittest
from model.project import Project

import util.astroid_util as au

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestReflection(unittest.TestCase):

    def test_inherited(self):
        relative_path = "../../dataset/dictionary"
        project = Project(os.path.join(THIS_DIR, relative_path))
        module_paths = project.find_modules()
        m_file = "multi.py"
        cls_name = "MultiDict"
        multidict_path = [p for p in module_paths if m_file in p][0]

        fns, clss, _ = au.compile_module(multidict_path)
        self.assertIn(cls_name, clss.keys())
        methods = clss[cls_name]
        m_names = [m.func.__name__ for m in methods]

        self.assertIn("__init__", m_names)
        self.assertIn("items", m_names)
        self.assertIn("put", m_names)
        self.assertIn("clear", m_names)

    def test_compiles(self):
        intermediate = au._compile_module(  # ,  kwarg1=1, kwarg2="BAR", kwarg3="BAZ",**kw
            """
def func(p:int, a=3, *args, b=__Some, c: dict = {})->Set:
    return __Some1 
            """
        )
        self.assertIsNotNone(intermediate)
