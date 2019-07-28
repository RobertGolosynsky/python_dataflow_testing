import sys
from collections import defaultdict
import os


class Tracer(object):

    trace_folder = ".traces"
    dict_file_ext = "dict"
    trace_file_ext = "trace"
    dict_file_name = "files"

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
        self.file_cache = []
        self.buff = []
        self.buff_size = 100000
        self.prev_trace_func = None
        self.current_trace_name = ""
        self.current_log_file = None
        os.makedirs(self.trace_folder, exist_ok=True)
        idx_file = self._index_file_path()
        self.index_file = open(idx_file, "w")

    def _index_file_path(self):
        file_name = self.dict_file_name+"."+self.dict_file_ext
        return os.path.join(self.trace_folder, file_name)

    def _trace_file_path(self, trace_name):
        file_name = trace_name + "." + self.trace_file_ext
        return os.path.join(self.trace_folder, file_name)

    def should_keep_fast(self, file):
        if file in self.keep_files:
            return True
        for keep_dir in self.keep_dirs:
            if file.startswith(keep_dir):
                return True
        return False

    def should_exclude_fast(self, file):
        if file in self.exclude_files:
            return True
        for exclude_dir in self.exclude_dirs:
            if file.startswith(exclude_dir):
                return True
        return False

    def _log_line(self, *args):
        self.current_log_file.write(", ".join(map(str, args))+"\n")

    def _log_new_file(self, *args):
        self.index_file.write(", ".join(map(str, args))+"\n")
        self.index_file.flush()

    def start(self, trace_name):
        self.prev_trace_func = sys.gettrace()
        self.current_trace_name = trace_name
        self.current_log_file = open(self._trace_file_path(self.current_trace_name), "w")
        sys.settrace(self._tracefunc)

    def stop(self):
        sys.settrace(self.prev_trace_func)
        self.current_trace_name = ""
        self.current_log_file.close()

    def trace(self, function_to_trace):
        self.log = list()
        self.log_by_file = defaultdict(list)
        sys.settrace(self._tracefunc)
        function_to_trace()
        sys.settrace(None)
        self.current_log_file.writelines(self.buff)
        return self.log

    def _tracefunc(self, frame, event, arg):

        if event == "call":
            self.scope_counter += 1
            self.scope_stack.append(self.scope_counter)

        scope = self.scope_stack[-1]
        code = frame.f_code
        line = frame.f_lineno

        fname = code.co_filename
        file_path = fname
        should_trace_deeper = False
        # file_path = Path(fname)
        # return self.tracefunc
        # TODO: figure out events, return seems to be irrelevant
        if self.should_keep_fast(file_path) and not self.should_exclude_fast(file_path):
            should_trace_deeper = True
            # if True:
            #     args = inspect.getargvalues(frame)
            # if self.interactive:
            #     code, start = inspect.getsourcelines(frame)
            #     for i, l in enumerate(code):
            #         cur = start+i
            #         prefix = "   "
            #         if cur == line:
            #             prefix = ">>>"
            #         print(prefix, cur, l, end="")
            #     print(args)
            #     print("Scope:", scope)
            #     print("Event:", event)
            #     input()
            # frame_self = id(args.locals["self"]) if "self" in args.locals else None

            frame_self = frame.f_locals.get("self", None)
            if frame_self:
                frame_self = id(frame_self)
            else:
                frame_self = -1

            if event == "line" or event == "call":
                if file_path in self.file_cache:
                    file_idx = self.file_cache.index(file_path)
                else:
                    self.file_cache.append(file_path)
                    file_idx = len(self.file_cache) - 1
                    self._log_new_file(file_idx, file_path)

                self._log_line(file_idx, line, frame_self, scope)
        if event == "return":
            self.scope_stack.pop()

        if should_trace_deeper:
            return self._tracefunc
