import itertools
import operator
import os
from typing import List
import random
import numpy as np
from loguru import logger
from playhouse.sqlite_ext import SqliteExtDatabase

from experiment.visualization.cum_chart import draw_biased, draw_grouped, draw_grouped_normalized
from experiment.visualization.dataset_visualization import visualize_dataset
from experiment.db_model.repo import *
from experiment.folders import results_root
from experiment.pydefects.get_projects import RepositoryManager
from model.project import Project, Merger
import combined_experiment_cli
from multiprocessing import Pool

combined_experiment_cli_path = combined_experiment_cli.__file__


def run_for_one_project(params):
    module, dataset_path, graphs_path, extra_requirements = params
    manager = RepositoryManager(module.repo.url, module.repo.fixed_commit, module.path)

    fixed_root = manager.clone_to(dataset_path, overwrite_if_exists=False)
    buggy_root, buggy_hash = manager.clone_parent_to(dataset_path, overwrite_if_exists=True)

    fixed_project = Project(fixed_root)
    buggy_project = Project(buggy_root)
    logger.info(f"Fixed commit path {fixed_project.path}")
    logger.info(f"Buggy commit path {buggy_project.path}")

    fixed_project.create_venv(force_remove_previous=True)
    buggy_project.create_venv(force_remove_previous=True)
    logger.info("Venv created")

    logger.info("Moving tests...")
    merger = Merger(fixed_project, buggy_project)
    merger.move_test_from_fixed_to_buggy()

    module_under_test = module.path
    revealing_node_ids = []

    for tc in module.test_cases.where(TestCase.result == "revealed"):
        revealing_node_ids.append(tc.node_id)
    print("*" * 100)
    revealing_node_ids = " ".join(revealing_node_ids)

    test_suite_sizes = np.arange(start=1, stop=int(module.total_cases), step=2) + 1
    test_suite_sizes = " ".join(map(str, test_suite_sizes))

    code = buggy_project.run_command(
        f"python3 {combined_experiment_cli_path} --module={module_under_test} --revealing_node_ids {revealing_node_ids} --out={graphs_path} --test_suite_sizes {test_suite_sizes} --test_suite_coverages_count=20 --max_trace_size=10 ",
        extra_requirements=extra_requirements
    )


if __name__ == "__main__":
    lim = 998
    off = 0
    flag = "grouped_all_c_all_p"
    graphs_path = results_root / "graphs_cumulative_off_{}_lim_{}{}".format(off, lim, flag)
    general_graphs = graphs_path / "graphs"
    os.makedirs(graphs_path, exist_ok=True)
    os.makedirs(general_graphs, exist_ok=True)

    database = "selection.db"
    max_trace_size = 100  # MB
    dataset_path = results_root / "dataset_cumulative_off_{}_lim_{}{}".format(off, lim, flag)
    extra_requirements = [r.strip() for r in open("../requirements.txt").readlines()]

    db = SqliteExtDatabase(
        database,
        pragmas={
            "journal_mode": "wal",
            "cache_size": -64 * 1000,
            "foreign_key": 1,
            "ignore_check_constraints": 9,
            "synchronous": 0,
        }
    )
    DATABASE_PROXY.initialize(db)

    ms: List[Module] = Module.select() \
        .join(Repo) \
        .order_by(Module.total_cases.desc()) \
        .where(Module.bugs < 8) \
        .where(Module.total_cases < 100) \
        .group_by(Repo.name) \
        .offset(off) \
        .limit(lim)
    ms = list(ms)
    random.shuffle(ms)
    visualize_dataset(ms, general_graphs)

    # min_test_cases = min(ms, key=operator.attrgetter("total_cases")).total_cases
    # test_suite_sizes = np.arange(start=1, stop=int(min_test_cases), step=2) + 1
    # test_suite_sizes = " ".join(map(str, test_suite_sizes))
    pool = Pool(processes=4)
    pool.map(
        run_for_one_project,
        zip(
            ms,
            itertools.cycle([dataset_path]),
            itertools.cycle([graphs_path]),
            itertools.cycle([extra_requirements])
        )
    )

    draw_biased(graphs_path, general_graphs)
    draw_grouped(graphs_path, general_graphs)
    draw_grouped_normalized(graphs_path, general_graphs)
