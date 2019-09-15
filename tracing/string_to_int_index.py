import json
from collections import defaultdict


class StringToIntIndex:

    def __init__(self, d=None):
        self.index = {}
        self.reverse_index = {}
        if not d:
            self.last_index = -1
        else:
            self.index.update(d)
            self.reverse_index = {v: k for k, v in d.items()}
            self.last_index = max(d.values())

    def get_or_create_int(self, s):
        if s in self.index:
            return self.index[s]
        else:
            self.last_index += 1
            self.index[s] = self.last_index
            self.reverse_index[self.last_index] = s
            return self.last_index

    def get_int(self, s):
        if s in self.index:
            return self.index[s]

    def get_string(self, i):
        if i in self.reverse_index:
            return self.reverse_index[i]

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {k: v for k, v in self.index.items()},
                f,
                indent=2
            )

    def keys(self):
        return self.index.keys()

    @staticmethod
    def load(path):
        with open(path, encoding="utf-8") as f:
            file_dict = json.load(f)
            return StringToIntIndex({k: int(v) for k, v in file_dict.items()})
