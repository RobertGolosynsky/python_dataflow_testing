import traceback
from pathlib import Path
from loguru import logger

from experiment.dataset_experiments.dataset_real_bugs_experiment import RepoStatistics
from experiment.pydefects.get_projects import get_projects
from model.project import Project
import mutation_experiment_cli

mutation_experiment_path = mutation_experiment_cli.__file__

if __name__ == "__main__":
    repo_managers = get_projects("pydefects.db",
                                 limit=None,
                                 time_less_then=60,
                                 coverage_greater_then=30,
                                 passed_greater_than=15,
                                 unique_repos=True,
                                 no_errors=True)

    max_mutation_run_time = 30 * 60

    results_root = Path(__file__).parent.parent.parent / "1experiments_results"
    dataset_path = results_root / "dataset_mutation"
    graphs_path_parent = results_root / "graphs_mutation"

    repo_stats = RepoStatistics("repo_stats_mutation")
    extra_requirements = [r.strip() for r in open("../requirements.txt").readlines()]
    for manager in repo_managers:
        if repo_stats.is_repo_bad(manager) or repo_stats.is_repo_suspicious(manager):
            continue
        logger.info(manager)
        try:
            logger.info("Downloading...")
            repo_root = manager.clone_to(dataset_path, overwrite_if_exists=False)
            project = Project(repo_root)
            logger.info(f"Downloaded project to {project.path}")
            logger.info("Creating venv...")
            project.create_venv(force_remove_previous=False)

            if project.tests_fail():
                logger.warning("Tests fail, marking repo as bad")
                repo_stats.mark_repo_as_bad(manager)
            elif project.tracing_fails():
                logger.error("Tests don't fail, but tracing does, marking repo as suspicious")
                repo_stats.mark_repo_as_suspicious(manager)
                # project.delete_from_disk()
            else:
                graphs_path = graphs_path_parent  # / project.project_name
                project.run_command(
                    f"python3 {mutation_experiment_path} --max_select=5 --min_pairs=5 --graphs_folder={graphs_path} --test_suite_sizes_count=20 --test_suite_coverages_count=20 --max_trace_size=10 --timeout={max_mutation_run_time}",
                    extra_requirements=extra_requirements
                )
                repo_stats.mark_repo_as_good(manager)
        except Exception as e:
            logger.error(traceback.format_exc())
