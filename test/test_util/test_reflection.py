import os
import unittest
import util.reflection as ur
from model.project import Project

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
        module = ur.try_load_module(multidict_path)

        multidict_cls = [descriptor for name, descriptor in ur.module_classes(module)
                         if name == cls_name][0]

        self.assertIn("items", ur.class_functions(multidict_cls, m_type=ur.DEFINED))
        self.assertIn("put", ur.class_functions(multidict_cls, m_type=ur.OVERRIDDEN))
        self.assertIn("get", ur.class_functions(multidict_cls, m_type=ur.INHERITED))

