import unittest
from core.my_dict import Dict


class DictTest(unittest.TestCase):

	def test_put_get(self):
		d = Dict()
		k = "key"
		v = "some value"
		d.put(k, v)
		self.assertEqual(v, d.get(k))

	def test_len(self):
		d = Dict()
		l = 10
		for i in range(l):
			d.put(i, i)
		self.assertEqual(l, len(d))

	def test_get_key_not_exist(self):
		d = Dict()
		value = d.get("some key")
		self.assertEqual(None, value)


if __name__ == '__main__':
	unittest.main()
