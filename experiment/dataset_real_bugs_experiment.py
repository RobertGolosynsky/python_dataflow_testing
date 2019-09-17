import traceback
from pathlib import Path
from pprint import pprint

from experiment.pydefects.get_projects import get_projects
from model.project import Project, Merger
import real_bugs_experiment

real_bugs_experiment_path = real_bugs_experiment.__file__

if __name__ == "__main__":
    repo_managers = get_projects("pydefects.db",
                                 limit=None,
                                 time_less_then=2 * 60,
                                 coverage_greater_then=50,
                                 passed_greater_than=50,
                                 unique_repos=True,
                                 no_errors=True)

    dataset_path = Path(__file__).parent.parent.parent / "dataset_bugs"
    graphs_path_parent = Path(__file__).parent.parent.parent / "graphs_bugs"
    projects = []
    extra_requirements = [r.strip() for r in open("../requirements.txt").readlines()]

    for manager in repo_managers:
        print(manager)
        try:
            print("Downloading...")
            fixed_root = manager.clone_to(dataset_path)
            buggy_root = manager.clone_parent_to(dataset_path)
            fixed_project = Project(fixed_root)
            buggy_project = Project(buggy_root)
            print(f"Downloaded fixed project to {fixed_project._path}")
            print(f"Downloaded buggy project to {buggy_project._path}")

            print("Creating venv...")
            fixed_project.create_venv()
            buggy_project.create_venv()
            print("Venv created...")

            fixed_failed_node_ids = fixed_project.run_tests_get_failed_node_ids()
            buggy_failed_node_ids_before_merge = buggy_project.run_tests_get_failed_node_ids()

            print(f"fixed {fixed_failed_node_ids}")
            print(f"buggy {buggy_failed_node_ids_before_merge}")

            merger = Merger(fixed_project, buggy_project)
            merger.move_test_from_fixed_to_buggy()

            buggy_failed_node_ids_after_merge = buggy_project.run_tests_get_failed_node_ids()

            print("before:")
            pprint(buggy_failed_node_ids_before_merge)

            print("after:")
            pprint(buggy_failed_node_ids_after_merge)

            print("difference:")
            before = set(buggy_failed_node_ids_before_merge)
            after = set(buggy_failed_node_ids_after_merge)
            new_failing_node_ids = after-before
            pprint(new_failing_node_ids)

            if len(new_failing_node_ids) > 0:
                node_ids = " ".join(new_failing_node_ids)
                graphs_path = graphs_path_parent/buggy_project.project_name
                buggy_project.run_command(
                        f"python3 {real_bugs_experiment_path} --node_ids {node_ids} --graphs_folder={graphs_path} --test_suite_sizes_count=20 --test_suite_coverages_count=20 --max_trace_size=10",
                        extra_requirements=extra_requirements
                )
                fixed_project.delete_from_disk()
            else:
                fixed_project.delete_from_disk()
                buggy_project.delete_from_disk()

        except Exception as e:
            print(traceback.format_exc())
