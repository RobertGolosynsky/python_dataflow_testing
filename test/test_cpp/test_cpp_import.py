import unittest

from cpp.cpp_import import load_cpp_extension


class TestImportMatcherExt(unittest.TestCase):

    def test_import_matcher_ext(self):
        ext = load_cpp_extension("matcher_ext")
        self.assertIsNotNone(ext)

    def test_import_def_use_pairs_ext(self):
        ext = load_cpp_extension("def_use_pairs_ext")
        self.assertIsNotNone(ext)
