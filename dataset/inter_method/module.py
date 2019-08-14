class HasIntermethod:

    def a(self):
        c = self.a3()
        if self.a1(2):
            print("If one func")

        if self.a1(1) or self.a2(1, 2):
            print("If 'or' funcs ")

        if self.a1(1) and self.a2(1, 2) and self.a3(1, 2, 3):
            print("If 'and' funcs ")

        if self.a([el for el in list()]) == 0:
            print("if iter sum")
        x = self.a1(self.a2(self.a1(1), self.a3(1, 2, 3)))
        something = bool(random.getrandbits(1))
        res = self.a1(1) if something else self.a2(1, 2)

        return x

    def a1(self, p1):
        return 1

    def a2(self, p1, p2):
        return 1

    def a3(self, p1, p2, p3):
        return 1
