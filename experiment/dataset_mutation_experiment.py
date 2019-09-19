import builtins
import traceback
from pathlib import Path
from loguru import logger
from experiment.pydefects.get_projects import get_projects
from model.project import Project
import mutation_experiment_cli

mutation_experiment_path = mutation_experiment_cli.__file__

orig_print = builtins.print


def add_print_prefix(prefix):
    def print(*objs, **kwargs):
        return orig_print(prefix, *objs, **kwargs)

    builtins.print = print


if __name__ == "__main__":
    repo_managers = get_projects("pydefects.db",
                                 limit=None,
                                 time_less_then=2 * 60,
                                 coverage_greater_then=80,
                                 passed_greater_than=50,
                                 unique_repos=True,
                                 no_errors=True)

    max_mutation_run_time = 30 * 60

    results_root = Path(__file__).parent.parent.parent / "1experiments_results"
    dataset_path = results_root / "dataset_mutation"
    graphs_path_parent = results_root / "graphs_mutation"

    projects = []
    extra_requirements = [r.strip() for r in open("../requirements.txt").readlines()]
    for manager in repo_managers[50:]:
        logger.info(manager)
        add_print_prefix(manager.name)
        try:
            logger.info("Downloading...")
            repo_root = manager.clone_to(dataset_path, overwrite_if_exists=False)
            project = Project(repo_root)
            logger.info(f"Downloaded project to {project.path}")
            logger.info("Creating venv...")
            project.create_venv(force_remove_previous=False)

            if project.tests_fail():
                logger.warning("Tests fail, removing the repo")
                # project.delete_from_disk()
            elif project.tracing_fails():
                logger.error("Tests don't fail, but tracing does, removing the repo")

                # project.delete_from_disk()
            else:
                projects.append(project)
                graphs_path = graphs_path_parent / project.project_name
                project.run_command(
                    f"python3 {mutation_experiment_path} --max_select=5 --min_pairs=5 --graphs_folder={graphs_path} --test_suite_sizes_count=20 --test_suite_coverages_count=20 --max_trace_size=10 --timeout={max_mutation_run_time}",
                    extra_requirements=extra_requirements
                )
        except Exception as e:
            logger.error(traceback.format_exc())
