import ast
import dis
import os
import time
import unittest
from collections import defaultdict
from pathlib import Path

from graphs.create import try_create_cfg, LINE_KEY, INSTRUCTION_KEY
import operator
import util.astroid_util as au

here = Path(os.path.realpath(__file__)).parent
this_project_root = here.parent

linked_list_root = this_project_root / "dataset/inter_method"
linked_list = linked_list_root / "module.py"


class TestAstCFG(unittest.TestCase):

    def test_call_sequence(self):
        module = str(linked_list)
        with open(module) as f:
            lines = f.read()
        tree = ast.parse(lines)
        calls = au.get_calls(tree)

        for c in calls:
            print(c)

        call_dict = defaultdict(list)
        for line, idx, fname in calls:
            call_dict[line].append((idx, fname))

        fns, clss, calls = au.compile_module(module)
        cls = clss["HasIntermethod"]
        cfg = None
        for function in cls:

            if function.func.__name__ == "a":
                time.sleep(0.1)
                dis.dis(function.func)
                cfg = try_create_cfg(function.func, function.first_line, function.argument_names)
        if cfg:
            # assumes nodes are sorted by the bytecode offset
            for node, data in cfg.g.nodes(data=True):
                line = data.get(LINE_KEY)
                if line:
                    inst = data.get(INSTRUCTION_KEY)
                    if inst:
                        opname = inst.opname
                        if opname.startswith("CALL_"):
                            calls_on_line = call_dict.get(line)
                            if calls_on_line:
                                if len(calls_on_line) == 1:
                                    _, fname = calls_on_line[0]
                                    del calls_on_line[0]
                                    data["calls"] = fname
                                else:

                                    index, value = max(enumerate(calls_on_line), key=operator.itemgetter(0))

                                    print(line ,value)
                                    _, fname = value
                                    data["calls"] = fname
                                    del calls_on_line[index]

            for node, data in cfg.g.nodes(data=True):
                print(node, ":", data)

