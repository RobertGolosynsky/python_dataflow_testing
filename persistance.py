import os
import pickle
from pathlib import Path
from my_manager import TestManager



manager_file_ext = "mgr"
managers_folder = Path("./managers")


def manager_file_name(mngr):
    project_name = mngr.project.project_name
    return "{}.{}".format(project_name, manager_file_ext)


def save_test_manager(mngr: TestManager):
    os.makedirs(managers_folder, exist_ok=True)
    pickle.dump(mngr, open(managers_folder/manager_file_name(mngr), "wb"))


def load_test_managers() -> [TestManager]:
    managers = []
    for file in listdir_fullpath(managers_folder):
        mngr = pickle.load(open(file, "rb"))
        managers.append(mngr)
    return managers


def listdir_fullpath(d):
    return [os.path.join(d, f) for f in os.listdir(d)]

