import importlib.util
import sys
from collections import defaultdict

from pathlib import Path

from networkx.drawing.nx_agraph import graphviz_layout
import matplotlib.pyplot as plt

import persistance
import module_cfg
import networkx as nx

from draw import draw
from new_def_use import definition_use_pairs, Trace

managers = persistance.load_test_managers()

test_manager = managers[0]
project = test_manager.project

a_module = test_manager.tests[0]
module_path = a_module.file_path
sys.path.insert(0, project.project_path)

spec = importlib.util.spec_from_file_location("test_module", module_path)
test_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(test_module)

test_class = a_module.test_classes[0]
cfg = module_cfg.ModuleCFG(Path("dataset/linked_list/core/ll.py"))

pairs = cfg.def_use()
one = cfg.as_one()
draw(one, [(x.line, y.line) for x, y in pairs], [x.raw_var for x, y in pairs])
# a = 1/0

def print_instructions(instrs):
    for i in instrs:
        print(i)

trace = []

for manager in managers:
    for test_module in manager.tests:
        for test_class in test_module.test_classes:
            pairs = []
            for fn in test_class.function_nodes:
                trace = Trace()
                print("Tracing", fn.name)
                for line, file, id_, scope in test_class.trace[fn]:
                    line_key = str(line)

                    deffs = cfg.defs_for_line(str(line))
                    uses = cfg.uses_for_line(str(line))
                    if len(deffs) == 0 and len(uses) == 0:
                        print("no instructions on line", line)
                    else:
                        deffs = [d.raw_var for d in deffs]
                        uses = [u.raw_var for u in uses]
                        trace.add_trace(line, file, list(deffs), list(uses), id_=id_, scope=str(scope))


                print("--------------"*5)
                pairs.extend(definition_use_pairs(trace))

            one = cfg.as_one()
            print("aaaaaaa"*5)
            print(pairs)

            draw(one, [(x.line, y.line) for x, y in pairs], [x.raw_var for x, y in pairs])




"""
1. 
self.a = new_a
c = self.a
2.
self.a = new_a
x = self.a.b 
3. 
self.a = new_a
if m:
    self.a.b = 3 <
x = self.a.b <
4.
self.a = new_a <
self.a.x() <
5. 
self.a = new_a <
self.a.b = new_b - this will be checked on the level of that class
self.a.x() <
6.
self.a = new_a
self.a.b = new_b
self.a = new_a <
x = self.a.b <
7.



// unresolved

node = self.get_next()

if x:
    v = node.a
    v.b = 3

x = node.a.b

"""