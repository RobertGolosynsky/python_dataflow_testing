from model.cfg.module_cfg import ModuleCFG
from model.project import Project
from util.find import find_files


class ProjectCFG:
    exclude_folders = ["venv", "__pycache__"]

    def __init__(self, project: Project):
        self.module_cfgs = []
        project.add_to_path()
        for f in find_files(project.project_path, ".py", self.exclude_folders):
            try:
                module_cfg = ModuleCFG(f)
                self.module_cfgs.append(module_cfg)
            except NotImplementedError:
                print("Could not load module:", f)
        project.remove_from_path()
