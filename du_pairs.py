import sys

from graphs.draw import source_w_pairs
from model.cfg.module_cfg import ModuleCFG

if __name__ == "__main__":
    path = sys.argv[1]
    p_type = sys.argv[2]
    cfg = ModuleCFG(path)
    pairs = []
    if p_type == "m":
        pairs = cfg.intramethod_pairs
    elif p_type == "im":
        pairs = cfg.intermethod_pairs
    elif p_type == "ic":
        pairs = cfg.interclass_pairs
    else:
        print("type must be one of {m, im, ic}")
        exit(1)
    source_w_pairs(path, pairs)
