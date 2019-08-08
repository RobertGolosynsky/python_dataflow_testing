import unittest
from core import LinkedList


class LinkedListTest(unittest.TestCase):

    def test_append_when_empty(self):
        ll = LinkedList()
        ll.append(1)
        self.assertEqual(ll.get(0), 1)

    def test_append_when_not_empty(self):
        ll = LinkedList()
        ll.append(1)
        ll.append(2)
        self.assertEqual(ll.get(1), 2)

    def test_remove_when_empty(self):
        ll = LinkedList()
        self.assertRaises(IndexError, ll.remove, 0)

    def test_remove_when_not_empty(self):
        ll = LinkedList()
        ll.append(2)
        ll.remove(0)
        self.assertRaises(IndexError, ll.get, 0)

    def test_len(self):
        ll = LinkedList()
        ll.append(2)
        self.assertEqual(ll.len(), 1)

    def test_get(self):
        ll = LinkedList()
        a = 2
        ll.append(a)
        self.assertEqual(ll.get(0), a)

    def test_get_empty(self):
        ll = LinkedList()
        self.assertRaises(IndexError, ll.get, 0)

    def test_get_out_bounds(self):
        ll = LinkedList()
        x = 10
        for i in range(x):
            ll.append(i)
        self.assertRaises(IndexError, ll.get, x)

    def test_create_from_list(self):
        l = [1, 2, 3]
        ll = LinkedList(l)
        for i in range(len(l)):
            self.assertEqual(l[i], ll.get(i))


if __name__ == '__main__':
    unittest.main()
