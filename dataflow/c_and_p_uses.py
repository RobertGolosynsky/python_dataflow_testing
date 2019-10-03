import ast
from pprint import pprint
import itertools


# source = """
# a = 3
# if a>2:
#     print("")
# elif a<1:
#     pass
# else:
#     pass
# for x in range(a):
#     print(x)
#
# while a<5:
#     if a>0:
#         a-=1
#     print(a)
#
# def asd(a,b):
#     print(a.a1)
#
# class ABC:
#     def __init__(self, param):
#         self.param = param
#         a = self.param
#
# """

# tree = ast.parse(source)

class MyVisitor(ast.NodeVisitor):
    def __init__(self):
        self.p_uses = set()
        self.c_uses = set()

    def visit_If(self, node):
        for child in ast.walk(node.test):
            if isinstance(child, ast.Name):
                self.p_uses.add(child.lineno)
        for n in itertools.chain(node.body, node.orelse):
            self.generic_visit(n)

    def visit_For(self, node):
        for child in ast.walk(node.target):
            if isinstance(child, ast.Name):
                self.p_uses.add(child.lineno)
        for n in itertools.chain([node.iter], node.body, node.orelse):
            self.generic_visit(n)

    def visit_While(self, node):
        for child in ast.walk(node.test):
            if isinstance(child, ast.Name):
                self.p_uses.add(child.lineno)
        for n in itertools.chain(node.body, node.orelse):
            self.generic_visit(n)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.c_uses.add(node.lineno)


def get_all_c_all_p_uses(tree):
    v = MyVisitor()
    v.visit(tree)
    return v.c_uses, v.p_uses
