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
        project.add_to_path()
        multidict_path = [p for p in module_paths if m_file in p][0]

        fns, clss = au.compile_module(multidict_path)
        self.assertIn(cls_name, clss.keys())
        methods = clss[cls_name]
        m_names = [m[0].__name__ for m in methods]

        self.assertIn("__init__", m_names)
        self.assertIn("items", m_names)
        self.assertIn("put", m_names)
        self.assertIn("clear", m_names)

