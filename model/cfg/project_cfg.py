import os
from collections import defaultdict
from loguru import logger

from config import COMMON_EXCLUDE
from model.cfg.module_cfg import ModuleCFG
from util.find import find_files
import pathlib
import hashlib
import pickle
import json


class ProjectCFG:
    __version__ = 2
    cfg_folder = ".flow_graph"
    tag_file = "version.hash"
    cfg_file = "project.flow"
    du_file = "du.json"

    @staticmethod
    def create_from_path(project_path, exclude_folders=None, exclude_files=None, use_cached_if_possible=True):
        if not exclude_folders:
            exclude_folders = COMMON_EXCLUDE
        module_paths = find_files(project_path, ".py", exclude_folders, exclude_files, exclude_hidden_directories=True)
        project_changed = ProjectCFG._check_project_changed(project_path, module_paths)
        if project_changed:
            logger.debug("Project changed so we have to recreate the project cfg")
        if use_cached_if_possible and not project_changed:
            p = ProjectCFG._load(project_path)
            if p and hasattr(p, "__version__") and p.__version__ == ProjectCFG.__version__:
                logger.info("Loaded Project CFG from a save file")
            else:
                logger.warning("Save file not found for project {pp}", pp=project_path)
                p = ProjectCFG(
                    project_path=project_path,
                    module_paths=module_paths
                )
        else:
            p = ProjectCFG(
                project_path=project_path,
                module_paths=module_paths
            )
        return p

    def __init__(self, project_path, module_paths):
        self.project_path = project_path
        self.module_cfgs = {}
        self.cache = {}

        self.module_cfgs = self._create_module_cfgs(module_paths)
        self.definitions = defaultdict(dict)
        self.uses = defaultdict(dict)

        for m, cfg in self.module_cfgs.items():
            self.definitions[cfg.module_path].update(cfg.definitions)
            self.uses[cfg.module_path].update(cfg.uses)

        self._save()

        logger.info("Have CFGs for such modules: {ms}", ms=list(self.module_cfgs.keys()))

    def get_variables(self, file_path, line):
        file_path = str(file_path)
        if file_path not in self.module_cfgs:
            logger.debug("No cfg for module: {f}", f=file_path)
            return None
        d = self.definitions[file_path].get(line, [])
        u = self.uses[file_path].get(line, [])
        return d, u

    def _create_module_cfgs(self, module_paths):
        self.version_hash = self._calculate_project_hash(module_paths)
        module_cfgs = {}
        for f in module_paths:
            try:
                module_cfg = ModuleCFG(f)
                module_cfgs[f] = module_cfg
            except NotImplementedError:
                logger.info("Could not create module cfg for {f}", f=f)
        return module_cfgs

    def _save(self):
        project_path = pathlib.Path(self.project_path)
        cfg_folder_path = project_path / ProjectCFG.cfg_folder
        os.makedirs(cfg_folder_path, exist_ok=True)
        module_cfg_save_file = cfg_folder_path / self.cfg_file

        tag_file_path = cfg_folder_path / self.tag_file

        du_file_path = cfg_folder_path / self.du_file

        with open(tag_file_path, "w") as f:
            f.write(self.version_hash)

        with open(module_cfg_save_file, "wb") as f:
            pickle.dump(self, f)

        d = {"definitions": self.definitions, "uses": self.uses}
        with open(du_file_path, "w") as f:
            json.dump(d, f, indent=2)

    @staticmethod
    def _load(project_path):
        project_path = pathlib.Path(project_path)
        save_file = project_path / ProjectCFG.cfg_folder / ProjectCFG.cfg_file

        if save_file.is_file():
            with open(save_file, "rb") as f:
                return pickle.load(f)
        else:
            return None

    @staticmethod
    def _calculate_project_hash(module_paths):
        h = hashlib.sha1()
        for f_path in module_paths:
            with open(f_path, encoding="utf-8") as f:
                h.update(f.read().encode("utf-8"))
        return h.hexdigest()

    @staticmethod
    def _check_project_changed(project_path, modules):
        project_path = pathlib.Path(project_path)
        if project_path.is_dir():
            tag_file_path = project_path / ProjectCFG.cfg_folder / ProjectCFG.tag_file
            if tag_file_path.is_file():
                with open(tag_file_path, "r") as f:
                    h = f.read()
                calculated_hash = ProjectCFG._calculate_project_hash(modules)
                if h == calculated_hash:
                    return False
        return True


def read_du_index(project_root):
    du_json_path = os.path.join(project_root, ProjectCFG.cfg_folder, ProjectCFG.du_file)
    with open(du_json_path) as f:
        file_dict = json.load(f)
        new_dict = {}
        for d_or_u in file_dict:
            files_dict = file_dict[d_or_u]
            new_files_dict = {}
            for fname in files_dict:
                module_dict = files_dict[fname]
                new_files_dict[fname] = {int(l): vs for l, vs in module_dict.items()}
            new_dict[d_or_u] = new_files_dict

        return new_dict
