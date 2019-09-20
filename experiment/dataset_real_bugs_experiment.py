import os
import traceback
import json
from pathlib import Path
from pprint import pformat

import pandas as pd
from loguru import logger
from pandas.errors import EmptyDataError

from experiment.pydefects.get_projects import get_projects, get_projects_bugs, RepositoryManager
from model.project import Project, Merger
import real_bugs_experiment_cli
from pytest_failed_node_ids import EXCEPTIONS_FILE

real_bugs_experiment_path = real_bugs_experiment_cli.__file__


def node_ids_where_assertion_error(js):
    ids = []
    for node_id in js:
        if "AssertionError" in js[node_id]:
            ids.append(node_id)
    return ids


class RepoStatistics:

    def __init__(self, path):
        self.path = path
        os.makedirs(path, exist_ok=True)

        good_path = os.path.join(path, "good_repos.csv")
        bad_path = os.path.join(path, "bad_repos.csv")
        suspicious_path = os.path.join(path, "suspicious_repos.csv")
        self.bad_repos = self._read_repos(bad_path)
        self.good_repos = self._read_repos(good_path)
        self.suspicious_repos = self._read_repos(suspicious_path)

        self.good_file = open(good_path, "a")
        self.bad_file = open(bad_path, "a")
        self.suspicious_file = open(suspicious_path, "a")

    def mark_repo_as_bad(self, repo: RepositoryManager):
        self.bad_file.write(f"{repo.name},{repo.commit.hash}\n")
        self.bad_file.flush()

    def mark_repo_as_good(self, repo: RepositoryManager):
        self.good_file.write(f"{repo.name},{repo.commit.hash}\n")
        self.good_file.flush()

    def mark_repo_as_suspicious(self, repo: RepositoryManager):
        self.suspicious_file.write(f"{repo.name},{repo.commit.hash}\n")
        self.suspicious_file.flush()

    def is_repo_bad(self, repo_manager: RepositoryManager):
        for name, commit in self.bad_repos:
            if name == repo_manager.name and commit == repo_manager.commit.hash:
                return True
        return False

    def is_repo_good(self, repo_manager: RepositoryManager):
        for name, commit in self.good_repos:
            if name == repo_manager.name and commit == repo_manager.commit.hash:
                return True
        return False

    def is_repo_suspicious(self, repo_manager: RepositoryManager):
        for name, commit in self.suspicious_repos:
            if name == repo_manager.name and commit == repo_manager.commit.hash:
                return True
        return False

    def _read_repos(self, path):
        try:
            repos_name_commit = pd.read_csv(
                path,
                header=None,
                delimiter=",",
                dtype=str
            ).values
        except EmptyDataError as e:
            logger.warning("File {f} is empty", f=path)
            return []
        except FileNotFoundError as e:
            logger.warning("File {f} does not exist", f=path)
            return []
        return repos_name_commit


if __name__ == "__main__":
    repo_managers = get_projects_bugs(
        "pydefects.db",
        limit=None,
        time_less_then=60,
        coverage_greater_then=60,
        passed_greater_than=15,
        unique_repos=False,
        no_errors=False
    )

    results_root = Path(__file__).parent.parent.parent / "1experiments_results"
    dataset_path = results_root / "dataset_bugs"
    graphs_path_parent = results_root / "graphs_bugs"
    extra_requirements = [r.strip() for r in open("../requirements.txt").readlines()]
    repo_stat = RepoStatistics("repo_stats_bugs")

    logger.warning("Loading bad repos: {rs}", rs=repo_stat.bad_repos)
    logger.warning("Loading good repos: {rs}", rs=repo_stat.good_repos)
    logger.warning("Total repos in database with this query: {c}", c=len(repo_managers))

    for manager in repo_managers:
        logger.info(manager)
        if repo_stat.is_repo_bad(manager):
            logger.warning("Repo {n} version {c} is excluded", n=manager.name, c=manager.commit.hash)
            continue
        if repo_stat.is_repo_good(manager):
            logger.warning("Repo {n} version {c} is good, but we exclude it to try others", n=manager.name,
                           c=manager.commit.hash)
            continue
        try:

            fixed_root = manager.clone_to(dataset_path, overwrite_if_exists=False)
            buggy_root = manager.clone_parent_to(dataset_path, overwrite_if_exists=True)
            fixed_project = Project(fixed_root)
            buggy_project = Project(buggy_root)
            logger.info(f"Fixed commit path {fixed_project.path}")
            logger.info(f"Buggy commit path {buggy_project.path}")

            fixed_project.create_venv(force_remove_previous=True)
            buggy_project.create_venv(force_remove_previous=True)
            logger.info("Venv created")

            fixed_failed_node_ids = fixed_project.run_tests_get_failed_node_ids()
            buggy_failed_node_ids_before_merge = buggy_project.run_tests_get_failed_node_ids()

            logger.info("Fixed commit failed node ids {node_ids}", node_ids=fixed_failed_node_ids)
            logger.info("Buggy commit failed node ids {node_ids}", node_ids=buggy_failed_node_ids_before_merge)

            logger.info("Moving tests...")
            merger = Merger(fixed_project, buggy_project)
            merger.move_test_from_fixed_to_buggy()

            buggy_failed_node_ids_after_merge = buggy_project.run_tests_get_failed_node_ids()

            logger.info("Before merge failed node ids: {data}",
                        data=pformat(buggy_failed_node_ids_before_merge))
            logger.info("After merge failed node ids: {data}", data=pformat(buggy_failed_node_ids_after_merge))

            before = set(buggy_failed_node_ids_before_merge)
            after = set(buggy_failed_node_ids_after_merge)
            new_failing_node_ids = after - before
            logger.info("New node ids that failed, these have revealed a bug: {data}",
                        data=pformat(new_failing_node_ids))
            if len(new_failing_node_ids) > 0:
                with open(os.path.join(buggy_project.path, EXCEPTIONS_FILE)) as f:
                    exceptions = json.load(f)
                for node_id in new_failing_node_ids:
                    exc = exceptions[node_id]
                    logger.warning("Node id {node_id} failed with exception text: {exc}", node_id=node_id,
                                   exc=exc)
                good_node_ids = node_ids_where_assertion_error(exceptions)
                if len(good_node_ids) > 0:
                    repo_stat.mark_repo_as_good(manager)

                    logger.warning("Found node ids which failed on assertion!")
                    node_ids = " ".join(good_node_ids)
                    graphs_path = graphs_path_parent  # / buggy_project.project_name
                    module_path = manager.test_module_path
                    logger.info("Running the experiment for module {p}", p=module_path)
                    buggy_project.run_command(
                        f"python3 {real_bugs_experiment_path} --node_ids {node_ids} --graphs_folder={graphs_path} --test_suite_sizes_count=20 --test_suite_coverages_count=20 --max_trace_size=10 --module={module_path}",
                        extra_requirements=extra_requirements
                    )
                else:
                    repo_stat.mark_repo_as_bad(manager)
            else:
                logger.warning("There are no new tests which failed in the merged version of code base")
                repo_stat.mark_repo_as_bad(manager)

        except Exception as e:
            print(traceback.format_exc())
