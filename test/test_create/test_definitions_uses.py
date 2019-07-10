import unittest
import networkx as nx

from test.test_create.test_graphs_create import is_isomorphic_with_data, functions_to_dis, check_against_saved
from graphs.create import try_create_cfg
from dataflow.def_use import try_create_cfg_with_definitions_and_uses


class TestDefinitionUsePairs(unittest.TestCase):

    def test_def_use_pairs(self):

        def node_match(n1, n2):

            for key in n1:
                attr1 = n1[key]
                attr2 = n2[key]

                if type(attr1) == nx.DiGraph:
                    if not is_isomorphic_with_data(attr1, attr2):

                        return False
                else:
                    if not attr1 == attr2:
                        return False
            return True

        module = nx
        functions, names = functions_to_dis(module)
        cutoff = 10

        def checker(true_, actual):
            if true_:
                self.assertTrue(nx.is_isomorphic(true_, actual, node_match=node_match))

        def mapper(func):

            g = try_create_cfg_with_definitions_and_uses(func)
            # lines, start = inspect.getsourcelines(func)
            # dump(g, start, lines, attr_keys=[DEFINITIONS_KEY, USES_KEY])

            return g

        check_against_saved(
            functions[:cutoff],
            mapper,
            checker,
            names[:cutoff],
            "true_line_cfgs_with_def_use",
            save=True
        )
