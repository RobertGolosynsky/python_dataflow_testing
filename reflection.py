import importlib.util
import inspect


def load_module(module_path, under_name, path=None):
    spec = importlib.util.spec_from_file_location(under_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def module_functions(module):
    return [o for o in inspect.getmembers(module, inspect.isfunction)]


def module_classes(module):
    return [o for o in inspect.getmembers(module, inspect.isclass)]


def class_functions(cls):
    return [o for o in inspect.getmembers(cls, inspect.isroutine)]


def method_type(clazz, method):
    if method not in clazz.__dict__:  # Not defined in clazz : inherited
        return 'inherited'
    elif hasattr(super(clazz), method):  # Present in parent : overloaded
        return 'overridden'
    else:  # Not present in parent : newly defined
        return 'new'
#
# def is_defined_in_class(cls, fn):
#
#
# def is_inherited(cls, fn):
#     if fn not in cls.__dict__:
#         return True
#     return False
#
# def is_overridden(cls, fn):
#     if not is_inherited(cls, fn) and hasattr(super(cls), fn):