import os

import pandas as pd
from loguru import logger
from pandas.errors import EmptyDataError

from experiment.pydefects.get_projects import RepositoryManager


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
        self.bad_file.write(f"{repo.repo_name},{repo.commit_hash}\n")
        self.bad_file.flush()

    def mark_repo_as_good(self, repo: RepositoryManager):
        self.good_file.write(f"{repo.repo_name},{repo.commit_hash}\n")
        self.good_file.flush()

    def mark_repo_as_suspicious(self, repo: RepositoryManager):
        self.suspicious_file.write(f"{repo.repo_name},{repo.commit_hash}\n")
        self.suspicious_file.flush()

    def is_repo_bad(self, repo_manager: RepositoryManager):
        for name, commit in self.bad_repos:
            if name == repo_manager.repo_name and commit == repo_manager.commit_hash:
                return True
        return False

    def is_repo_good(self, repo_manager: RepositoryManager):
        for name, commit in self.good_repos:
            if name == repo_manager.repo_name and commit == repo_manager.commit_hash:
                return True
        return False

    def is_repo_suspicious(self, repo_manager: RepositoryManager):
        for name, commit in self.suspicious_repos:
            if name == repo_manager.repo_name and commit == repo_manager.commit_hash:
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

