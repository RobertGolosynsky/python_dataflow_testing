import sys
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
        self.interactive = False

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
        sys.settrace(self.tracefunc)
        function_to_trace()
        sys.settrace(None)
        return self.log

    def tracefunc(self, frame, event, arg):
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
                print("Event: ", event)
                input()
            frame_self = args.locals["self"] if "self" in args.locals else None
            self.log.append((line, file_path, frame_self))
        else:
            return None

        return self.tracefunc


