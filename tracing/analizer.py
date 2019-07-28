import glob
import os

import numpy as np

from model.cfg.project_cfg import ProjectCFG
from tracing.tracer import Tracer
import util.find as uf
import pandas as pd
import swifter

from functools import wraps
from time import time


def timing(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time()
        result = f(*args, **kwargs)
        end = time()
        print('Elapsed time {}: {}'.format(f.__name__, end - start))
        return result

    return wrapper


class Trace:

    def __init__(self, path):
        self.path = path
        self.chunksize = 10 ** 4
        self.df = self._read_trace_file()

    @timing
    def _read_trace_file(self):
        trace_batches = pd.read_csv(
            self.path,
            header=None,
            names=["file", "line", "self", "scope"],
            dtype={"file": np.int, "line": np.int, "self": np.int, "scope": np.int},
            # chunksize=self.chunksize
        )
        return trace_batches


class DataflowAnalyzer:

    def __init__(self, folder, project_cfg: ProjectCFG):
        self.folder = folder
        self.project_cfg = project_cfg
        self.files_dict = self._read_file_dict()
        pass

    def _read_file_dict(self):
        files = [f for f in glob.glob(os.path.join(self.folder, "*." + Tracer.dict_file_ext),
                                      recursive=True)]
        if files:
            with open(files[0]) as f:
                file_dict = {}
                for line in f.readlines():
                    k, v = line[:-1].split(", ")
                    key = int(k)
                    file_dict[key] = v
                return file_dict
        else:
            return None

    @timing
    def _analyze(self):
        d = {}
        trace_files = uf.find_files(self.folder, Tracer.trace_file_ext, [], [])
        for i, f in enumerate(trace_files):
            print("Progress:", i * 100 // len(trace_files))
            t = Trace(f)
            f_name = os.path.basename(f)
            self._add_extra_columns(t)
            self._add_def_use(t)
            pairs = self._add_reaching_definitions(t)
            import pickle
            with open(f+"_pairs", "wb") as f:
                pickle.dump(pairs, f)
        return d

    @timing
    def _add_extra_columns(self, trace):
        trace.df['definitions'] = [[] for _ in range(len(trace.df))]
        trace.df['uses'] = [[] for _ in range(len(trace.df))]
        trace.df['reach_out'] = [[] for _ in range(len(trace.df))]

    @timing
    def _add_def_use(self, trace: Trace):

        def transform(row, return_defs):
            file_path = self.files_dict[row["file"]]
            vars = self.project_cfg.get_variables(file_path, row["line"])
            if vars:
                defs, uses = vars
                # print("defs:", defs, "uses:", uses)
                if return_defs:
                    return defs
                else:
                    return uses
            return []

        trace.df["definitions"] = trace.df.apply(transform, return_defs=True, axis=1)
        trace.df["uses"] = trace.df.apply(transform, return_defs=False, axis=1)


    @timing
    def _add_reaching_definitions(self, trace):
        pairs_time = 0
        reaching_time = 0
        pairs_result = []
        for file_idx, grouped_by_file in trace.df.groupby("file"):
            file_path = self.files_dict[file_idx]
            for scope, grouped_by_scope in grouped_by_file.groupby("scope"):
                scoped = grouped_by_scope
                st = time()
                reach_in = self._reaching_definitions(scoped)
                reaching_time += time() - st
                st = time()
                pairs = self._find_pairs(scoped, reach_in)
                pairs_result.extend(pairs)
                pairs_time += time() - st
        print("Adding reaching definitions:", reaching_time)
        print("Matching def-use pairs:", pairs_time)
        return pairs_result

    def _reaching_definitions(self, df: pd.DataFrame):

        class Apply:
            def __init__(self, reach_in=[]):
                self.reach_in = []

            def reach_out(self, tuple):
                reach_in_copy = self.reach_in.copy()
                this_idx = tuple.Index
                definitions = tuple.definitions
                this_line = tuple.line
                reach_out = []
                for idx, line, var_name in self.reach_in:
                    if var_name not in definitions:
                        reach_out.append((idx, line, var_name))
                for this_def in definitions:
                    reach_out.append((this_idx, this_line, this_def))

                self.reach_in = reach_out
                return reach_in_copy

        apply = Apply()
        return [apply.reach_out(row) for row in df.itertuples(index=True)]

    def _find_pairs(self, df, reach_in):

        def extract_pairs(row, rin):
            this_line = row.line
            pairs = []
            for use_var in row.uses:
                for def_index, def_line, def_var in rin:
                    if use_var == def_var:
                        pairs.append((use_var, def_line, this_line, def_index))
                        break
            return pairs

        return [extract_pairs(row, rin) for row, rin in zip(df.itertuples(index=True), reach_in)]
