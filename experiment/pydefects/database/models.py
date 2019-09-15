# -*- coding: utf-8 -*-

# This file is part of PyDefects.
#
# PyDefects is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyDefects is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with PyDefects.  If not, see <https://www.gnu.org/licenses/>.
# pylint: disable=missing-docstring,too-few-public-methods
from peewee import (
    Model,
    TextField,
    ForeignKeyField,
    IntegerField,
    CompositeKey,
    DateTimeField,
    FloatField,
    Proxy,
)

DATABASE_PROXY = Proxy()


class BaseModel(Model):
    class Meta:
        database = DATABASE_PROXY


class Keyword(BaseModel):
    keyword = TextField()


class License(BaseModel):
    license = TextField()


class Platform(BaseModel):
    platform = TextField()


class TestFramework(BaseModel):
    framework = TextField()


class Classifier(BaseModel):
    classifier = TextField()


class Repository(BaseModel):
    author = TextField()
    name = TextField()
    description = TextField()
    homepage = TextField()
    download_url = TextField()
    summary = TextField()
    version = TextField()
    lines_of_code = IntegerField()
    number_commits = IntegerField()
    number_files = IntegerField()
    type_annotations = TextField()
    last_commit = DateTimeField()
    create_at = DateTimeField()
    forks_count = IntegerField()
    language = TextField()
    last_modified = DateTimeField()
    open_issues_count = IntegerField()
    stargazers_count = IntegerField()
    subscribers_count = IntegerField()
    updated_at = DateTimeField()
    watchers_count = IntegerField()
    mining_date = DateTimeField()


class RepositoryClassifier(BaseModel):
    repository = ForeignKeyField(Repository)
    classifier = ForeignKeyField(Classifier)

    class Meta:
        primary_key = CompositeKey("repository", "classifier")


class TestResults(BaseModel):
    failed = IntegerField()
    passed = IntegerField()
    skipped = IntegerField()
    warnings = IntegerField()
    error = IntegerField()
    time = FloatField()
    statements = IntegerField()
    missing = IntegerField()
    coverage = FloatField()
    runner = ForeignKeyField(TestFramework)
    repository = ForeignKeyField(Repository)


class Commit(BaseModel):
    hash = TextField()
    author = TextField()
    author_date = DateTimeField()
    committer = TextField()
    committer_date = DateTimeField()
    msg = TextField()
    repository = ForeignKeyField(Repository)


class IssueLabel(BaseModel):
    label = TextField()


class IssueState(BaseModel):
    state = TextField()


class Issue(BaseModel):
    issue_id = IntegerField()
    author = TextField()
    title = TextField()
    content = TextField()
    timestamp = DateTimeField()
    state = ForeignKeyField(IssueState)
    assignees = TextField()
    repository = ForeignKeyField(Repository)


class IssueIssueLabel(BaseModel):
    issue = ForeignKeyField(Issue)
    label = ForeignKeyField(IssueLabel)

    class Meta:
        primary_key = CompositeKey("issue", "label")


class IssueComment(BaseModel):
    author = TextField()
    content = TextField()
    timestamp = DateTimeField()
    issue = ForeignKeyField(Issue)


class Diff(BaseModel):
    type = TextField()
    old_path = TextField()
    new_path = TextField()
    diff = TextField()
    commit = ForeignKeyField(Commit)


class CommitIssue(BaseModel):
    commit = ForeignKeyField(Commit)
    issue = ForeignKeyField(Issue)

    class Meta:
        primary_key = CompositeKey("commit", "issue")


class CommitTag(BaseModel):
    tag = TextField(unique=True)


class CommitCommitTag(BaseModel):
    commit = ForeignKeyField(Commit)
    tag = ForeignKeyField(CommitTag)

    class Meta:
        primary_key = CompositeKey("commit", "tag")


class RepositoryKeyword(BaseModel):
    repository = ForeignKeyField(Repository)
    keyword = ForeignKeyField(Keyword)

    class Meta:
        primary_key = CompositeKey("repository", "keyword")


class RepositoryLicense(BaseModel):
    repository = ForeignKeyField(Repository)
    license = ForeignKeyField(License)

    class Meta:
        primary_key = CompositeKey("repository", "license")


class RepositoryPlatform(BaseModel):
    repository = ForeignKeyField(Repository)
    platform = ForeignKeyField(Platform)

    class Meta:
        primary_key = CompositeKey("repository", "platform")


class RepositoryTestFramework(BaseModel):
    repository = ForeignKeyField(Repository)
    test_framework = ForeignKeyField(TestFramework)

    class Meta:
        primary_key = CompositeKey("repository", "test_framework")


def create_tables(testing=False) -> None:
    """Create the tables in the database if they do not exist."""
    tables = [
        Keyword,
        License,
        Platform,
        TestFramework,
        Classifier,
        Repository,
        RepositoryClassifier,
        TestResults,
        Commit,
        IssueLabel,
        IssueState,
        Issue,
        IssueIssueLabel,
        IssueComment,
        Diff,
        CommitIssue,
        CommitTag,
        CommitCommitTag,
        RepositoryKeyword,
        RepositoryLicense,
        RepositoryPlatform,
        RepositoryTestFramework,
    ]
    if testing:
        DATABASE_PROXY.bind(tables, bind_refs=False, bind_backrefs=False)
    DATABASE_PROXY.connect()
    DATABASE_PROXY.create_tables(tables)
    DATABASE_PROXY.close()


