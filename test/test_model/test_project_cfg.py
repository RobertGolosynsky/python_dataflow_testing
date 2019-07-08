import os
import unittest
from model.cfg.project_cfg import ProjectCFG
from model.project import Project

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestProjectCFG(unittest.TestCase):

    def test_init(self):
        relative_path = "../../dataset/linked_list"
        project_cfg = ProjectCFG(Project(os.path.join(THIS_DIR, relative_path)))
