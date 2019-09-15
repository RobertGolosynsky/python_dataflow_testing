import argparse
import csv
import os
import sys

from git import Repo
from playhouse.sqlite_ext import SqliteExtDatabase

from experiment.pydefects.database.models import DATABASE_PROXY, Repository, TestResults, Commit, \
    CommitTag, CommitCommitTag


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("-db", required=True, dest="db_path", help="Path to database")
    parser.add_argument(
        "-out",
        required=False,
        dest="out_path",
        help="Path where repositories will be placed, will be created if necessary",
    )
    config = parser.parse_args(args)

    db = SqliteExtDatabase(
        config.db_path,
        pragmas={
            "journal_mode": "wal",
            "cache_size": -64 * 1000,
            "foreign_key": 1,
            "ignore_check_constraints": 9,
            "synchronous": 0,
        },
    )
    DATABASE_PROXY.initialize(db)

    if config.out_path:
        os.makedirs(config.out_path, exist_ok=True)

    commits = (
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
        ).limit(5)
    )

    rows = []
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
        if config.out_path:
            print(f"Do checkout for commit {commit.hash} in {repo.name}")
            print(f"Test results:")
            print(f"    Failed:     {repo.testresults.failed}")
            print(f"    Passed:     {repo.testresults.passed}")
            print(f"    Skipped:    {repo.testresults.skipped}")
            print(f"    Warnings:   {repo.testresults.warnings}")
            print(f"    Errors:     {repo.testresults.error}")
            print(f"    Time:       {repo.testresults.time}s")
            print(f"    Statements: {repo.testresults.statements}")
            print(f"    Missing:    {repo.testresults.missing}")
            print(f"    Coverage:   {repo.testresults.coverage}%")

            checkout_path = os.path.join(config.out_path, f"{repo.name}_{commit.hash}")
            git_repo = Repo.clone_from(repo.homepage, checkout_path)
            git_repo.git.checkout(commit.hash)

            parent_path = os.path.join(
                config.out_path,
                f"{repo.name}_{commit.hash}_parent"
            )
            git_repo = Repo.clone_from(repo.homepage, parent_path)
            parent = git_repo.commit(commit.hash)
            git_repo.git.checkout(parent.parents[0])

            print()
            print()
        else:
            row = {
                "repo_id": repo.id,
                "repo_name": repo.name,
                "repo_homepage": repo.homepage,
                "commit_hash": commit.hash,
                "failed": repo.testresults.failed,
                "passed": repo.testresults.passed,
                "skipped": repo.testresults.skipped,
                "warnings": repo.testresults.warnings,
                "errors": repo.testresults.error,
                "time": repo.testresults.time,
                "statements": repo.testresults.statements,
                "missing": repo.testresults.missing,
                "coverage": repo.testresults.coverage,
            }
            rows.append(row)

    if not config.out_path:
        fields = [
            "repo_id",
            "repo_name",
            "repo_homepage",
            "commit_hash",
            "failed",
            "passed",
            "skipped",
            "warnings",
            "errors",
            "time",
            "statements",
            "missing",
            "coverage",
        ]
        with open("/tmp/commits.csv", mode="w") as csv_file:
            writer = csv.DictWriter(csv_file, fields)
            writer.writeheader()
            writer.writerows(rows)


if __name__ == '__main__':
    main(sys.argv[1:])
