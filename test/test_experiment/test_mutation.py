import unittest
from pathlib import Path

from experiment.mutation import run_mutation


class TestMutation(unittest.TestCase):

    def test_mutate_linked_list_module(self):
        root = Path("/home/robert/Documents/master/code/python_dataflow_testing/dataset/linked_list_mutmut")
        module_under_test = Path("core") / "ll.py"
        tests_dir = Path("tests")
        test_result = run_mutation(project_root=root,
                                   module_under_test=module_under_test,
                                   tests_root=tests_dir,
                                   test_cases=[]
                                   )

        self.assertEqual(45, test_result.total)
        self.assertEqual(33, test_result.killed_mutants)
        self.assertEqual(11, test_result.surviving_mutants)
        self.assertEqual(1, test_result.surviving_mutants_timeout)
        self.assertEqual(0, test_result.suspicious_mutants)
