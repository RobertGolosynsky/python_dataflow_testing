import contextlib
import hashlib
import time
import os
import sys
import importlib
import traceback
from collections import defaultdict
from pathlib import Path
from shutil import move
from typing import List

from joblib import Memory
from loguru import logger
from mutmut import MutationID, Context
from mutmut.__main__ import time_test_suite, add_mutations_by_file, Config, mutate_file, tests_pass_expanded
from mutmut.cache import update_line_numbers, hash_of_tests

from tqdm import tqdm

from tracing.trace_reader import TraceReader
from util.cache import cache

cache_location = Path("/tmp/thorough/.cached_mutants").resolve()
cache_location_2 = Path("/tmp/thorough/.cached_mutants_mine").resolve()
memory = Memory(location=cache_location, verbose=10000)


def killed_mutants(
        module_under_test_path,
        project_root,
        not_failing_node_ids,
        timeout=None
):
    rel_path = Path(module_under_test_path).relative_to(project_root)
    key = f"{rel_path}"
    return killed_mutants_raw(module_under_test_path, project_root,
                              not_failing_node_ids,
                              timeout=timeout, cache_key=key)


# @memory.cache(ignore=["path_to_module_under_test", "test_cases_ids", "project_root", "timeout"],
#               verbose=100000)
def key(cache_key):
    return hashlib.sha1(cache_key.encode("utf-8")).hexdigest()


@cache(key=key, arg_names=["cache_key"], location=str(cache_location_2), version=2)
def killed_mutants_raw(
        module_under_test_path,
        project_root,
        not_failing_node_ids,
        timeout=None,
        cache_key=None
):
    logger.debug("Killed mutants of project {proj} will be saved in folder {f}", proj=project_root, f=cache_location)
    test_time_multiplier = 2.0
    test_time_base = 0.0
    swallow_output = True
    cache_only = False,
    pre_mutation = None
    post_mutation = None
    backup = False

    save_working_dir = os.getcwd()
    os.chdir(project_root)

    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # stop python from creating .pyc files



    pytest_args = []
    pytest_args += not_failing_node_ids

    baseline_time_elapsed = time_test_suite(
        swallow_output=not swallow_output,
        test_command=pytest_args,
        working_dir=project_root,
        using_testmon=False
    )

    mutations: List[MutationID] = get_mutants_of(module_under_test_path)

    total = len(mutations)

    timed_out_mutants = set()
    killed = defaultdict(set)
    st = time.time()
    prog = 0
    for mutation_id in tqdm(mutations):
        prog += 1
        mut = mutation_id.line, mutation_id.index

        config = Config(
            swallow_output=not swallow_output,
            test_command=pytest_args,
            working_dir=project_root,
            baseline_time_elapsed=baseline_time_elapsed,
            backup=backup,
            dict_synonyms=[],
            total=total,
            using_testmon=False,
            cache_only=cache_only,
            tests_dirs=[],
            hash_of_tests=hash_of_tests([]),
            test_time_multiplier=test_time_multiplier,
            test_time_base=test_time_base,
            pre_mutation=pre_mutation,
            post_mutation=post_mutation,
            coverage_data=None,
            covered_lines_by_filename=None,
        )

        context = Context(
            mutation_id=mutation_id,
            filename=module_under_test_path,
            dict_synonyms=config.dict_synonyms,
            config=config,
        )

        try:
            mutate_file(
                backup=True,
                context=context
            )

            try:
                # those test cases that killed this mutant
                # they failed - which is good
                failed_test_cases_ids = tests_pass_expanded(config=config, working_dir=project_root, callback=print)
            except TimeoutError:
                failed_test_cases_ids = None
            if failed_test_cases_ids is None:
                # This means test cases timed out
                # we can't figure out which ones exactly
                # so we don't use this mutant in statistics
                timed_out_mutants.add(mut)
            else:
                for test_case_id in failed_test_cases_ids:
                    killed[test_case_id].add(mut)

            if timeout and prog > 2 and prog < total / 2:
                time_per_item = (time.time() - st) / prog
                estimate = time_per_item * total
                if estimate > timeout * 1.1:
                    raise TimeoutError("It will take too much time")

        except Exception:
            raise
        finally:
            move(module_under_test_path + '.bak', module_under_test_path)
            os.chdir(save_working_dir)

    return killed, total


def remove_mutmut_cache(project_root):
    cache_file = Path(project_root) / ".mutmut-cache"
    if cache_file.exists():
        os.remove(cache_file)


def get_mutants_of(path_to_module_under_test):
    mutations_by_file = {}

    update_line_numbers(path_to_module_under_test)
    add_mutations_by_file(mutations_by_file=mutations_by_file, filename=path_to_module_under_test,
                          dict_synonyms=[""], config=None)

    return mutations_by_file[path_to_module_under_test]
