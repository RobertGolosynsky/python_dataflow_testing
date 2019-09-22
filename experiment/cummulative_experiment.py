import operator
import os
from pathlib import Path
from typing import List

import numpy as np
from loguru import logger
from playhouse.sqlite_ext import SqliteExtDatabase
from experiment.db_model.repo import *
from experiment.pydefects.get_projects import RepositoryManager
from model.project import Project, Merger
import combined_experiment_cli

combined_experiment_cli_path = combined_experiment_cli.__file__

database = "selection.db"
plots = "plots"

max_trace_size = 10  # MB
results_root = Path(__file__).parent.parent.parent / "1experiments_results"
dataset_path = results_root / "dataset_cumulative"
graphs_path = results_root / "graphs_cumulative"
extra_requirements = [r.strip() for r in open("../requirements.txt").readlines()]

if __name__ == "__main__":
    if not os.path.isdir(plots):
        os.makedirs(plots, exist_ok=True)
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
        .group_by(Repo.name) \
        .order_by(Module.total_cases.desc()) \
        .where(Repo.status == "good") \
        .limit(20)

    min_test_cases = min(ms, key=operator.attrgetter("total_cases")).total_cases
    test_suite_sizes = np.arange(min_test_cases) + 1

    for m in ms:
        manager = RepositoryManager(m.repo.url, m.repo.fixed_commit, m.path)
        fixed_root = manager.clone_to(dataset_path, overwrite_if_exists=False)
        buggy_root, buggy_hash = manager.clone_parent_to(dataset_path, overwrite_if_exists=True)

        fixed_project = Project(fixed_root)
        buggy_project = Project(buggy_root)
        logger.info(f"Fixed commit path {fixed_project.path}")
        logger.info(f"Buggy commit path {buggy_project.path}")

        fixed_project.create_venv(force_remove_previous=True)
        buggy_project.create_venv(force_remove_previous=False)
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

        test_suite_sizes = " ".join(map(str, test_suite_sizes))
        buggy_project.run_command(
            f"python3 {combined_experiment_cli_path} --module={module_under_test} --revealing_node_ids {revealing_node_ids} --out={graphs_path} --test_suite_sizes={test_suite_sizes} --test_suite_coverages_count=20 --max_trace_size=10 ",
            extra_requirements=extra_requirements
        )
