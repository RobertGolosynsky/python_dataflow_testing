import os
from pprint import pformat


class TestCase:

    after_path_sep = "@"
    after_class_sep = "+"
    path_sep = "-"

    def __init__(self, path, class_name, function_name):
        self.path = path
        self.class_name = class_name
        self.function_name = function_name

    def to_folder_name(self):
        sanitized_path = self.path.replace(os.path.sep, self.path_sep)
        return "".join([sanitized_path, self.after_path_sep, self.class_name,
                        self.after_class_sep, self.function_name])

    @classmethod
    def from_folder_name(cls, folder_name):
        encoded_path, suffix = folder_name.split(cls.after_path_sep)
        path = encoded_path.replace(cls.path_sep, os.path.sep)
        class_name, function_name = suffix.split(cls.after_class_sep)
        return TestCase(path, class_name, function_name)

    def to_node_id(self):
        return self.path+"::"+self.class_name+"::"+self.function_name

    def __hash__(self):
        return hash(self.path) + hash(self.class_name) + hash(self.function_name)

    def __eq__(self, other):
        return self.path == other.path and \
               self.class_name == other.class_name and \
               self.function_name == other.function_name

    def __repr__(self) -> str:
        return self.to_folder_name()

