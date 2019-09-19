import os
import traceback
import json
from pathlib import Path
from pprint import pformat
from loguru import logger
from experiment.pydefects.get_projects import get_projects
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


if __name__ == "__main__":
    repo_managers = get_projects("pydefects.db",
                                 limit=None,
                                 time_less_then=2 * 60,
                                 coverage_greater_then=80,
                                 passed_greater_than=50,
                                 unique_repos=False,
                                 no_errors=False)

    results_root = Path(__file__).parent.parent.parent / "1experiments_results"
    dataset_path = results_root / "dataset_bugs"
    graphs_path_parent = results_root / "graphs_bugs"
    projects = []
    extra_requirements = [r.strip() for r in open("../requirements.txt").readlines()]

    for manager in repo_managers[155:]:
        logger.info(manager)
        try:

            fixed_root = manager.clone_to(dataset_path, overwrite_if_exists=False)
            buggy_root = manager.clone_parent_to(dataset_path, overwrite_if_exists=False)
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

            logger.info("Before merge failed node ids: {data}", data=pformat(buggy_failed_node_ids_before_merge))
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
                    logger.warning("Node id {node_id} failed with exception text: {exc}", node_id=node_id, exc=exc)
                good_node_ids = node_ids_where_assertion_error(exceptions)
                if len(good_node_ids):
                    logger.warning("Found node ids which failed on assertion!")
                    node_ids = " ".join(good_node_ids)
                    graphs_path = graphs_path_parent / buggy_project.project_name
                    logger.info("Running the experiment")
                    buggy_project.run_command(
                        f"python3 {real_bugs_experiment_path} --node_ids {node_ids} --graphs_folder={graphs_path} --test_suite_sizes_count=20 --test_suite_coverages_count=20 --max_trace_size=10",
                        extra_requirements=extra_requirements
                    )
                # fixed_project.delete_from_disk()
            else:
                logger.warning("There are no new tests which failed in the merged version of code base")
                # fixed_project.delete_from_disk()
                # buggy_project.delete_from_disk()

        except Exception as e:
            print(traceback.format_exc())
