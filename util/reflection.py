import importlib.util
import inspect
import os.path

DEFINED = "defined"
INHERITED = "inherited"
OVERRIDDEN = "overridden"


def try_load_module(module_path, under_name=None):
    if not under_name:
        under_name = os.path.basename(module_path)
    try:
        spec = importlib.util.spec_from_file_location(under_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except:
        raise
        raise NotImplementedError("There was a problem loading module")

    return module


def module_functions(module):
    return [f_name for f_name, f_descriptor in inspect.getmembers(module, inspect.isfunction)
            if inspect.getmodule(f_name) == module]


def module_classes(module):
    return [m for m in inspect.getmembers(module, inspect.isclass)
            if m[1].__module__ == module.__name__]


def class_functions(cls, m_type=None):
    if m_type:
        return [m for m in class_functions(cls) if method_type(cls, m) == m_type]
    return [f_name for f_name, _ in inspect.getmembers(cls, inspect.isroutine)]


def method_type(cls, method):
    if method not in cls.__dict__:  # Not defined in cls : inherited
        return INHERITED
    elif hasattr(super(cls), method):  # Present in parent : overloaded
        return OVERRIDDEN
    else:  # Not present in parent : newly defined
        return DEFINED


def get_class_function(module, class_name, function_name):
    cls_obj = getattr(module, class_name)
    return getattr(cls_obj, function_name)
