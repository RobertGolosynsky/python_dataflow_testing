import os
import json
import traceback
from pathlib import Path
from pprint import pformat
from time import time

from loguru import logger
from playhouse.sqlite_ext import SqliteExtDatabase

from coverage_metrics.branch_coverage import BranchCoverage
from coverage_metrics.coverage_metric_enum import CoverageMetric
from coverage_metrics.def_use_coverage import DefUsePairsCoverage
from coverage_metrics.statement_coverage import StatementCoverage
from experiment.dataset_experiments.dataset_real_bugs_experiment import node_ids_where_assertion_error
from experiment.dataset_experiments.repo_statistics import RepoStatistics

from experiment.db_model.repo import DATABASE_PROXY, Repo, tables, Module, TestCase
from experiment.core.mutation import get_mutants_of
from experiment.pydefects.get_projects import get_projects_bugs
from model.cfg.project_cfg import ProjectCFG
from model.project import Project, Merger
from pytest_failed_node_ids import EXCEPTIONS_FILE
import thorough
from tracing.trace_reader import TraceReader

STATUS_NO_REVEALING_NODE_IDS = "no_revealing_node_ids"
STATUS_DYNAMIC_NODE_IDS = "not_constant_node_ids"
STATUS_GOOD = "good"
STATUS_NO_MODULE_CFG = "no_module_cfg"
STATUS_NO_FAILED_ON_ASSERTION = "no_failed_on_assertion"
STATUS_BAD = "bad"

thorough_path = thorough.__file__

if __name__ == "__main__":
    db = SqliteExtDatabase(
        "selection.db",
        pragmas={
            "journal_mode": "wal",
            "cache_size": -64 * 1000,
            "foreign_key": 1,
            "ignore_check_constraints": 9,
            "synchronous": 0,
        }
    )
    DATABASE_PROXY.initialize(db)
    DATABASE_PROXY.create_tables(tables)

    repo_managers = get_projects_bugs(
        "pydefects.db",
    )
    silent = True
    remove_repos = True
    max_trace_size = 10  # MB
    results_root = Path(__file__).parent.parent.parent / "1experiments_results"
    dataset_path = results_root / "dataset_bugs"
    graphs_path_parent = results_root / "graphs_bugs"
    extra_requirements = [r.strip() for r in open("../requirements.txt").readlines()]
    repo_stat = RepoStatistics("repo_stats_bugs")

    logger.warning("Loading bad repos: {rs}", rs=repo_stat.bad_repos)
    logger.warning("Loading good repos: {rs}", rs=repo_stat.good_repos)
    logger.warning("Total repos in database with this query: {c}", c=len(repo_managers))
    halting_projects = ["nnweaver", "pyflightdata", "audio-clip-extractor", "clu", "ghost"]
    for manager in repo_managers:
        repo_and_commit = manager.repo_name + "@" + manager.commit_hash
        logger.info(manager)
        try:
            repo = Repo.get_by_id(repo_and_commit)
            if repo.status == STATUS_BAD:
                continue
        except Exception as e:
            repo = Repo.create(id=repo_and_commit, status=STATUS_BAD, name=manager.repo_name, url=manager.url,
                               fixed_commit=manager.commit_hash, buggy_commit="")

        logger.warning("Processing {n}", n=repo_and_commit)

        if manager.repo_name in halting_projects:
            continue

        try:
            try:
                fixed_root = manager.clone_to(dataset_path, overwrite_if_exists=False)
                buggy_root, buggy_hash = manager.clone_parent_to(dataset_path, overwrite_if_exists=True)
            except Exception as e:
                logger.log(e)
                continue
            repo.buggy_commit = buggy_hash

            fixed_project = Project(fixed_root, silence_output=silent)
            buggy_project = Project(buggy_root, silence_output=silent)
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
            repo.status = STATUS_NO_REVEALING_NODE_IDS
            repo.save()
            if len(new_failing_node_ids) > 0:
                with open(os.path.join(buggy_project.path, EXCEPTIONS_FILE)) as f:
                    exceptions = json.load(f)
                for node_id in new_failing_node_ids:
                    exc = exceptions[node_id]
                    logger.warning("Node id {node_id} failed with exception text: {exc}", node_id=node_id,
                                   exc=exc)
                failing_on_assertion_node_ids = set(node_ids_where_assertion_error(exceptions))
                repo.status = STATUS_NO_FAILED_ON_ASSERTION
                repo.save()
                if len(failing_on_assertion_node_ids) > 0:
                    repo.status = STATUS_NO_MODULE_CFG
                    repo.save()
                    repo_stat.mark_repo_as_good(manager)

                    logger.warning("Found node ids which failed on assertion!")
                    graphs_path = graphs_path_parent
                    module_under_test_path = manager.test_module_path
                    logger.info("Running the experiment for module {p}", p=module_under_test_path)
                    st = time()
                    buggy_project.run_command(
                        f"python3 {thorough_path} -t --trace_dir={buggy_project.path}",
                        extra_requirements=extra_requirements
                    )
                    elapsed_tracing = int(time() - st)
                    trace_reader = TraceReader(buggy_project.path)
                    module_under_test_absolute = os.path.join(buggy_project.path, module_under_test_path)
                    covering_node_ids, paths = trace_reader.get_traces_for(module_under_test_absolute)
                    covering_node_ids = set(covering_node_ids)
                    bad_node_ids = after - failing_on_assertion_node_ids
                    covering_node_ids -= bad_node_ids
                    not_failing_node_ids = covering_node_ids - failing_on_assertion_node_ids
                    not_failing_node_ids_as_params = " ".join(not_failing_node_ids)
                    return_code = buggy_project.run_command(f"pytest {not_failing_node_ids_as_params}")

                    if return_code == 0:
                        logger.warning("Test cases can be run individually")
                        cfg = ProjectCFG.create_from_path(buggy_project.path)
                        module_cfg = cfg.module_cfgs.get(module_under_test_absolute)
                        if module_cfg:
                            mutants = get_mutants_of(module_under_test_absolute)
                            stcov = StatementCoverage(buggy_project.path, buggy_project.path,
                                                      max_trace_size=max_trace_size)
                            brcov = BranchCoverage(buggy_project.path, buggy_project.path,
                                                   max_trace_size=max_trace_size)
                            ducov = DefUsePairsCoverage(buggy_project.path, buggy_project.path,
                                                        max_trace_size=max_trace_size)

                            repo.status = STATUS_GOOD
                            [module.delete() for module in repo.modules]
                            module = Module.create(
                                path=module_under_test_path,
                                m_pairs=len(module_cfg.intramethod_pairs),
                                im_pairs=len(module_cfg.intermethod_pairs),
                                ic_pairs=len(module_cfg.interclass_pairs),
                                statements=len(StatementCoverage.lines_in_module(module_cfg)),
                                branches=len(module_cfg.branches),
                                mutants=len(mutants),
                                bugs=len(failing_on_assertion_node_ids),
                                total_cases=len(covering_node_ids),
                                st_cov=stcov.coverage_of(module_under_test_absolute),
                                br_cov=brcov.coverage_of(module_under_test_absolute),
                                du_cov=ducov.coverage_of(module_under_test_absolute, of_type=CoverageMetric.ALL_PAIRS),
                                time=elapsed_tracing,
                                repo=repo,
                                is_full_cfg=module_cfg.is_full_cfg
                            )
                            module.save()
                            repo.save()
                            for node_id in (covering_node_ids - failing_on_assertion_node_ids):
                                TestCase.create(module=module, node_id=node_id, result="passed")
                            for node_id in failing_on_assertion_node_ids:
                                TestCase.create(module=module, node_id=node_id, result="revealed")
                            logger.warning("Saving {repo_name} to database", repo_name=repo_and_commit)
                        else:
                            logger.error("Could not find cfg for module under test {p}", p=module_under_test_absolute)
                    else:
                        logger.warning("Tests don't have constant ids: {p}", p=module_under_test_path)
                        repo_stat.mark_repo_as_bad(manager)
                        repo.status = STATUS_DYNAMIC_NODE_IDS
                        repo.save()
                else:
                    repo_stat.mark_repo_as_bad(manager)
            else:
                logger.warning("There are no new tests which failed in the merged version of code base")
                repo_stat.mark_repo_as_bad(manager)
            if remove_repos:
                fixed_project.delete_from_disk()
                buggy_project.delete_from_disk()

        except Exception as e:
            print(traceback.format_exc())
