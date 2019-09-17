import shutil
import subprocess
import traceback
from pathlib import Path

from experiment.pydefects.get_projects import get_projects
from model.project import Project
import mutation_experiment

mutation_experiment_path = mutation_experiment.__file__

if __name__ == "__main__":
    repo_managers = get_projects("pydefects.db",
                                 limit=None,
                                 time_less_then=2 * 60,
                                 coverage_greater_then=50,
                                 passed_greater_than=50,
                                 unique_repos=True,
                                 no_errors=True)

    dataset_path = Path(__file__).parent.parent.parent / "dataset_mutation"
    graphs_path = Path(__file__).parent.parent.parent/"graphs_mutation"
    projects = []
    extra_requirements = [r.strip() for r in open("../requirements.txt").readlines()]
    timeout = 30*60
    for manager in repo_managers:
        print(manager)
        try:
            print("Downloading...")
            repo_root = manager.clone_to(dataset_path)
            project = Project(repo_root)
            print(f"Downloaded project to {project._path}")
            print("Creating venv...")
            project.create_venv()

            if project.tests_fail():
                print("Tests fail, removing the repo")
                project.delete_from_disk()
            elif project.tracing_fails():
                print("Tests don't fail, but tracing does, removing the repo")
                project.delete_from_disk()
            else:
                projects.append(project)
                graphs_path = graphs_path / project.project_name
                project.run_command(
                    f"python3 {mutation_experiment_path} --max_select=5 --graphs_folder={graphs_path} --test_suite_sizes_count=20 --test_suite_coverages_count=20 --max_trace_size=10 --timeout={timeout}",
                    extra_requirements=extra_requirements
                )
        except Exception as e:
            print(traceback.format_exc())
