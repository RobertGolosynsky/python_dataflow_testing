import importlib.util
import inspect
import os.path
import sys

DEFINED = "defined"
INHERITED = "inherited"
OVERRIDDEN = "overridden"

standard_modules = [
    'builtins',
    'sys',
    '_frozen_importlib', '_imp',
    '_warnings', '_thread', '_weakref',
    '_frozen_importlib_external', '_io', 'marshal', 'posix', 'zipimport',
    'encodings', 'codecs', '_codecs', 'encodings.aliases', 'encodings.utf_8',
    '_signal', '__main__', 'encodings.latin_1', 'io', 'abc', '_weakrefset', 'site', 'os', 'errno',
    'stat', '_stat', 'posixpath', 'genericpath', 'os.path', '_collections_abc', '_sitebuiltins',
    'sysconfig', '_sysconfigdata_m_linux_x86_64-linux-gnu', '_bootlocale', '_locale', 'types',
    'functools', '_functools', 'collections', 'operator', '_operator', 'keyword', 'heapq', '_heapq',
    'itertools', 'reprlib', '_collections', 'weakref', 'collections.abc', 'importlib',
    'importlib._bootstrap', 'importlib._bootstrap_external', 'warnings', 'importlib.util',
    'importlib.abc', 'importlib.machinery', 'contextlib', 'mpl_toolkits', 'zope', 'sitecustomize',
    'encodings.cp437',
    'apport_python_hook'
]


def try_load_module(module_path, under_name=None):
    print("Loading module {}".format(module_path))
    if not under_name:
        # under_name = os.path.basename(module_path)
        under_name = "some_random_name"
    try:

        # print("Modules loaded ", len(sys.modules.keys()))
        mods = sys.modules.copy()
        to_remove = set(sys.modules.keys())
        to_remove = to_remove.difference(standard_modules)
        #
        for module_name in to_remove:
            del sys.modules[module_name]
        print("Modules loaded ", len(sys.modules.keys()))
        sys.modules.clear()
        spec = importlib.util.spec_from_file_location(under_name, module_path)
        module = importlib.util.module_from_spec(spec)
        # print("loader", type(spec.loader), spec.loader)

        spec.loader.exec_module(module)
        sys.modules.clear()
        # print("Modules loaded ", len(sys.modules.keys()))
        for module_name in mods:
            sys.modules[module_name] = mods[module_name]
        # print("Modules loaded ", len(sys.modules.keys()))

    except Exception as e:
        print(e)
        raise

        raise NotImplementedError("There was a problem loading module {}".format(module_path))

    return module


def module_functions(module):
    return [m[0] for m in inspect.getmembers(module, inspect.isfunction)
            if m[1].__module__ == module.__name__]


def module_classes(module):
    return [m for m in inspect.getmembers(module, inspect.isclass)
            if m[1].__module__ == module.__name__]


def class_functions(cls, m_type=None):
    if m_type:
        return [m for m in class_functions(cls) if method_type(cls, m) == m_type]

    def predicate(x):
        return inspect.isroutine(x) and inspect.isfunction(x)

    return [f_name for f_name, _ in inspect.getmembers(cls, predicate)]


def method_type(cls, method):
    if method not in cls.__dict__:  # Not defined in cls : inherited
        return INHERITED
    else:
        for base in cls.__bases__:
            if hasattr(base, method):  # Present in a parent : overloaded
                return OVERRIDDEN
        return DEFINED


def get_class_function(module, class_name, function_name):
    cls_obj = getattr(module, class_name)
    return getattr(cls_obj, function_name)
