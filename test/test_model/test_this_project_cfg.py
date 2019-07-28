import os
import unittest
import pathlib
from model.cfg.project_cfg import ProjectCFG
from model.project import Project

THIS_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))


class TestThisProjectCFG(unittest.TestCase):
    def setUp(self) -> None:
        relative_path = "../../"
        project_path = THIS_DIR / relative_path
        project = Project(project_path)

        self.project_cfg = ProjectCFG(project)
        self.astroid_util = THIS_DIR / "../../util/astroid_util.py"
        self.astroid_util = self.astroid_util.resolve()

    def test_init(self):
        self.assertIsNotNone(self.project_cfg)

    def test_astroid_util_cfg_created(self):
        self.assertIn(str(self.astroid_util), self.project_cfg.module_cfgs.keys())

    def test_astroid_util_definitions_uses(self):
        cfg = self.project_cfg.module_cfgs[str(self.astroid_util)].function_cfgs["compile_func"].cfg
        defs, uses = self.project_cfg.get_variables(self.astroid_util, 6)
        self.assertIn("line", defs)
        self.assertIn("function_def", uses)
