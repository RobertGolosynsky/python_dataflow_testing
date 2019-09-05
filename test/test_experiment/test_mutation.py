import unittest
from pathlib import Path

from experiment.mutation import run_mutation


class TestMutation(unittest.TestCase):

    def test_mutate_linked_list_module(self):
        root = Path("/home/robert/Documents/master/code/python_dataflow_testing/dataset/linked_list_mutmut")
        module_under_test = Path("core") / "ll.py"
        tests_dir = Path("tests")

        cases = """
tests/test_list.py::LinkedListTest::test_append_on_removed
tests/test_list.py::LinkedListTest::test_append_when_empty
tests/test_list.py::LinkedListTest::test_append_when_not_empty
tests/test_list.py::LinkedListTest::test_as_list
tests/test_list.py::LinkedListTest::test_as_list_on_empty
tests/test_list.py::LinkedListTest::test_create_from_list
tests/test_list.py::LinkedListTest::test_get
tests/test_list.py::LinkedListTest::test_get_empty
tests/test_list.py::LinkedListTest::test_get_middle
tests/test_list.py::LinkedListTest::test_get_out_bounds
tests/test_list.py::LinkedListTest::test_len
tests/test_list.py::LinkedListTest::test_len_large_list
tests/test_list.py::LinkedListTest::test_len_on_empty
tests/test_list.py::LinkedListTest::test_remove_first_append
tests/test_list.py::LinkedListTest::test_remove_first_as_list
tests/test_list.py::LinkedListTest::test_remove_middle
tests/test_list.py::LinkedListTest::test_remove_twice_when_not_empty
tests/test_list.py::LinkedListTest::test_remove_when_empty
tests/test_list.py::LinkedListTest::test_remove_when_not_empty
tests/test_node.py::TestNode::test_create
"""
        test_result = run_mutation(project_root=root,
                                   module_under_test=module_under_test,
                                   tests_root=tests_dir,
                                   test_cases=cases.split(),
                                   no_cache=True
                                   )

        self.assertEqual(45, test_result.total)
        self.assertEqual(33, test_result.killed_mutants)
        self.assertEqual(11, test_result.surviving_mutants)
        self.assertEqual(1, test_result.surviving_mutants_timeout)
        self.assertEqual(0, test_result.suspicious_mutants)
