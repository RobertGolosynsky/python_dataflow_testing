import operator
import os
from pathlib import Path
from typing import List

import numpy as np
from loguru import logger
from playhouse.sqlite_ext import SqliteExtDatabase
from experiment.db_model.repo import *
from experiment.folders import results_root
from experiment.pydefects.get_projects import RepositoryManager
from model.project import Project, Merger
import combined_experiment_cli

combined_experiment_cli_path = combined_experiment_cli.__file__

if __name__ == "__main__":
    database = "selection.db"
    max_trace_size = 10  # MB
    dataset_path = results_root / "dataset_cumulative"
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
    lim = 20
    off = 60
    graphs_path = results_root / "graphs_cumulative_off_{}_lim_{}".format(off, lim)
    ms: List[Module] = Module.select() \
        .join(Repo) \
        .group_by(Repo.name) \
        .order_by(Module.total_cases.desc()) \
        .where(Repo.status == "good") \
        .offset(off) \
        .limit(lim)

    min_test_cases = min(ms, key=operator.attrgetter("total_cases")).total_cases
    test_suite_sizes = np.arange(start=1, stop=int(min_test_cases * 0.8), step=2) + 1
    test_suite_sizes = " ".join(map(str, test_suite_sizes))
    for m in ms:
        manager = RepositoryManager(m.repo.url, m.repo.fixed_commit, m.path)
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

        module_under_test = m.path
        revealing_node_ids = []

        for tc in m.test_cases.where(TestCase.result == "revealed"):
            revealing_node_ids.append(tc.node_id)
        print("*" * 100)
        revealing_node_ids = " ".join(revealing_node_ids)

        buggy_project.run_command(
            f"python3 {combined_experiment_cli_path} --module={module_under_test} --revealing_node_ids {revealing_node_ids} --out={graphs_path} --test_suite_sizes {test_suite_sizes} --test_suite_coverages_count=20 --max_trace_size=10 ",
            extra_requirements=extra_requirements
        )
