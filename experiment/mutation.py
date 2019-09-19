import contextlib
import hashlib
import time
import os
import sys
import importlib
import traceback
from collections import defaultdict
from pathlib import Path
from pprint import pprint
from shutil import move
from typing import List

from glob2 import glob
from joblib import Memory
from loguru import logger
from mutmut import MutationID, Context
from mutmut.__main__ import time_test_suite, python_source_files, add_mutations_by_file, Config, run_mutation_tests, \
    run_mutation, mutate_file, tests_pass, tests_pass_expanded
from mutmut.cache import update_line_numbers, filename_and_mutation_id_from_pk, hash_of_tests
import random

from tqdm import tqdm

cache_location = Path(".cached_mutants").resolve()
memory = Memory(location=cache_location, verbose=10000)


@memory.cache(ignore=["timeout"], verbose=100000)
def killed_mutants(path_to_module_under_test, test_cases_ids,
                   project_root,
                   timeout=None
                   ):
    logger.debug("Killed mutants of project {proj} will be saved in folder {f}", proj=project_root, f=cache_location)
    test_time_multiplier = 2.0
    test_time_base = 0.0
    swallow_output = True
    dict_synonyms = ""
    cache_only = False,
    pre_mutation = None
    post_mutation = None
    backup = False

    dict_synonyms = [x.strip() for x in dict_synonyms.split(',')]

    save_working_dir = os.getcwd()
    os.chdir(project_root)

    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # stop python from creating .pyc files

    pytest_args = []
    pytest_args += test_cases_ids

    baseline_time_elapsed = time_test_suite(
        swallow_output=not swallow_output,
        test_command=pytest_args,
        working_dir=project_root,
        using_testmon=False
    )

    mutations_by_file = {}

    update_line_numbers(path_to_module_under_test)
    add_mutations_by_file(mutations_by_file=mutations_by_file, filename=path_to_module_under_test,
                          dict_synonyms=dict_synonyms, config=None)

    mutations: List[MutationID] = mutations_by_file[path_to_module_under_test]

    total = sum(len(mutations) for mutations in mutations_by_file.values())

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
            filename=path_to_module_under_test,
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
            move(path_to_module_under_test + '.bak', path_to_module_under_test)
            os.chdir(save_working_dir)

    return killed, total


def remove_mutmut_cache(project_root):
    cache_file = Path(project_root) / ".mutmut-cache"
    if cache_file.exists():
        os.remove(cache_file)
