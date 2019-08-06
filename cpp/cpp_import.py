import os
import sys
from pathlib import Path
import cppimport

CPP_ROOT = Path(__file__).parent

def load_cpp_extension(ext_name):
    ext_root = _find(ext_name+".cpp", str(CPP_ROOT))
    sys.path.insert(0, ext_root)
    ext = cppimport.imp(ext_name)
    sys.path.remove(ext_root)
    return ext


def _find(name, path):
    for root, dirs, files in os.walk(path):
        if name in files:
            return root
