import unittest
from pathlib import Path

from experiment.mutation import killed_mutants


class TestMutation(unittest.TestCase):

    def test_mutate_linked_list_module(self):
        root = Path(__file__).parent.parent.parent / "dataset/linked_list_clean"
        module_under_test = root / "core" / "ll.py"

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

        killed, total = killed_mutants(
            project_root=str(root),
            path_to_module_under_test=str(module_under_test),
            test_cases_ids=cases.split()
        )
        s = set()
        for m in killed.values():
            s.update(m)
        self.assertEqual(46, total)
        self.assertEqual(30, len(s))