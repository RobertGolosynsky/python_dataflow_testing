import importlib.util
import sys
from pathlib import Path

from persistance import save_test_manager
from test_manager import find_projects, TestManager
from tracer import Tracer

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
