import inspect
from collections import defaultdict

from loguru import logger
import sys
import os
import json
from time import time
from cpp.cpp_import import load_cpp_extension

import shutil

matcher_ext = load_cpp_extension("matcher_ext")


class Tracer(object):
    trace_file_ext = "trace"
    scopes_file_ext = "scopes"
    files_index_file = "files_index.json"
    trace_folder = ".traces"

    def __init__(self, keep, exclude, trace_folder_parent="./"):

        self.trace_folder = os.path.join(trace_folder_parent, self.trace_folder)

        self.keep_dirs = [f for f in keep if os.path.isdir(f)]
        self.keep_files = [f for f in keep if os.path.isfile(f)]

        self.exclude_dirs = [f for f in exclude if os.path.isdir(f)]
        self.exclude_files = [f for f in exclude if os.path.isfile(f)]

        self.interactive = False

        self.scope_stack = list()
        self.scope_counter = 0
        self.scope_stack.append(self.scope_counter)

        self.file_index = {}
        self.last_index = defaultdict(int)

        self.current_log_files = {}
        self.current_scope_files = {}

        self.prev_trace_func = None
        self.current_trace_name = ""

        shutil.rmtree(self.trace_folder, ignore_errors=True)

        os.makedirs(self.trace_folder, exist_ok=False)

        idx_file = self._index_file_path()

        self.index_file = open(idx_file, "w")

        self.fileNameHelper = matcher_ext.FileMatcher(self.keep_files, self.keep_dirs,
                                                      self.exclude_files, self.exclude_dirs)

        logger.info("Created Tracer object with logging to {trace_folder_parent}, {keep}, {exclude}",
                    trace_folder_parent=trace_folder_parent, keep=keep, exclude=exclude)
        # remove this

        self.after_write = 0
        self.before_write_log = 0
        self.before_call_check = 0
        self.before_locals = 0
        self.check_time = 0
        self.before_if = 0

    def times(self):
        return {
            "each_trace": self.before_if,
            "if_time": self.check_time,
            "get_locals": self.before_locals,
            "check_if_comprehension": self.before_call_check,
            "scope_logic": self.before_write_log,
            "write_trace": self.after_write,

        }

    def _index_file_path(self):
        return os.path.join(self.trace_folder, self.files_index_file)

    def _trace_file_path(self, trace_name, file_under_trace):
        this_trace_folder = os.path.join(self.trace_folder, trace_name)
        os.makedirs(this_trace_folder, exist_ok=True)
        file_name = str(file_under_trace) + "." + self.trace_file_ext
        return os.path.join(this_trace_folder, file_name)

    def _scope_file_path(self, trace_name, file_under_trace):
        this_trace_folder = os.path.join(self.trace_folder, trace_name)
        os.makedirs(this_trace_folder, exist_ok=True)
        file_name = str(file_under_trace) + "." + self.scopes_file_ext
        return os.path.join(this_trace_folder, file_name)

    def _log_scope_closed(self, file, scope):
        if file not in self.current_scope_files:
            self.current_scope_files[file] = open(self._scope_file_path(
                self.current_trace_name,
                file
            ), "w")
        idx = self.last_index[file]
        self.current_scope_files[file].write(str(scope) + ", " + str(idx) + "\n")

    def _log_line(self, file, line, self_ref, scope):
        self.last_index[file] += 1
        if file not in self.current_log_files:
            self.current_log_files[file] = open(self._trace_file_path(
                self.current_trace_name,
                file
            ), "w")
        self.current_log_files[file].write(", ".join(map(str, [file, line, self_ref, scope])) + "\n")

    def start(self, trace_name):
        logger.debug("Tracer started with trace name {trace_name}", trace_name=trace_name)
        self.prev_trace_func = sys.gettrace()
        self.current_trace_name = trace_name
        self.current_log_files = {}
        self.current_scope_files = {}
        self.last_index = defaultdict(int)
        sys.settrace(self._tracefunc)

    def stop(self):
        sys.settrace(None)
        logger.debug("Tracer stopped with trace name {trace_name}", trace_name=self.current_trace_name)
        [f.close() for f in self.current_log_files.values()]
        [f.close() for f in self.current_scope_files.values()]
        # self.current_log_files = {}
        # self.current_scope_files = {}
        self.current_trace_name = ""
        sys.settrace(self.prev_trace_func)
        self.prev_trace_func = None

    def fullstop(self):
        json.dump(
            {v: k for k, v in self.file_index.items()},
            self.index_file,
            indent=2
        )
        self.index_file.close()

        logger.debug("Tracer closed, file index saved to {p}", p=self._index_file_path())

    def _tracefunc(self, frame, event, _):
        # st = time()
        file_path = frame.f_code.co_filename

        should_trace_deeper = False

        interructive = False

        # self.before_if += (time() - st)
        st = time()
        if self.fileNameHelper.should_include(file_path):
            self.check_time += (time() - st)
            # st = time()

            line = frame.f_lineno
            is_comprehension = False
            f_locals = frame.f_locals

            # self.before_locals += (time() - st)
            # st = time()

            if len(f_locals) > 0 and ".0" in f_locals:
                is_comprehension = True

            # self.before_call_check += (time() - st)
            # st = time()
            if event == "call":
                self.scope_counter += 1
                self.scope_stack.append(self.scope_counter)
            elif event == "return":
                file_idx = self.file_index[file_path]
                self._log_scope_closed(file=file_idx, scope=self.scope_stack[-1])
                self.scope_stack.pop()

            scope = self.scope_stack[-1]

            # self.before_write_log += (time() - st)
            # st = time()

            should_trace_deeper = True
            # if interructive:
            #     args = inspect.getargvalues(frame)
            # # if self.interactive:
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

            if is_comprehension:
                pass
            elif event == "line" or event == "call":
                if file_path in self.file_index:
                    file_idx = self.file_index[file_path]
                else:
                    self.file_index[file_path] = len(self.file_index)
                    file_idx = len(self.file_index) - 1
                self._log_line(file_idx, line, frame_self, scope)
            # self.after_write += (time() - st)

        # if should_trace_deeper:
        return self._tracefunc
