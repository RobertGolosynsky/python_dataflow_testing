import os
from pathlib import Path
from typing import List
import shutil
from git import Repo
from loguru import logger
from playhouse.sqlite_ext import SqliteExtDatabase

from experiment.pydefects.database.models import DATABASE_PROXY, Repository, TestResults, Commit, \
    CommitTag, CommitCommitTag, Diff


class RepositoryManager:
    def __init__(self, repo: Repository, commit: Commit, test_module_path: str = None):
        self.repo = repo
        self.commit = commit
        self.name = Path(self.url()).name
        self.test_module_path = test_module_path

    def url(self):
        return self.repo.homepage

    def path_to_repo(self, folder_path):
        return os.path.join(folder_path, f"{self.repo.name}_{self.commit.hash}")

    def clone_to(self, path, overwrite_if_exists=False):
        checkout_path = self.path_to_repo(path)
        if not overwrite_if_exists and Path(checkout_path).is_dir():
            logger.info("Repo was already cloned, using previous version")
            return checkout_path
        shutil.rmtree(checkout_path, ignore_errors=True)
        logger.info("Cloning from {url}:{commit}", url=self.repo.homepage, commit=self.commit.hash)
        git_repo = Repo.clone_from(self.repo.homepage, checkout_path)
        git_repo.git.checkout(self.commit.hash)
        return checkout_path

    def clone_parent_to(self, path, overwrite_if_exists=False):
        parent_path = os.path.join(
            path,
            f"{self.repo.name}_{self.commit.hash}_parent"
        )
        if not overwrite_if_exists and Path(parent_path).is_dir():
            logger.info("Repo was already cloned, using previous version")
            return parent_path
        shutil.rmtree(parent_path, ignore_errors=True)
        logger.info("Cloning from {url}:{commit}", url=self.repo.homepage, commit=self.commit.hash)
        git_repo = Repo.clone_from(self.repo.homepage, parent_path)
        parent = git_repo.commit(self.commit.hash)
        git_repo.git.checkout(parent.parents[0])
        return parent_path

    def __repr__(self):
        return f"""
        Repo:       {self.name} @ {self.commit.hash}
        Failed:     {self.repo.testresults.failed}
        Passed:     {self.repo.testresults.passed}
        Skipped:    {self.repo.testresults.skipped}
        Warnings:   {self.repo.testresults.warnings}
        Errors:     {self.repo.testresults.error}
        Time:       {self.repo.testresults.time}s
        Statements: {self.repo.testresults.statements}
        Missing:    {self.repo.testresults.missing}
        Coverage:   {self.repo.testresults.coverage}%
        Test module path:   {self.test_module_path}
"""


def get_projects(
        db_path,
        limit=None,
        time_less_then=None,
        passed_greater_than=None,
        no_errors=True,
        coverage_greater_then=None,
        unique_repos=False
) -> List[RepositoryManager]:
    db = SqliteExtDatabase(
        db_path,
        pragmas={
            "journal_mode": "wal",
            "cache_size": -64 * 1000,
            "foreign_key": 1,
            "ignore_check_constraints": 9,
            "synchronous": 0,
        },
    )
    DATABASE_PROXY.initialize(db)

    commits = \
        Commit.select(
            Commit.hash,
            Commit.repository,
            CommitTag.tag,
        ).join(
            CommitCommitTag
        ).join(
            CommitTag
        ).where(
            CommitTag.tag.startswith("regression")
        )
    if limit:
        commits = commits.limit(limit)

    repos = []
    for commit in commits:
        repo = (
            Repository.select(
                Repository.id,
                Repository.name,
                Repository.homepage,
                TestResults.failed,
                TestResults.passed,
                TestResults.skipped,
                TestResults.warnings,
                TestResults.error,
                TestResults.time,
                TestResults.statements,
                TestResults.missing,
                TestResults.coverage,
            ).join(
                TestResults
            ).where(
                Repository.id == commit.repository
            ).get()
        )
        # print(repo, dir(commit))
        repos.append(RepositoryManager(repo, commit))
    filtered = []
    used_repos = set()
    for repo_version in repos:
        tr: TestResults = repo_version.repo.testresults
        if time_less_then and tr.time > time_less_then:
            continue
        if no_errors and tr.error > 0:
            continue
        if coverage_greater_then and tr.coverage < coverage_greater_then:
            continue
        if passed_greater_than and tr.passed < passed_greater_than:
            continue
        if unique_repos and repo_version.repo.id in used_repos:
            continue
        used_repos.add(repo_version.repo.id)
        filtered.append(repo_version)

    return filtered


def get_projects_bugs(
        db_path,
        limit=None,
        time_less_then=None,
        passed_greater_than=None,
        no_errors=True,
        coverage_greater_then=None,
        unique_repos=False
):
    db = SqliteExtDatabase(
        db_path,
        pragmas={
            "journal_mode": "wal",
            "cache_size": -64 * 1000,
            "foreign_key": 1,
            "ignore_check_constraints": 9,
            "synchronous": 0,
        },
    )
    DATABASE_PROXY.initialize(db)

    commits = (
        Commit.select(
            Commit.id,
            Commit.hash,
            Commit.repository,
            CommitTag.tag,
        ).join(
            CommitCommitTag
        ).join(
            CommitTag
        ).where(
            CommitTag.tag.startswith("regression")
        ).limit(limit)
    )
    repos = []
    for commit in commits:
        diffs = (
            Diff.select()
                .where(
                (Diff.commit == commit.id)
                & ((Diff.old_path.endswith("py")) | (Diff.new_path.endswith("py")))
                & ~(Diff.old_path.contains("test"))
                & ~(Diff.new_path.contains("test"))
            )
                .count()
        )

        if diffs != 1:
            continue

        repo = (
            Repository.select(
                Repository.id,
                Repository.name,
                Repository.homepage,
                TestResults.failed,
                TestResults.passed,
                TestResults.skipped,
                TestResults.warnings,
                TestResults.error,
                TestResults.time,
                TestResults.statements,
                TestResults.missing,
                TestResults.coverage,
            ).join(
                TestResults
            ).where(
                Repository.id == commit.repository
            ).get()
        )

        module_name = (
            Diff.select(Diff.new_path)
                .where(
                (Diff.commit == commit.id)
                & ((Diff.old_path.endswith("py")) | (Diff.new_path.endswith("py")))
                & ~(Diff.old_path.contains("test"))
                & ~(Diff.new_path.contains("test"))
            ).get()
        )
        repos.append(RepositoryManager(repo, commit, test_module_path=module_name.new_path))

    filtered = []
    used_repos = set()
    for repo_version in repos:
        tr: TestResults = repo_version.repo.testresults
        if time_less_then and tr.time > time_less_then:
            continue
        if no_errors and tr.error > 0:
            continue
        if coverage_greater_then and tr.coverage < coverage_greater_then:
            continue
        if passed_greater_than and tr.passed < passed_greater_than:
            continue
        if unique_repos and repo_version.repo.id in used_repos:
            continue
        used_repos.add(repo_version.repo.id)
        filtered.append(repo_version)

    return filtered
