import os
import sys
import pickle
import importlib.util
from pathlib import Path
from test_runner import Tracer
from test_manager import TestManager, find_projects

from util import listdir_fullpath



"""
if a test function has 2 target objects of same class simple tracing (line num) is indecisive
we should distinguish a method calls by the specific object they were called from 
1. add object reference to a trace (object memory address), to disambiguate "self"
2. create module level cfg (functions and classes)
3. find def-use pairs having a trace [(obj_addr, file, line)] and a module cfg

"""



manager_file_ext = "mgr"
managers_folder = Path("./managers")


def manager_file_name(mngr):
    project_name = mngr.project.project_name
    return "{}.{}".format(project_name, manager_file_ext)


def save_test_manager(mngr: TestManager):
    os.makedirs(managers_folder, exist_ok=True)
    pickle.dump(mngr, open(managers_folder/manager_file_name(mngr), "wb"))


def load_test_managers():
    managers = []
    for file in listdir_fullpath(managers_folder):
        mngr = pickle.load(open(file, "rb"))
        managers.append(mngr)
    return managers





project = find_projects("dataset")[0]
test_manager = TestManager(project)
test_modules = test_manager.find_test_modules()

a_module = test_modules[0]
module_path = a_module.file_path
sys.path.insert(0, project.project_path)

spec = importlib.util.spec_from_file_location("test_module", module_path)
test_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(test_module)

test_class = a_module.test_classes[0]
test_class_name = test_class.test_class_name()

print(test_class_name)
print(dir(test_module))
test_case_constructor = getattr(test_module, test_class_name)

test_case = test_case_constructor()

tracer = Tracer([Path(project.project_path)], [Path(test_class.file_path)])
for function in test_class.function_nodes:
    func_name = function.name
    test_function = getattr(test_case, func_name)
    traced_path = tracer.trace(test_function)
    test_class.add_trace(function, traced_path)


# test_class.report_class()

print(test_manager.project.project_name)
save_test_manager(test_manager)
