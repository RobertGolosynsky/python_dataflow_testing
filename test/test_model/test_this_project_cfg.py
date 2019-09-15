import os
import unittest
import pathlib
from model.cfg.project_cfg import ProjectCFG
from model.project import Project

THIS_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
PROJECT_PATH = THIS_DIR.parent.parent
PROJECT = Project(PROJECT_PATH)
ASTROID_UTIL = PROJECT_PATH / "util" / "astroid_util.py"
exclude_folders=["venv", "dataset"]

class TestThisProjectCFG(unittest.TestCase):

    def test_create_project_cfg(self):
        project_cfg = ProjectCFG.create_from_path(PROJECT_PATH, exclude_folders=exclude_folders)
        self.assertIsNotNone(project_cfg)
        self.assertIn(str(ASTROID_UTIL), project_cfg.module_cfgs.keys())

    def test_astroid_util_definitions_uses(self):
        project_cfg = ProjectCFG.create_from_path(PROJECT_PATH, exclude_folders=exclude_folders)
        line = 16
        defs, uses = project_cfg.get_variables(ASTROID_UTIL, line)
        self.assertIn("line", defs)
        self.assertIn("function_def", uses)
