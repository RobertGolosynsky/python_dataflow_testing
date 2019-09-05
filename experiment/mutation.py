import time
import os
import sys

import traceback
from pathlib import Path
from pprint import pprint

from glob2 import glob
from mutmut.__main__ import time_test_suite, python_source_files, add_mutations_by_file, Config, run_mutation_tests
from mutmut.cache import update_line_numbers, filename_and_mutation_id_from_pk, hash_of_tests


def current_time_millis_hex():
    return hex(int(round(time.time() * 1000)))


class MutationTestingResult:
    def __init__(self, total, killed_mutants, surviving_mutants,
                 surviving_mutants_timeout, suspicious_mutants):
        self.total = total
        self.killed_mutants = killed_mutants
        self.surviving_mutants = surviving_mutants
        self.surviving_mutants_timeout = surviving_mutants_timeout
        self.suspicious_mutants = suspicious_mutants


def main(path_to_module_under_test, runner, tests_dir,
         test_time_multiplier=2.0, test_time_base=0.0,
         swallow_output=True, dict_synonyms="", cache_only=False,
         pre_mutation=None, post_mutation=None, paths_to_exclude=None,
         backup=False,
         argument=None,
         no_cache=False
         ):
    # """return exit code, after performing an mutation test run.
    #
    # :return: the exit code from executing the mutation tests
    # :rtype: int
    # """
    # if version:
    #     print("mutmut version %s" % __version__)
    #     return 0
    #
    # if use_coverage and use_patch_file:
    #     raise click.BadArgumentUsage("You can't combine --use-coverage and --use-patch")
    #
    # valid_commands = ['run', 'results', 'apply', 'show', 'junitxml']
    # if command not in valid_commands:
    #     raise click.BadArgumentUsage('%s is not a valid command, must be one of %s' % (command, ', '.join(valid_commands)))
    #
    # if command == 'results' and argument:
    #     raise click.BadArgumentUsage('The %s command takes no arguments' % command)
    #
    dict_synonyms = [x.strip() for x in dict_synonyms.split(',')]
    #
    # if command in ('show', 'diff'):
    #     if not argument:
    #         print_result_cache()
    #         return 0
    #
    #     if argument == 'all':
    #         print_result_cache(show_diffs=True, dict_synonyms=dict_synonyms, print_only_filename=argument2)
    #         return 0
    #
    #     print(get_unified_diff(argument, dict_synonyms))
    #     return 0
    #
    # if use_coverage and not exists('.coverage'):
    #     raise FileNotFoundError('No .coverage file found. You must generate a coverage file to use this feature.')
    #
    # if command == 'results':
    #     print_result_cache()
    #     return 0
    #
    # if command == 'junitxml':
    #     print_result_cache_junitxml(dict_synonyms, suspicious_policy, untested_policy)
    #     return 0
    #
    # if command == 'apply':
    #     do_apply(argument, dict_synonyms, backup)
    #     return 0

    # paths_to_mutate = get_or_guess_paths_to_mutate(paths_to_mutate)

    # if not isinstance(paths_to_mutate, (list, tuple)):
    # paths_to_mutate = [x.strip() for x in paths_to_mutate.split(',')]

    # if not paths_to_mutate:
    #     raise click.BadOptionUsage('--paths-to-mutate', 'You must specify a list of paths to mutate. Either as a command line argument, or by setting paths_to_mutate under the section [mutmut] in setup.cfg')

    tests_dirs = []
    for p in tests_dir.split(':'):
        tests_dirs.extend(glob(p, recursive=True))

    # for p in paths_to_mutate:
    #     for pt in tests_dir.split(':'):
    #         tests_dirs.extend(glob(p + '/**/' + pt, recursive=True))
    del tests_dir

    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # stop python from creating .pyc files

    using_testmon = '--testmon' in runner

    #     print("""
    # - Mutation testing starting -
    #
    # These are the steps:
    # 1. A full test suite run will be made to make sure we
    #    can run the tests successfully and we know how long
    #    it takes (to detect infinite loops for example)
    # 2. Mutants will be generated and checked
    #
    # Results are stored in .mutmut-cache.
    # Print found mutants with `mutmut results`.
    #
    # Legend for output:
    # 🎉 Killed mutants.   The goal is for everything to end up in this bucket.
    # ⏰ Timeout.          Test suite took 10 times as long as the baseline so were killed.
    # 🤔 Suspicious.       Tests took a long time, but not long enough to be fatal.
    # 🙁 Survived.         This means your tests needs to be expanded.
    # """)
    baseline_time_elapsed = time_test_suite(
        swallow_output=not swallow_output,
        test_command=runner,
        using_testmon=using_testmon
    )

    # if using_testmon:
    #     copy('.testmondata', '.testmondata-initial')

    # if we're running in a mode with externally whitelisted lines
    # if use_coverage or use_patch_file:
    #     covered_lines_by_filename = {}
    #     if use_coverage:
    #         coverage_data = read_coverage_data()
    #     else:
    #         assert use_patch_file
    #         covered_lines_by_filename = read_patch_data(use_patch_file)
    #         coverage_data = None
    #
    #     def _exclude(context):
    #         try:
    #             covered_lines = covered_lines_by_filename[context.filename]
    #         except KeyError:
    #             if coverage_data is not None:
    #                 covered_lines = coverage_data.lines(os.path.abspath(context.filename))
    #                 covered_lines_by_filename[context.filename] = covered_lines
    #             else:
    #                 covered_lines = None
    #
    #         if covered_lines is None:
    #             return True
    #         current_line = context.current_line_index + 1
    #         if current_line not in covered_lines:
    #             return True
    #         return False
    # else:
    if True:
        def _exclude(context):
            del context
            return False

    # if command != 'run':
    #     raise click.BadArgumentUsage("Invalid command %s" % command)

    mutations_by_file = {}

    paths_to_exclude = paths_to_exclude or ''
    if paths_to_exclude:
        paths_to_exclude = [path.strip() for path in paths_to_exclude.split(',')]

    update_line_numbers(path_to_module_under_test)
    add_mutations_by_file(mutations_by_file, path_to_module_under_test, _exclude, dict_synonyms)

    # if argument is None:
    #     for path in paths_to_mutate:
    #         for filename in python_source_files(path, tests_dirs, paths_to_exclude):
    #             update_line_numbers(filename)
    #             add_mutations_by_file(mutations_by_file, filename, _exclude, dict_synonyms)
    # else:
    #
    #     filename, mutation_id = filename_and_mutation_id_from_pk(int(argument))
    #     mutations_by_file[filename] = [mutation_id]

    total = sum(len(mutations) for mutations in mutations_by_file.values())

    # print()
    # print('2. Checking mutants')

    config = Config(
        swallow_output=not swallow_output,
        test_command=runner,
        exclude_callback=_exclude,
        baseline_time_elapsed=baseline_time_elapsed,
        backup=backup,
        dict_synonyms=dict_synonyms,
        total=total,
        using_testmon=using_testmon,
        cache_only=cache_only,
        tests_dirs=tests_dirs,
        hash_of_tests=current_time_millis_hex() if no_cache else hash_of_tests(tests_dirs),
        test_time_multiplier=test_time_multiplier,
        test_time_base=test_time_base,
        pre_mutation=pre_mutation,
        post_mutation=post_mutation
    )
    print(hash_of_tests(tests_dirs))

    try:
        run_mutation_tests(config=config, mutations_by_file=mutations_by_file)

    except Exception as e:
        traceback.print_exc()
        return None
    else:
        return MutationTestingResult(total=config.total,
                                     killed_mutants=config.killed_mutants,
                                     surviving_mutants=config.surviving_mutants,
                                     surviving_mutants_timeout=config.surviving_mutants_timeout,
                                     suspicious_mutants=config.suspicious_mutants
                                     )
        # return compute_exit_code(config)
    # finally:
    #     print()  # make sure we end the output with a newline


class FakeSink(object):
    def write(self, *args):
        pass

    def writelines(self, *args):
        pass

    def close(self, *args):
        pass

    def flush(self):
        pass


class PrintSilencer:

    def __init__(self):
        self.blocked = False
        self.out = sys.__stdout__

    def block_print(self):
        self.blocked = True
        self.out = sys.stdout
        # sys.stdout = open(os.devnull, 'w')
        sys.stdout = FakeSink()

    def revert_print(self):
        if self.blocked:
            self.blocked = False
            sys.stdout = self.out


def run_mutation(project_root, module_under_test, test_cases, tests_root, no_cache=False):
    project_root = Path(project_root)
    module_under_test = Path(module_under_test)
    tests_root = Path(tests_root)

    if not module_under_test.is_absolute():
        module_under_test = project_root / module_under_test

    if not tests_root.is_absolute():
        tests_root = project_root / tests_root

    save_working_dir = os.curdir
    os.chdir(project_root)

    runner = "python3 -m pytest -x " + " ".join(test_cases)
    silencer = PrintSilencer()
    # silencer.block_print()
    res = main(str(module_under_test), runner, str(tests_root), no_cache=no_cache)
    # silencer.revert_print()

    os.chdir(save_working_dir)

    return res
