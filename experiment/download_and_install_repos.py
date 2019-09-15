import shutil
import subprocess
import traceback
from pathlib import Path

from experiment.pydefects.get_projects import get_projects, RepositoryManager
from model.project import Project

if __name__ == "__main__":
    repo_managers = get_projects("pydefects.db",
                                 limit=None,
                                 time_less_then=2 * 60,
                                 coverage_greater_then=50,
                                 passed_greater_than=50,
                                 unique_repos=True,
                                 no_errors=True)

    dataset_path = Path(__file__).parent.parent / "dataset"
    projects = []
    for manager in repo_managers[:1]:
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
            else:
                projects.append(project)
        except subprocess.CalledProcessError as e:
            print(traceback.format_exc())
            raise


