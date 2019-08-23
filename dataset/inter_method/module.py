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

    def m1(self):
        self.v1 = 1
        self.m2()
        self.m3()
        print(self.v1)

    def m2(self):
        self.m4()
        return 1

    def m3(self):
        self.m2()
        self.v1 = 2
        self.m2()
        return 2

    def m4(self):
        return 1

    def g1(self):
        if self.bigger(self.one(), self.two()):
            wow_such_deep = 1
            return wow_such_deep
        return None

    def bigger(self, a, b):
        return a > b

    def one(self):
        return 1

    def two(self):
        return 2

    def three(self):
        return 3

    def x(self):
        self.b = 1
        self.y()

    def y(self):
        print(self.b)
        # self.x()

    def recursive(self, a):
        if a > 3:
            self.recursive(a - 1)
        return a - 1

    def f1(self):
        self.f2()

    def f2(self):
        self.f3()

    def f3(self):
        print("end")

    def multiple_calls_in_if(self):
        if self.one() or self.two():
            return 1

    def multiline_if(self):
        if self.one() or \
                self.two():
            x = 1

    def one_in_another(self):
        self.a3(self.a2(self.one(), self.two()), self.a1(self.two()), list())

    def one_in_another_multiline(self):
        self.a3(
            self.a2(self.one(), self.two()),
            self.a1(self.two()),
            list()
        )

    def one_in_another_multiline_bad_formatting(self):
        self.a3(self.a2(self.one(),
                        self.two()),
                self.a1(
                    self.two()), list()
                )

    def returns_a_list(self):
        return [1, 2, 3]

    def call_inside_comprehension(self):
        x = self.a1([y for y in self.returns_a_list()])

    def interclass_only(self):
        self.l1 = 1
        x = 3
        self.ic1()
        self.ic2()
        print(self.l1)
        print(y)

    def ic1(self):
        print(x)
        self.l2 = self.l1

    def ic2(self):
        print(x)
        y = 1
        print(self.l2)
