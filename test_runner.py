
import sys
from pathlib import Path
import os
from collections import defaultdict


class Tracer(object):

    def __init__(self, keep, exclude):
        self.keep_dirs = [f for f in keep if os.path.isdir(f)]
        self.keep_files = [f for f in keep if os.path.isfile(f)]

        self.exclude_dirs = [f for f in exclude if os.path.isdir(f)]
        self.exclude_files = [f for f in exclude if os.path.isfile(f)]

        self.log = defaultdict(list)

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
        self.log = defaultdict(list)
        sys.settrace(self.tracefunc)
        function_to_trace()
        sys.settrace(None)
        return self.log

    def tracefunc(self, frame, event, arg):
        # if event == "line":
        # indent[0] += 2

        code = frame.f_code
        line = frame.f_lineno
        fname = code.co_filename
        # print(fname, line)
        file_path = Path(fname)

        if self.should_keep(file_path) and not self.should_exclude(file_path):
            # if Path(parent) in file_path.parents and exclude not in file_path.parents:
            self.log[file_path].append(line)
        else:
            return None
        # elif event == "return":
        #     print("<" + "-" * indent[0], "exit function", frame.f_code.co_name)
        #     indent[0] -= 2
        return self.tracefunc




# def tracefunc(frame, event, arg, indent=[0]):
#     if event == "line":
#         indent[0] += 2
#         code = frame.f_code
#         line = frame.f_lineno
#         fname = code.co_filename
#
#     elif event == "return":
#         print("<" + "-" * indent[0], "exit function", frame.f_code.co_name)
#         indent[0] -= 2
#     return tracefunc


#
# def tracefunc(frame, event, arg, indent=[0]):
#     if event == "call":
#         indent[0] += 2
#         code = frame.f_code
#         print("-" * indent[0] + "> call function", frame.f_code.co_name, code.co_filename)
#     elif event == "return":
#         print("<" + "-" * indent[0], "exit function", frame.f_code.co_name)
#         indent[0] -= 2
#     return tracefunc




