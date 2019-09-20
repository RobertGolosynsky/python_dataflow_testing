from peewee import Proxy, Model, CharField, ForeignKeyField, IntegerField, FloatField, BooleanField

DATABASE_PROXY = Proxy()


class Base(Model):
    class Meta:
        database = DATABASE_PROXY


class Repo(Base):
    id = CharField(primary_key=True)
    status = CharField()
    name = CharField()
    url = CharField()
    fixed_commit = CharField()
    buggy_commit = CharField()


class Module(Base):
    repo = ForeignKeyField(Repo, backref='modules')
    path = CharField()
    m_pairs = IntegerField()
    im_pairs = IntegerField()
    ic_pairs = IntegerField()
    statements = IntegerField()
    branches = IntegerField()
    mutants = IntegerField()
    bugs = IntegerField()
    total_cases = IntegerField()
    st_cov = IntegerField()
    br_cov = IntegerField()
    du_cov = IntegerField()
    time = IntegerField()
    is_full_cfg = BooleanField()


class TestCase(Base):
    module = ForeignKeyField(Module, backref='test_cases')
    node_id = CharField()
    result = CharField()


tables = [Repo, Module, TestCase]
