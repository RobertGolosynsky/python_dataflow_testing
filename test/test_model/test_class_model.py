import os
import unittest
import sys

from model.cfg.project_cfg import ProjectCFG
from model.project import Project

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestClassModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        relative_path = "../../dataset/dictionary"
        cls.project = Project(os.path.join(THIS_DIR, relative_path))

        with cls.project as p:
            cls.project_cfg = ProjectCFG(p)

        multi_dict_class_name = "MultiDict"
        multidict_cfg = None
        # self.project.add_to_path()
        for file_path, mod_cfg in cls.project_cfg.module_cfgs.items():
            for cls_name in mod_cfg.class_cfgs:
                if cls_name == multi_dict_class_name:
                    multidict_cfg = mod_cfg.class_cfgs[cls_name]
        cls.multidict_cfg = multidict_cfg

    def test_found_inherited_methods(self):

        self.assertIn("items", self.multidict_cfg.methods)

        self.assertIn("put", self.multidict_cfg.methods)
        self.assertIn("__init__", self.multidict_cfg.methods)

    def test_local_interclass_pairs(self):
        self.assertEqual(7, len(self.multidict_cfg.interclass_pairs))
