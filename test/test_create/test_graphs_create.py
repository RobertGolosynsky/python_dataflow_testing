import os
import unittest
import pickle
import networkx as nx
import inspect
from graphs.create import _try_create_byte_offset_cfg

import dataflow.def_use as du
from util import reflection


def is_isomorphic_with_data(g1, g2):
    def node_match(n1, n2):
        for key in n1:
            attr1 = n1[key]
            attr2 = n2[key]
            if not attr1 == attr2:
                return False
        return True

    return nx.is_isomorphic(g1, g2, node_match=node_match)


def check_against_saved(to_map, map_function, check, names, prefix, save = False):
    os.makedirs(prefix, exist_ok=True)
    for item, name in list(zip(to_map, names)):
        if save:
            with open(os.path.join(prefix, name), "wb") as f:
                processed = map_function(item)

                pickle.dump(processed, f)
                print(f)

        with open(os.path.join(prefix, name), "rb") as f:
            expected_obj = pickle.load(f)
            check(expected_obj, map_function(item))


def functions_to_dis(module):
    functions = []
    names = []
    for func_name in dir(module):
        func = getattr(module, func_name)

        if inspect.isfunction(func):
            names.append(func_name)
            functions.append(func)

    return functions, names


class TestGraphsCreate(unittest.TestCase):

    def test_create_byte_code_cfg(self):
        module = nx
        cutoff = 10
        functions, names = functions_to_dis(module)

        def checker(expected, actual):
            if expected:
                self.assertTrue(is_isomorphic_with_data(expected, actual))

        def mapper(func):

            return _try_create_byte_offset_cfg(func)

        check_against_saved(
            functions[:cutoff],
            mapper,
            checker,
            names[:cutoff],
            "expected_cfgs",
            save=True
        )

