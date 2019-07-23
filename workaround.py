import runpy
import sys
from pathlib import Path
import pytest

from tracing.tracer import Tracer

sys.argv.append("--ignore=dataset")
# sys.argv.append("--ignore=test/test_create")
# sys.argv.append("--ignore=test/test_create_basic_cfg")
# sys.argv.append("--ignore=test/test_util")
# sys.argv.append("--ignore=test/test_def_use")
# sys.argv.append("--ignore=test/test_model")

t = Tracer(
    [
        str("/home/robert/Documents/master/code/python_dataflow_testing"),
    ],
    [
        str("/home/robert/Documents/master/code/python_dataflow_testing/test"),
        str("/home/robert/Documents/master/code/python_dataflow_testing/venv")
    ]
)

# print(help(pytest))


class MyPlugin:
    def __init__(self, tracer):
        self.tracer = tracer
        # self.log = open("out.log", "w")

    def pytest_runtest_call(self, item):
        # self.log.write(str(dir(item))+"\n")
        # self.log.write(str(item.location)+"\n")
        # self.log.write(item.name+"\n")
        #
        #item_location = item.location
        self.tracer.start(trace_name="_".join(item.name))

    def pytest_runtest_teardown(self, item):
        # self.log.write(item.name + "\n")
        self.tracer.stop()


pytest.main(["--ignore=dataset"],  plugins=[MyPlugin(tracer=t)])

# t.trace(lambda: runpy.run_module('pytest', run_name='__main__', alter_sys=True))
