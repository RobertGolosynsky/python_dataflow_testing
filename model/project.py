import os
import shutil
import subprocess
import sys
import time

import pytest_collect_test_modules
import pytest_failed_node_ids
import pathlib
from typing import List, Union
import pipfile
import virtualenv
from loguru import logger

from util.find import find_files

pytest_failed_node_ids_path = pytest_failed_node_ids.__file__
pytest_collect_test_modules_path = pytest_collect_test_modules.__file__
through_requirements_path = pathlib.Path(__file__).parent.parent / "requirements.txt"
assert through_requirements_path.is_file()
dataset_folder = "dataset"


# activate_this_py_url = "https://raw.githubusercontent.com/pypa/virtualenv/master/virtualenv_embedded/activate_this.py"


class Project(object):
    commands_sep = " ; "
    venv_folder_name = "venv"
    activate_this_file_name = "activate_this.py"
    bin_folder_name = "bin"
    exclude_folders = ["venv", "__pycache__"]
    thorough_requirements = [r.strip() for r in open(through_requirements_path).readlines()]

    def __init__(self, project_path, silence_output=False):
        self.venv_activated = False
        self.silence_output = silence_output
        self.path = str(pathlib.Path(project_path).resolve())
        self.project_name = os.path.basename(self.path)
        self.tests = []
        self.requirements = self._extract_necessary_packages()
        self.installed_packages = set()
        self.testing_time = 0

    def __repr__(self):
        return "<Project, path={}>".format(self.path)

    def has_setup(self):
        return "setup.py" in os.listdir(self.path)

    def has_requirements(self):
        return "requirements.txt" in os.listdir(self.path)

    def has_venv(self):
        return os.path.isdir(os.path.join(self.path, self.venv_folder_name))

    def _create_venv_path(self):
        return os.path.join(self.path, self.venv_folder_name)

    def is_venv_installed(self):
        venv = self._create_venv_path()
        if os.path.isdir(venv):
            if os.path.join(venv, "bin", "activate"):
                return True
        return False

    def create_venv(self, force_remove_previous=True):
        venv_path = self._create_venv_path()

        if force_remove_previous or not self.is_venv_installed():
            logger.info("Creating virtual environment in {venv}", venv=venv_path)
            virtualenv.create_environment(venv_path)
        else:
            logger.warning("Using previously created virtual environment in {venv}", venv=venv_path)
            self.installed_packages.update(self.get_installed_modules())

    def get_installed_modules(self):
        code, out, err = self.run_command_capture_output(f"pip3 freeze", activate_only=True)
        installed_packages = []
        for line in out.split("\n"):
            clean = line.strip()
            if clean:
                installed_packages.append(clean)
        return installed_packages

    def run_command(self, cmd, extra_requirements=None, capture_output=False, activate_only=False, timeout=None):
        if not extra_requirements:
            extra_requirements = []

        kw = {
            "stdout": subprocess.PIPE if capture_output or self.silence_output else sys.stdout,
            "stderr": subprocess.PIPE if capture_output or self.silence_output else sys.stdout,
            "shell": True,
            "cwd": self.path
        }

        packages = [p for p in self.requirements + extra_requirements if p.strip() != ""]

        activate_venv = f". {self.venv_folder_name}/bin/activate"
        if timeout:
            cmd = f"timeout {timeout} " + cmd
        cmds = [activate_venv]
        if not activate_only:
            packages_set = set(packages)
            to_install = packages_set - self.installed_packages
            already_installed = packages_set - to_install
            if already_installed:
                logger.debug("Packages {p} are already installed {path}", p=already_installed, path=self.path)
            logger.debug("Packages {p} are queued do be installed {path}", p=to_install, path=self.path)
            for package in to_install:
                cmds.append(f"pip3 install {package}")
                self.installed_packages.add(package)
        cmds.append(cmd)

        extended_cmd = self.commands_sep.join(cmds)
        logger.info("Running {extended_cmd} in {path}", extended_cmd=extended_cmd, path=self.path)
        proc = subprocess.run(extended_cmd, **kw)
        if capture_output:
            return proc
        else:
            return proc.returncode

    def run_command_capture_output(self, cmd, extra_requirements=None, activate_only=False, timeout=None):
        if extra_requirements is None:
            extra_requirements = []
        _ = self.run_command("", extra_requirements=extra_requirements, activate_only=False)
        proc = self.run_command(cmd, extra_requirements=extra_requirements, capture_output=True,
                                activate_only=activate_only, timeout=timeout)
        return proc.returncode, proc.stdout.decode(), proc.stderr.decode()

    def run_tests_get_failed_node_ids(self):
        st = time.time()
        if self.testing_time > 0:
            timeout = int(self.testing_time)*10
        else:
            timeout = None

        extra_requirements = """
pytest
""".split("\n")
        code, out, err = self.run_command_capture_output(
            f"python3 {pytest_failed_node_ids_path}",
            extra_requirements=extra_requirements,
            timeout=timeout
        )
        self.testing_time = time.time() - st
        print("SDTOUT=" * 100)
        print(out)
        print("SDTERR=" * 100)
        print(err)
        failed_cases = []
        for line in out.split("\n"):
            clean = line.strip()
            if clean:
                failed_cases.append(clean)
        return failed_cases

    def collect_test_modules(self):
        extra_requirements = """
pytest
""".split("\n")
        code, out, err = self.run_command_capture_output(f"python3 {pytest_collect_test_modules_path}",
                                                         extra_requirements=extra_requirements)
        print("=" * 100)
        print(out)
        print("=" * 100)
        print(err)
        test_modules_paths = []
        for line in out.split("\n"):
            clean = line.strip()
            if clean:
                test_modules_paths.append(clean)
        return test_modules_paths

    def tests_fail(self):
        return self.run_command("pytest") != 0

    def tracing_fails(self):
        return self.run_command("python3 /home/robert/Documents/master/code/python_dataflow_testing/thorough.py -t",
                                extra_requirements=self.thorough_requirements) != 0

    def find_test_modules(self):
        modules = []
        for f in find_files(self.path, ".py", self.exclude_folders, [],
                            exclude_hidden_directories=True):
            if os.path.basename(f)[:4].lower() == "test":
                modules.append(f)
        return modules

    def find_modules(self):
        test_modules = self.find_test_modules()
        modules = []

        for f in find_files(self.path, ".py", self.exclude_folders, test_modules,
                            exclude_hidden_directories=True):
            modules.append(f)

        return modules

    def _extract_necessary_packages(self) -> List[str]:
        packages = []
        file_names = [
            "requirements.txt",
            "dev-requirements.txt",
            "dev_requirements.txt",
            "test-requirements.txt",
            "test_requirements.txt",
            "requirements-dev.txt",
            "requirements_dev.txt",
            "requirements-test.txt",
            "requirements_test.txt",
        ]
        for file_name in file_names:
            packages.extend(self._extract_packages(os.path.join(self.path, file_name)))
        if os.path.exists(os.path.join(self.path, "Pipfile")) and os.path.isfile(
                os.path.join(self.path, "Pipfile")
        ):
            packages.extend(self._extract_packages_from_pipfile())

        return packages

    @staticmethod
    def _extract_packages(
            requirements_file: Union[bytes, str, os.PathLike]
    ) -> List[str]:
        packages = []
        if os.path.exists(requirements_file) and os.path.isfile(requirements_file):
            with open(requirements_file) as f:
                packages = [
                    line.strip() for line in f.readlines() if "requirements" not in line
                ]
        return packages

    def _extract_packages_from_pipfile(self) -> List[str]:
        packages = []
        p = pipfile.load(os.path.join(self.path, "Pipfile"))
        data = p.data
        if len(data["default"]) > 0:
            for k, _ in data["default"].items():
                packages.append(k)
        if len(data["develop"]) > 0:
            for k, _ in data["develop"].items():
                packages.append(k)
        return packages

    def delete_from_disk(self):
        shutil.rmtree(self.path)


class Merger:
    def __init__(self, fixed_proj, buggy_proj):
        self.fixed_proj = fixed_proj
        self.buggy_proj = buggy_proj

    def move_test_from_fixed_to_buggy(self):
        fixed_project_test_modules = self.fixed_proj.collect_test_modules()
        buggy_project_test_modules = self.buggy_proj.collect_test_modules()

        self.remove_all(self.buggy_proj.path, buggy_project_test_modules)

        for test_module_path in fixed_project_test_modules:
            self.move(self.fixed_proj.path, self.buggy_proj.path, test_module_path)

    def move(self, old_parent, new_parent, path):

        shutil.copy(
            os.path.join(old_parent, path),
            os.path.join(new_parent, path)
        )

    def remove_all(self, parent_path, paths):
        for file in paths:
            os.remove(os.path.join(parent_path, file))
