import os
import shutil
import subprocess
import sys
import urllib.request
import pathlib
from typing import List, Union
import pipfile
import virtualenv
from loguru import logger

from util.find import find_files

dataset_folder = "dataset"
# activate_this_py_url = "https://raw.githubusercontent.com/pypa/virtualenv/master/virtualenv_embedded/activate_this.py"


class Project(object):
    venv_folder_name = "venv"
    activate_this_file_name = "activate_this.py"
    bin_folder_name = "bin"
    exclude_folders = ["venv", "__pycache__"]
    thorough_requirements = """
pipfile
peewee
virtualenv
pytest
pytest-cov
loguru
cppimport
pandas
numpy
matplotlib==2.2.2
networkx==2.1
xdis==4.0.1
-e git+git://github.com/RobertGolosynsky/mutmut.git#egg=mutmut
-e git+git://github.com/rocky/python-control-flow#egg=control-flow
pygraphviz
""".split("\n")

    def __init__(self, project_path):
        self.venv_activated = False
        self._path = str(pathlib.Path(project_path).resolve())
        self.project_name = os.path.basename(self._path)
        self.tests = []
        self.requirements = self._extract_necessary_packages()

    def __repr__(self):
        return "<Project, path={}>".format(self._path)

    def has_setup(self):
        return "setup.py" in os.listdir(self._path)

    def has_requirements(self):
        return "requirements.txt" in os.listdir(self._path)

    def has_venv(self):
        return os.path.isdir(os.path.join(self._path, self.venv_folder_name))

    def _create_venv_path(self):
        return os.path.join(self._path, self.venv_folder_name)

    def create_venv(self):
        venv_path = self._create_venv_path()
        virtualenv.create_environment(venv_path)

    def run_command(self, cmd, extra_requirements=None):
        if not extra_requirements:
            extra_requirements = []
        kw = {
            "stdout": sys.stderr,
            "stderr": subprocess.PIPE,
            "shell": True,
            "cwd": self._path
        }
        packages = [p for p in self.requirements+extra_requirements if p.strip() != ""]
        activate_venv = f". {self.venv_folder_name}/bin/activate"
        cmds = [activate_venv]
        for package in packages:
            cmds.append(f"pip3 install {package}")

        cmds.append(cmd)

        extended_cmd = " && ".join(cmds)
        print("Running", extended_cmd, "in", self._path)
        proc = subprocess.run(extended_cmd, **kw)

        print("Errors:")
        print("=" * 100)
        print(proc.stderr.decode("utf-8"))
        print("=" * 100)
        return proc.returncode

    # def tests_fail(self):
    #     return self.run_command("pytest -q", extra_requirements=["pytest"]) != 0

    def tests_fail(self):
        return self.run_command("python3 /home/robert/Documents/master/code/python_dataflow_testing/thorough.py -t",
                                extra_requirements=self.thorough_requirements) != 0

    def find_test_modules(self):
        modules = []
        for f in find_files(self._path, ".py", self.exclude_folders, [], exclude_hidden_directories=True):
            if os.path.basename(f)[:4].lower() == "test":
                modules.append(f)
        return modules

    def find_modules(self):
        test_modules = self.find_test_modules()
        modules = []

        for f in find_files(self._path, ".py", self.exclude_folders, test_modules,
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
            packages.extend(self._extract_packages(os.path.join(self._path, file_name)))
        if os.path.exists(os.path.join(self._path, "Pipfile")) and os.path.isfile(
                os.path.join(self._path, "Pipfile")
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
        p = pipfile.load(os.path.join(self._path, "Pipfile"))
        data = p.data
        if len(data["default"]) > 0:
            for k, _ in data["default"].items():
                packages.append(k)
        if len(data["develop"]) > 0:
            for k, _ in data["develop"].items():
                packages.append(k)
        return packages

    def delete_from_disk(self):
        shutil.rmtree(self._path)
