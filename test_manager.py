import ast
import sys
import os
import subprocess
import venv
from pathlib import Path
import astroid
import urllib.request

from file_finder import find_files

dataset_folder = "dataset"
activate_this_py_url = "https://raw.githubusercontent.com/pypa/virtualenv/master/virtualenv_embedded/activate_this.py"
"""
1. find requirements.txt if not
1.1 import subprocess
1.1 subprocess.run(["pip","freeze", ">", "requirements.txt"])
2. create venv
3. install dependencies in venv
maybe if setup is present - setup the project(for now no setup)
4. find test classes
5. for every test class find target class under test

"""




def listdir_fullpath(d):
    return [os.path.join(d, f) for f in os.listdir(d)]





class TestClass(object):
    def __init__(self, test_class_node, import_nodes, file_path, code):
        self.test_class_node = test_class_node
        self.import_nodes = import_nodes
        self.file_path = file_path
        self.code = code
        self.function_nodes = list(self.extract_function_nodes())

    def extract_function_nodes(self):
        for node in self.test_class_node.body:
            yield node


class TestModule(object):

    def __init__(self, file_path, code, ast):
        self.file_path = file_path
        self.code = code
        self.ast = ast
        self.import_nodes = self.extract_import_nodes()
        self.test_class_nodes = self.extract_test_class_nodes()
        self.test_classes = self.crete_test_classes()


    def extract_import_nodes(self):
        import_nodes = []
        for node in self.ast.body:
            if isinstance(node, astroid.ImportFrom) \
                    or isinstance(node, astroid.Import):
                import_nodes.append(node)
        return import_nodes

    def extract_test_class_nodes(self):
        test_class_nodes = []
        for node in self.ast.body:
            if isinstance(node, astroid.ClassDef):
                for base_class in node.bases:
                    if isinstance(base_class, astroid.Attribute):
                        base_class_name = base_class.attrname
                    else:
                        base_class_name = base_class.name
                    if base_class_name and base_class_name == "TestCase":
                        test_class_nodes.append(node)
        return test_class_nodes


    def crete_test_classes(self):
        test_classes = []
        for test_class_node in self.test_class_nodes:
            test_classes.append(TestClass(test_class_node, self.import_nodes, self.file_path, self.code))
        return test_classes

    def explore(self):
        print(self.ast)



class TestManager(object):

    exclude_folders = ["venv", "__pycache__"]

    def __init__(self, project) -> None:
        self.project = project
        self.tests = self.find_test_modules()


    def find_test_modules(self):
        modules = []
        for f in find_files(self.project.project_path, ".py", self.exclude_folders):
            with open(f) as file:
                module_text = file.read()
                if module_text:
                    # print(module_text)
                    module_node = astroid.parse(module_text)
                    for class_ in module_node.body:
                        if isinstance(class_, astroid.ClassDef):
                            for base_class in class_.bases:
                                if isinstance(base_class, astroid.Attribute):
                                    base_class_name = base_class.attrname
                                # elif isinstance(baseclass, astroid.Name):
                                #     base_class_name = baseclass.name
                                else:
                                    base_class_name = base_class.name
                                if base_class_name:
                                    if base_class_name == "TestCase":
                                        modules.append(TestModule(f, module_text, module_node))
                                        # ladies and gentleman, we got him
            #     node = ast.parse(file.read())
            #
            # classes = [n for n in node.body if isinstance(n, ast.ClassDef)]
            # classes = [n for n in node.body if isinstance(n, ast.ClassDef)]
            #
            # for class_ in classes:
            #
            #     # super = class_.bases[0].value.id
            #     print("bases: ", [type(b) for b in class_.bases])
            #
            #     methods = [n for n in class_.body if isinstance(n, ast.FunctionDef)]
            #     for methodNode in methods:
            #         method_name = methodNode.name
            #         args = methodNode.args.args
        return modules


class Project(object):
    venv_folder_name = "venv"
    activate_this_file_name = "activate_this.py"
    bin_folder_name = "bin"

    def __init__(self, project_path):

        self.project_path = project_path
        self.project_name = os.path.dirname(self.project_path)
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

    def create_vevn(self):
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


def find_projects(root):
    return [Project(project_path) for project_path in listdir_fullpath(root)]


projects = find_projects("dataset")
p = projects[0]
# p.freeze()
# p.create_vevn()
# p.activate_venv()
# p.install_dependencies()


test_manager = TestManager(p)
test_modules = test_manager.find_test_modules()
for m in test_modules:
    print(m.file_path)

    for test_cls in m.test_classes:
        for function in test_cls.function_nodes:
            print(dir(function))



# def trace(f, *args):
#     def callback(frame, event, arg):
#         print(frame, event, arg)
#         print(frame.f_lineno)
#         code_obj = frame.f_code
#         print(code_obj.co_filename)
#         return callback
#
#     sys.settrace(callback)
#     f(*args)
#     sys.settrace(None)
