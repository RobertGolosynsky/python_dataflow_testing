import os
import unittest

from coverage_metrics.branch_coverage import find_covered_branches, find_branches
from test.test_tracer import CLEAN_LINKED_LIST_LL, CLEAN_LINKED_LIST_ROOT, create_new_temp_dir
from model.cfg.project_cfg import ProjectCFG

from tracing.trace_reader import read_df, TraceReader

import thorough
from tracing.tracer import LINE_INDEX
import dataflow.def_use as du
from model.cfg.module_cfg import ModuleCFG


class TestFindBranches(unittest.TestCase):

    def test_asd(self):
        from loguru import logger
        logger.remove()
        # p = "/home/robert/Documents/master/code/1experiments_results/dataset_cumulative"
        p = "/home/robert/Documents/master/code/python_dataflow_testing/dataset/linked_list_clean"
        for dirpath, subdirs, files in os.walk(p):
            if "venv" in dirpath:
                continue
            for x in files:
                if x.endswith(".py"):
                    f_path = os.path.join(dirpath, x)
                    print(f_path)
                    cfg = ModuleCFG(f_path)
                    branching_edges = cfg.branching_edges
                    for line, ends in branching_edges.items():
                        print(line, ends)
                        assert len(ends) <= 2

    def test_while_with_if_inside(self):
        source = """   
def a(x): #2
    while x>1:#3
        if x>2:#4
            return x#5
        x+=1#6
    return None#7
        """
        s = branches_of(source)
        expected = {(4, 5), (3, 7), (3, 4), (4, 6)}
        self.assertEqual(expected, s)

    def test_find_branches(self):
        source = """   
def a(self, i):#2
    node = self.root#3
    for j in range(i):#4
        node = node.next#5
        if not node:#6
            return None#7
    return node#8
    """
        func = compile_source(source, "a")
        print(func)
        cfg = du.try_create_cfg_with_definitions_and_uses(
            func,
            definition_line=1,
            args=["x"]
        ).g
        di, s = find_branches(cfg)
        print(di)
        print(s)
        import graphs.draw as gd
        gd.draw_byte_cfg_dot(cfg, [], None)

    def test_find_branches_if_no_else_no_return(self):
        source = """
def a(x):
    if x>3:
        print(x)
            """
        s = branches_of(source)
        exit = "some exit node"
        # self.assertEqual({(3, 4), (3, exit)}, s)


class TestBranchCoverage(unittest.TestCase):

    def test_branch_coverage(self):
        project_root = CLEAN_LINKED_LIST_ROOT
        trace_root = create_new_temp_dir()

        exclude_folders = ["venv", "dataset"]
        cfg = ProjectCFG.create_from_path(project_root,
                                          exclude_folders=exclude_folders,
                                          use_cached_if_possible=False)

        thorough.run_tests(CLEAN_LINKED_LIST_ROOT, trace_root, exclude_folders)

        trace_reader = TraceReader(trace_root)

        ll_py = str(CLEAN_LINKED_LIST_LL)
        ll_py_cfg = cfg.module_cfgs[ll_py]

        total_exercised = []
        available_branches = set(ll_py_cfg.branches)
        node_ids = trace_reader.folders_mapping.keys()
        for node_id in node_ids:
            lines = get_covered_lines(trace_reader, node_id, ll_py)
            covered = find_covered_branches(lines, ll_py_cfg.branching_edges)
            total_exercised.extend(b for b in covered if b in available_branches)

        print("Coverage")
        print_percent("Branches covered", total_exercised, ll_py_cfg.branches)
        print(available_branches)
        print(total_exercised)
        not_exercised_branches = set(available_branches) - set(total_exercised)
        print("Not exercised branches total ({}): ".format(len(not_exercised_branches)), not_exercised_branches)
        self.assertEqual(16, len(not_exercised_branches))


def get_covered_lines(trace_reader, node_id, module_path):
    _, trace_file_paths = trace_reader.get_traces_for(module_path, selected_node_ids=[node_id])
    if trace_file_paths:
        trace_file_path = trace_file_paths[0]
        np_array, _ = read_df(trace_file_path)
        return np_array.T[LINE_INDEX]
    else:
        return []


def print_percent(text, given, total):
    a = len(set(given))
    b = len(set(total))
    if b == 0:
        percent = 100
    else:
        percent = a * 100 / b
    print("{}: found {} / total {} | {}%".format(text, a, b, int(percent)))


def compile_source(source, func_name):
    # fake_module_code = compile(fake_module, "", mode="exec")
    namespace = {}
    exec(source, namespace)
    return namespace[func_name]


def branches_of(source, func_name="a"):
    func = compile_source(source, func_name)
    cfg = du.try_create_cfg_with_definitions_and_uses(
        func,
        definition_line=1,
        args=[]
    ).g
    di, s = find_branches(cfg)
    return s
