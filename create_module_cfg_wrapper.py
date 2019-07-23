

import importlib.util
import sys

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


print(sys.argv)

print("Modules loaded ", len(sys.modules.keys()))

module_path = sys.argv[1]
project_path = sys.argv[2]
cfg_path = sys.argv[3]


sys.path.insert(0, project_path)

# mods = sys.modules.copy()
to_remove = set()
for module_name in sys.modules:
    if module_name not in standard_modules:
        to_remove.add(module_name)

for module_name in to_remove:
    del sys.modules[module_name]

print("Standard modules len", len(standard_modules))
print("Modules loaded ", len(sys.modules.keys()))

spec = importlib.util.spec_from_file_location("some name", module_path)
module = importlib.util.module_from_spec(spec)

spec.loader.exec_module(module)

to_remove = set()
for module_name in sys.modules:
    if module_name not in standard_modules:
        to_remove.add(module_name)

for module_name in to_remove:
    del sys.modules[module_name]


import inspect
import pickle
import ast
print("Modules loaded ", len(sys.modules.keys()))
# for module_name in mods:
#     sys.modules[module_name] = mods[module_name]
# print("Modules loaded ", len(sys.modules.keys()))
exit()
# m = ModuleCFG(module_path)
# with open(cfg_path, "wb") as wtf:
#     pickle.dump(m, wtf)
