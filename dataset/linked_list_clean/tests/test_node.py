import unittest
from core.node import Node


class TestNode(unittest.TestCase):

    def test_create(self):
        node = Node(0, None)
        self.assertEqual(0, node.el)
        self.assertEqual(None, node.next)
