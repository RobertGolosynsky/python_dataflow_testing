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

    def test_append_on_removed(self):
        ll = LinkedList()
        ll.append(1)
        ll.remove(0)
        ll.append(2)
        self.assertEqual(ll.get(0), 2)

    def test_remove_when_empty(self):
        ll = LinkedList()
        self.assertRaises(IndexError, ll.remove, 0)

    def test_remove_when_not_empty(self):
        ll = LinkedList()
        ll.append(2)
        ll.remove(0)
        self.assertRaises(IndexError, ll.get, 0)

    def test_remove_twice_when_not_empty(self):
        ll = LinkedList()
        ll.append(2)
        ll.append(2)
        ll.remove(0)
        ll.remove(0)
        self.assertEquals(0, ll.len())

    def test_remove_middle(self):
        ll = LinkedList()
        ll.append(1)
        ll.append(2)
        ll.append(3)
        ll.remove(1)
        self.assertEquals(3, ll.get(1))

    def test_remove_first_append(self):
        ll = LinkedList()
        ll.append(1)
        ll.append(2)
        ll.append(3)
        ll.remove(0)
        ll.append(4)
        self.assertEquals([2, 3, 4], ll.as_list())

    def test_len(self):
        ll = LinkedList()
        ll.append(1)
        ll.append(1)
        ll.remove(0)
        self.assertEqual(ll.len(), 1)

    def test_len_on_empty(self):
        ll = LinkedList()
        self.assertEqual(ll.len(), 0)

    def test_len_large_list(self):
        l = [1] * 100
        ll = LinkedList(l)

        self.assertEqual(ll.len(), len(l))

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

    def test_get_middle(self):
        ll = LinkedList()
        ll.append(0)
        ll.append(1)
        ll.append(2)
        ll.append(3)
        ll.append(4)
        self.assertEqual(ll.get(2), 2)

    def test_create_from_list(self):
        l = [1, 2, 3]
        ll = LinkedList(l)
        for i in range(len(l)):
            self.assertEqual(l[i], ll.get(i))

    def test_as_list(self):
        l = [1, 2, 3]
        ll = LinkedList(l)
        self.assertEquals(l, ll.as_list())

    def test_as_list_on_empty(self):
        ll = LinkedList()
        self.assertEquals([], ll.as_list())

    def test_remove_first_as_list(self):
        ll = LinkedList()
        ll.append(1)
        ll.append(2)
        ll.append(3)
        ll.remove(0)
        self.assertEquals([2, 3], ll.as_list())


if __name__ == '__main__':
    unittest.main()
