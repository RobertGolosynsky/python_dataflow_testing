import sys
from collections import defaultdict
from pathlib import Path
import os
import inspect


class Tracer(object):

    def __init__(self, keep, exclude):
        self.keep_dirs = [f for f in keep if os.path.isdir(f)]
        self.keep_files = [f for f in keep if os.path.isfile(f)]

        self.exclude_dirs = [f for f in exclude if os.path.isdir(f)]
        self.exclude_files = [f for f in exclude if os.path.isfile(f)]
        self.log = list()
        self.log_by_file = defaultdict(list)
        self.interactive = False
        self.scope_stack = list()
        self.scope_counter = 0
        self.scope_stack.append(self.scope_counter)

    def should_keep(self, file):
        if file in self.keep_files:
            return True
        for keep_dir in self.keep_dirs:
            if keep_dir in file.parents:
                return True
        return False

    def should_exclude(self, file):
        if file in self.exclude_files:
            return True
        for exclude_dir in self.exclude_dirs:
            if exclude_dir in file.parents:
                return True
        return False

    def trace(self, function_to_trace):
        self.log = list()
        self.log_by_file = defaultdict(list)
        sys.settrace(self.tracefunc)
        function_to_trace()
        sys.settrace(None)
        return self.log

    def tracefunc(self, frame, event, arg):
        if event == "call":
            self.scope_counter += 1
            self.scope_stack.append(self.scope_counter)

        scope = self.scope_stack[-1]
        code = frame.f_code
        line = frame.f_lineno

        fname = code.co_filename
        file_path = Path(fname)

        # TODO: figure out events, return seems to be irrelevant
        if self.should_keep(file_path) and not self.should_exclude(file_path):
            args = inspect.getargvalues(frame)
            if self.interactive:
                code, start = inspect.getsourcelines(frame)
                for i, l in enumerate(code):
                    cur = start+i
                    prefix = "   "
                    if cur == line:
                        prefix = ">>>"
                    print(prefix, cur, l, end="")
                print(args)
                print("Scope:", scope)
                print("Event:", event)
                input()
            frame_self = id(args.locals["self"]) if "self" in args.locals else None
            if event == "line" or event == "call":
                self.log.append((line, file_path, frame_self, scope))
                self.log_by_file[file_path].append((line, frame_self, scope))

        if event == "return":
            self.scope_stack.pop()

        return self.tracefunc


