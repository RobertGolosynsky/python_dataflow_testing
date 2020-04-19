import inspect
from collections import defaultdict

from loguru import logger
import sys
import os
import json
from time import time
from cpp.cpp_import import load_cpp_extension

import shutil

from tracing.string_to_int_index import StringToIntIndex

matcher_ext = load_cpp_extension("matcher_ext")

IDX_INDEX = 0
FILE_INDEX = 1
LINE_INDEX = 2
SELF_INDEX = 3
SCOPE_INDEX = 4


class Tracer(object):
    trace_file_ext = "trace"
    scopes_file_ext = "scopes"
    trace_index_file_name = "files_index.json"
    folder_index_file_name = "folder_index.json"
    failed_test_cases_file = "failed_cases.json"
    trace_folder = ".traces"

    def __init__(self, keep, exclude, trace_folder_parent="./"):
        self.stopped = True

        self.trace_folder = os.path.join(trace_folder_parent, self.trace_folder)

        self.keep_dirs = [f for f in keep if os.path.isdir(f)]
        self.keep_files = [f for f in keep if os.path.isfile(f)]

        self.exclude_dirs = [f for f in exclude if os.path.isdir(f)]
        self.exclude_files = [f for f in exclude if os.path.isfile(f)]

        self.interactive = False

        self.scope_stack = list()
        self.scope_counter = 0
        self.scope_stack.append(self.scope_counter)

        self.failed_test_cases = []
        self.last_index = defaultdict(int)

        self.current_log_files = {}
        self.current_scope_files = {}

        self.prev_trace_func = None
        self.current_trace_name = ""

        shutil.rmtree(self.trace_folder, ignore_errors=True)

        os.makedirs(self.trace_folder, exist_ok=False)

        self.file_index = StringToIntIndex()

        self.folder_index = StringToIntIndex()

        failed_test_cases_file_path = self._failed_test_cases_file_path()

        self.fileNameHelper = matcher_ext.FileMatcher(self.keep_files, self.keep_dirs,
                                                      self.exclude_files, self.exclude_dirs)

        logger.info("Created Tracer object with logging to {trace_folder_parent}, {keep}, {exclude}",
                    trace_folder_parent=trace_folder_parent, keep=keep, exclude=exclude)

    def _trace_index_path(self):
        return os.path.join(self.trace_folder, self.trace_index_file_name)

    def _folder_index_path(self):
        return os.path.join(self.trace_folder, self.folder_index_file_name)

    def _failed_test_cases_file_path(self):
        return os.path.join(self.trace_folder, self.failed_test_cases_file)

    def _trace_file_path(self, trace_name, file_under_trace):
        trace_id = self.folder_index.get_or_create_int(trace_name)
        this_trace_folder = os.path.join(self.trace_folder, str(trace_id))
        os.makedirs(this_trace_folder, exist_ok=True)
        file_name = str(file_under_trace) + os.path.extsep + self.trace_file_ext
        return os.path.join(this_trace_folder, file_name)

    def _scope_file_path(self, trace_name, file_under_trace):
        trace_id = self.folder_index.get_int(trace_name)
        this_trace_folder = os.path.join(self.trace_folder, str(trace_id))
        os.makedirs(this_trace_folder, exist_ok=True)
        file_name = str(file_under_trace) + os.path.extsep + self.scopes_file_ext
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
        self.stopped = False

    def stop(self):
        self.stopped = True
        sys.settrace(None)
        logger.debug("Tracer stopped with trace name {trace_name}", trace_name=self.current_trace_name)
        [f.close() for f in self.current_log_files.values()]
        [f.close() for f in self.current_scope_files.values()]
        self.current_trace_name = ""
        sys.settrace(self.prev_trace_func)
        self.prev_trace_func = None

    def mark_test_case_failed(self, test_case):
        self.failed_test_cases.append(test_case)

    def full_stop(self):
        self.file_index.save(self._trace_index_path())
        self.folder_index.save(self._folder_index_path())

        with open(self._failed_test_cases_file_path(), "w", encoding="utf-8") as f:
            json.dump(
                [case for case in self.failed_test_cases],
                f,
                indent=2
            )

        logger.debug("Tracer closed, file index saved to {p}", p=self._trace_index_path())

    def _tracefunc(self, frame, event, _):
        if self.stopped:
            return
        file_path = frame.f_code.co_filename
        if self.fileNameHelper.should_include(file_path):
            line = frame.f_lineno
            is_comprehension = False
            f_locals = frame.f_locals

            if len(f_locals) > 0 and ".0" in f_locals:
                is_comprehension = True
            is_call = False
            is_return = False
            if event == "call":
                is_call = True

                self.scope_counter += 1
                self.scope_stack.append(self.scope_counter)
            elif event == "return":
                is_return = True
                file_idx = self.file_index.get_or_create_int(file_path)
                self._log_scope_closed(file=file_idx, scope=self.scope_stack[-1])
                self.scope_stack.pop()

            scope = self.scope_stack[-1]
            frame_self = frame.f_locals.get("self", None)
            frame_self = id(frame_self) if frame_self is not None else -1

            if is_comprehension:
                pass
            elif is_call or event == "line":
                file_idx = self.file_index.get_or_create_int(file_path)
                # if file_path in self.file_index:
                #     file_idx = self.file_index[file_path]
                # else:
                #     self.file_index[file_path] = len(self.file_index)
                #     file_idx = len(self.file_index) - 1
                self._log_line(file_idx, line, frame_self, scope)

        return self._tracefunc
