import os
import unittest
import pathlib
from model.cfg.project_cfg import ProjectCFG
from model.project import Project

THIS_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))


class TestProjectCFG(unittest.TestCase):

    def setUp(self) -> None:
        relative_path = "../../dataset/linked_list"
        project_path = THIS_DIR / relative_path
        project = Project(project_path)

        self.project_cfg = ProjectCFG(project)
        self.ll_module_path = THIS_DIR / "../../dataset/linked_list/core/ll.py"
        self.ll_module_path = self.ll_module_path.resolve()

    def test_init(self):
        self.assertIsNotNone(self.project_cfg)

    def test_found_ll_py(self):

        for file_path, mod_cfg in self.project_cfg.module_cfgs.items():
            for cls_cfg in mod_cfg.class_cfgs:
                if cls_cfg == "LinkedList":
                    self.assertTrue(True)
                    return
        self.assertTrue(False)

    def test_get_variables(self):

        defs, uses = self.project_cfg.get_variables(str(self.ll_module_path), 11)
        self.assertIn("self.root", defs)

    def test_get_variables_wrong_line(self):
        variables = self.project_cfg.get_variables(str(self.ll_module_path), 1100)
        self.assertEqual(variables, None)
