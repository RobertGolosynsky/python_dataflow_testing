import os
from collections import defaultdict

from model.cfg.module_cfg import ModuleCFG
from model.project import Project
from util.find import find_files
import pathlib
import hashlib
import pickle


class ProjectCFG:

    cfg_folder = ".flow_graph"
    tag_file = "version.hash"
    cfg_file = "project.flow"

    def __init__(self, project: Project):
        self.project = project
        self.module_cfgs = {}
        self.cache = {}
        test_modules_paths = project.find_test_modules()
        self.module_paths = find_files(project.project_path, ".py", project.exclude_folders, test_modules_paths)

        if self._check_project_changed():
            self.module_cfgs = self._create_module_cfgs()
            self.definitions = defaultdict(dict)
            self.uses = defaultdict(dict)

            for m, cfg in self.module_cfgs.items():
                self.definitions[cfg.module_path].update(cfg.definitions)
                self.uses[cfg.module_path].update(cfg.uses)

            self._save()
        else:
            self.module_cfgs, self.definitions, self.uses = self._load()

        print("Have CFGs for such modules:")
        print("\n".join(self.module_cfgs.keys()))

    def get_variables(self, file_path, line):
        file_path = str(file_path)
        if file_path not in self.module_cfgs:
            print("No cfg for module:", file_path)
            return None
        d = self.definitions[file_path].get(line, [])
        u = self.uses[file_path].get(line, [])

        return d, u

    def get_variables_slow(self, file_path, line):
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

    def _create_module_cfgs(self):
        self.version_hash = self._calculate_project_hash()
        module_cfgs = {}
        for f in self.module_paths:
            try:
                module_cfg = ModuleCFG(f)
                module_cfgs[f] = module_cfg
            except NotImplementedError:
                print("Could not load module:", f)
        return module_cfgs

    def _calculate_project_hash(self):
        h = hashlib.sha1()
        for f_path in self.module_paths:
            last_modified_time = pathlib.Path(f_path).stat().st_mtime
            h.update(str(last_modified_time).encode())

        return h.hexdigest()

    def _check_project_changed(self):
        project_path = pathlib.Path(self.project.project_path)
        if project_path.is_dir():
            tag_file_path = project_path / self.cfg_folder / self.tag_file
            if tag_file_path.is_file():
                with open(tag_file_path, "r") as f:
                    h = f.read()
                calculated_hash = self._calculate_project_hash()
                if h == calculated_hash:
                    return False
        return True

    def _save(self):
        project_path = pathlib.Path(self.project.project_path)
        cfg_folder_path = project_path / self.cfg_folder
        os.makedirs(cfg_folder_path, exist_ok=True)
        save_file = cfg_folder_path / self.cfg_file

        tag_file_path = cfg_folder_path / self.tag_file

        with open(tag_file_path, "w") as f:
            f.write(self.version_hash)

        with open(save_file, "wb") as f:
            pickle.dump((self.module_cfgs, self.definitions, self.uses), f)

    def _load(self):

        project_path = pathlib.Path(self.project.project_path)
        save_file = project_path / self.cfg_folder / self.cfg_file

        if save_file.is_file():
            with open(save_file, "rb") as f:
                return pickle.load(f)
        else:
            return None
