import os
import subprocess
import sys
import urllib.request
import venv

import astroid

import util.astroid_util as au
from util.find import find_files

dataset_folder = "dataset"
activate_this_py_url = "https://raw.githubusercontent.com/pypa/virtualenv/master/virtualenv_embedded/activate_this.py"


class Project(object):
    venv_folder_name = "venv"
    activate_this_file_name = "activate_this.py"
    bin_folder_name = "bin"
    exclude_folders = ["venv", "__pycache__"]

    def __init__(self, project_path):
        self.venv_activated = False
        self.project_path = str(project_path)
        self.project_name = os.path.basename(self.project_path)
        self.tests = []

    def __repr__(self):
        return "<Project, path={}>".format(self.project_path)

    def has_setup(self):
        return "setup.py" in os.listdir(self.project_path)

    def has_requirements(self):
        return "requirements.txt" in os.listdir(self.project_path)

    def has_venv(self):
        return os.path.isdir(os.path.join(self.project_path, self.venv_folder_name))

    def create_venv_path(self):
        return os.path.join(self.project_path, self.venv_folder_name)

    def create_activator_location(self):
        return os.path.join(self.create_venv_path(),
                            self.bin_folder_name,
                            self.activate_this_file_name
                            )

    def freeze(self, force=False):
        if self.has_requirements() and not force:
            return

        cmd = "pipreqs {}".format(self.project_path)
        if force:
            cmd += " --force"

        process = subprocess.Popen(cmd, shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   # cwd=self.project_path
                                   )

        out, err = process.communicate()
        errcode = process.returncode
        if not errcode == 0:
            raise SystemError(err)
        else:
            return
        # subprocess.run(["pipreqs", self.project_path, "--force"])

    def create_venv(self):
        if not self.has_venv():
            env = venv.EnvBuilder(system_site_packages=False,
                                  clear=False,
                                  symlinks=False,
                                  upgrade=False,
                                  with_pip=True,  # apt-get install python3-venv
                                  prompt=self.project_name)
            venv_path = self.create_venv_path()
            env.create(venv_path)

            # add activate_this.py
            # https://raw.githubusercontent.com/pypa/virtualenv/master/virtualenv_embedded/activate_this.py
            activator_path = self.create_activator_location()
            urllib.request.urlretrieve(activate_this_py_url, activator_path)

    def _save_params(self):
        self.saved_params = (
            os.environ["PATH"],
            os.environ["VIRTUAL_ENV"],
            sys.path,
            sys.prefix
        )

    def _revert_params(self):
        os_path, venv, path, prefix = self.saved_params
        os.environ["PATH"] = os_path
        os.environ["VIRTUAL_ENV"] = venv
        sys.path[:0] = path
        sys.prefix = prefix

    def activate_venv(self):
        if self.has_venv():
            self.venv_activated = True
            self._save_params()
            activator_path = self.create_activator_location() # Looted from virtualenv; should not require modification, since it's defined relatively
            with open(activator_path) as f:
                exec(f.read(), {'__file__': activator_path})
            # print("Using this python environment:", os.path.dirname(sys.executable))
            print("Using this python environment:", os.environ["VIRTUAL_ENV"])

    def deactivate_venv(self):
        if self.has_venv():
            self.venv_activated = False
            self._revert_params()

    def install_dependencies(self):
        cmd = "pip3 install -r requirements.txt"
        process = subprocess.Popen(cmd, shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   cwd=self.project_path
                                   )

        out, err = process.communicate()
        errcode = process.returncode
        print(out)
        if not errcode == 0:
            raise SystemError(err)
        else:
            return

    def add_to_path(self):
        sys.path.insert(0, self.project_path)

    def remove_from_path(self):
        sys.path.remove(self.project_path)

    def find_test_modules(self):
        modules = []
        for f in find_files(self.project_path, ".py", self.exclude_folders, []):
            with open(f) as file:
                module_text = file.read()
                if module_text:
                    # print(module_text)
                    module_node = astroid.parse(module_text)
                    test_classes = au.classes_with_base_class(module_node, "TestCase")
                    if len(test_classes) > 0:
                        modules.append(f)
        # ladies and gentleman, we got him
        return modules

    def find_modules(self):
        test_modules = self.find_test_modules()
        modules = []

        for f in find_files(self.project_path, ".py", self.exclude_folders, test_modules):
            modules.append(f)

        return modules

    def __enter__(self):
        self.saved_modules = sys.modules.copy()
        self.activate_venv()
        self.add_to_path()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deactivate_venv()
        for mod in sys.modules:
            if mod not in self.saved_modules.keys():
                del sys.modules[mod]
        for module_name in self.saved_modules:
            sys.modules[module_name] = self.saved_modules[module_name]
