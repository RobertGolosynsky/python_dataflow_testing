import sys

from klepto.safe import inf_cache

from model.cfg.module_cfg import ModuleCFG
from model.project import Project
from util.find import find_files

# co = inf_cache()

class ProjectCFG:

    def __init__(self, project: Project):

        self.module_cfgs = {}
        self.cache = {}
        test_modules_paths = project.find_test_modules()

        for f in find_files(project.project_path, ".py", project.exclude_folders, test_modules_paths):
            try:
                module_cfg = ModuleCFG(f)
                self.module_cfgs[f] = module_cfg
            except NotImplementedError:
                print("Could not load module:", f)

        print("Created CFGs for such modules:")
        print("\n".join(self.module_cfgs.keys()))

    # @co
    def get_variables(self, file_path, line):
        # print(len(self.cache.keys()))
        file_path = str(file_path)
        if file_path not in self.module_cfgs:
            print("No cfg for module:", file_path)
            return None
        if (file_path, line) in self.cache:
            return self.cache[(file_path, line)]
        else:
            variables = self.module_cfgs[file_path].get_variables(line)
            self.cache[(file_path, line)] = variables
            return variables

