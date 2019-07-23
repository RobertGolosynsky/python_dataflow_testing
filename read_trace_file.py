import os

import numpy as np
import pandas as pd

from model.cfg.project_cfg import ProjectCFG
from model.project import Project

# trace_batches = pd.read_csv(
#     "t_e_s_t___c_r_e_a_t_e___b_y_t_e___c_f_g.log",
#     # sep=" ",
#     header=None,
#     names=["file", "line", "self", "scope"],
#     dtype={"file": np.int, "line": np.int, "self": np.int, "scope": np.int},
#     chunksize=100000
# )
# with open("trace_file_cache.log") as f:
#     file_dict = {}
#     for line in f.readlines():
#         k, v = line[:-1].split(", ")
#         key = int(k)
#         file_dict[key] = v


THIS_DIR = os.path.dirname(os.path.abspath(__file__))


# relative_path = ""
# project_path = os.path.join(THIS_DIR, relative_path)
import multiprocessing as mp
# mp.set_start_method("spawn", force=True)
def target():
    import sys

    project = Project("../pdt_copy")
    project_cfg = ProjectCFG(project)
    print(project_cfg.module_cfgs)


if __name__ == '__main__':

    p = mp.Process(target=target, args=())
    p.start()
    p.join()

#
# for b in trace_batches:
#     a = b.loc[b["self"] == -1]
#     for row in a.itertuples():
#         print(file_dict[row.file])
#


