import os
import subprocess
import sys
import urllib.request
import venv

dataset_folder = "dataset"
activate_this_py_url = "https://raw.githubusercontent.com/pypa/virtualenv/master/virtualenv_embedded/activate_this.py"


class Project(object):
    venv_folder_name = "venv"
    activate_this_file_name = "activate_this.py"
    bin_folder_name = "bin"

    def __init__(self, project_path):

        self.project_path = project_path
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

    def activate_venv(self):
        if self.has_venv():
            activator_path = self.create_activator_location() # Looted from virtualenv; should not require modification, since it's defined relatively
            with open(activator_path) as f:
                exec(f.read(), {'__file__': activator_path})
            print("Using this python environment:", os.path.dirname(sys.executable))

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
