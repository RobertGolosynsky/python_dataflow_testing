import core.my_dict as md


class MultiDict(md.Dict):

    def __init__(self):
        super().__init__()

    def clear(self):
        self.keys = []
        self.values = []

    def put(self, key, value):
        if key in self.keys:
            idx = self.keys.index(key)
            self.values[idx].append(value)
        else:
            self.keys.append(key)
            self.values.append([value])

    def items(self):
        values = []
        keys = []
        for idx, key in enumerate(self.keys):
            for value in self.values[idx]:
                keys.append(key)
                values.append(value)
        return zip(keys, values)
