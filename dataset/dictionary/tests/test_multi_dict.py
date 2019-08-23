import unittest
from core.multi import MultiDict


class MultiDictTest(unittest.TestCase):

    def test_put_get(self):
        d = MultiDict()
        k = "key"
        v = "some value"
        d.put(k, v)
        self.assertEqual(v, d.get(k)[0])

    def test_put_get_2(self):
        d = MultiDict()
        k = "key"
        v = "some value"
        d.put(k, v)
        d.put(k, v)
        self.assertEqual(2, len(d.get(k)))

    def test_len(self):
        d = MultiDict()
        l = 10
        for i in range(l):
            d.put(i, i)
        self.assertEqual(l, len(d))

    def test_get_key_not_exist(self):
        d = MultiDict()
        value = d.get("some key")
        self.assertEqual(None, value)


if __name__ == '__main__':
    unittest.main()
