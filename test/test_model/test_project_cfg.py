import os
import unittest
import sys
from model.cfg.project_cfg import ProjectCFG
from model.project import Project

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestProjectCFG(unittest.TestCase):

    def test_init(self):

        relative_path = "../../dataset/linked_list"
        project_path = os.path.join(THIS_DIR, relative_path)
        project = Project(project_path)

        project_cfg = ProjectCFG(project)

        self.assertIsNotNone(project_cfg)

    def test_found_ll_py(self):
        relative_path = "../../dataset/linked_list"
        project_cfg = ProjectCFG(Project(os.path.join(THIS_DIR, relative_path)))

        for mod_cfg in project_cfg.module_cfgs:
            for cls_cfg in mod_cfg.class_cfgs:
                if cls_cfg == "LinkedList":
                    self.assertTrue(True)
                    return
        self.assertTrue(False)

