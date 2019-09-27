import unittest
from pathlib import Path

from experiment.core.mutation import killed_mutants
from tracing.trace_reader import TraceReader


class TestMutation(unittest.TestCase):

    def test_mutate_linked_list_module(self):
        project_root = Path(__file__).parent.parent.parent / "dataset/linked_list_clean"
        module_under_test_path = project_root / "core" / "ll.py"

        trace_reader = TraceReader(project_root)
        not_failing_node_ids = trace_reader.get_not_failing_node_ids(module_under_test_path)

        killed, total = killed_mutants(
            project_root=str(project_root),
            module_under_test_path=str(module_under_test_path),
            not_failing_node_ids=not_failing_node_ids,
            timeout=None
        )
        s = set()
        for m in killed.values():
            s.update(m)
        self.assertEqual(46, total)
        self.assertEqual(30, len(s))
