class Dict(object):

    def __init__(self):
        self.keys = []
        self.values = []

    def put(self, key, value):
        try:
            idx = self.keys.index(key)
            self.values[idx] = value
        except ValueError:
            self.keys.append(key)
            self.values.append(value)

    def get(self, key):
        val = None
        try:
            idx = self.keys.index(key)
            val = self.values[idx]
        except ValueError:
            pass

        return val

    def __len__(self):
        return len(self.keys)
