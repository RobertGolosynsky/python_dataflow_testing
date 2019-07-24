import sys

from model.cfg.module_cfg import ModuleCFG
from model.project import Project
from util.find import find_files


class ProjectCFG:

    def __init__(self, project: Project):

        self.module_cfgs = []

        test_modules_paths = project.find_test_modules()

        for f in find_files(project.project_path, ".py", project.exclude_folders, test_modules_paths):
            try:
                module_cfg = ModuleCFG(f)
                self.module_cfgs.append(module_cfg)
            except NotImplementedError:
                print("Could not load module:", f)

