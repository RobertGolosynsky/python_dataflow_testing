import ast
import operator
import os
import unittest
from pathlib import Path

from util.astroid_util import find_class_with_name, functions_of, get_calls

here = Path(os.path.realpath(__file__)).parent
this_project_root = here.parent.parent

inter_method_root = this_project_root / "dataset/inter_method"
inter_method = inter_method_root / "module.py"

class TestCallOrder(unittest.TestCase):

    def setUp(self) -> None:
        with open(inter_method) as f:
            module_ast = ast.parse(f.read())
        class_ast = find_class_with_name("HasIntermethod", module_ast)
        self.methods = {function_def.name: function_def for function_def in functions_of(class_ast)}

    @staticmethod
    def calls_to_call_order(calls):
        call_order = []
        print(calls)
        for call in sorted(calls, key=operator.itemgetter(1), reverse=True):
            call_order.append(call[2])
        print(call_order)
        return call_order

    def test_one_after_another_in_if_multiline(self):
        expected_call_order = ["self.one", "self.two"]
        method = self.methods["multiline_if"]
        self.assertEqual(expected_call_order, self.calls_to_call_order(get_calls(method)))

    def test_inside_first_left_to_right(self):
        expected_call_order = ["self.one",
                               "self.two",
                               "self.a2",
                               "self.two",
                               "self.a1",
                               "list",
                               "self.a3"
                               ]
        method = self.methods["one_in_another"]
        self.assertEqual(expected_call_order, self.calls_to_call_order(get_calls(method)))

    def test_inside_first_left_to_right_multiline(self):
        expected_call_order = ["self.one",
                               "self.two",
                               "self.a2",
                               "self.two",
                               "self.a1",
                               "list",
                               "self.a3"
                               ]
        method = self.methods["one_in_another_multiline"]
        self.assertEqual(expected_call_order, self.calls_to_call_order(get_calls(method)))

    def test_inside_first_left_to_right_multiline_bad_formatting(self):
        expected_call_order = ["self.one",
                               "self.two",
                               "self.a2",
                               "self.two",
                               "self.a1",
                               "list",
                               "self.a3"
                               ]
        method = self.methods["one_in_another_multiline_bad_formatting"]
        self.assertEqual(expected_call_order, self.calls_to_call_order(get_calls(method)))

    def test_list_comprehension_inside_first(self):
        expected_call_order = ["self.returns_a_list", "self.a1"]
        method = self.methods["call_inside_comprehension"]
        self.assertEqual(expected_call_order, self.calls_to_call_order(get_calls(method)))
