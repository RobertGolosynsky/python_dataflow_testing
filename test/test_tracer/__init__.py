from datetime import datetime
import os

from tracing.tracer import Tracer

from pathlib import Path
import tempfile
import inspect

from tracing.trace_reader import read_df, TraceReader
from config import PROJECT_NAME

THIS_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = THIS_DIR.parent.parent
TEMP_DIRECTORY = Path(tempfile.gettempdir())

CLEAN_LINKED_LIST_ROOT = PROJECT_ROOT / "dataset" / "linked_list_clean"
CLEAN_LINKED_LIST_LL = CLEAN_LINKED_LIST_ROOT / "core" / "ll.py"
BUGGY_LINKED_LIST_ROOT = PROJECT_ROOT / "dataset" / "linked_list_bug"
BUGGY_LINKED_LIST_LL = BUGGY_LINKED_LIST_ROOT / "core" / "ll.py"


def create_new_temp_dir():
    folder_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')
    folder_path = TEMP_DIRECTORY / PROJECT_NAME.lower() / folder_name
    os.makedirs(folder_path, exist_ok=False)
    return folder_path


def trace_this(function, project_root=PROJECT_ROOT, trace_root=TEMP_DIRECTORY, args=None, kwargs=None):
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    target_source_file = inspect.getsourcefile(function)

    keep = [str(project_root)]
    exclude = [str(project_root / "venv")]
    trace_folder = trace_root
    tracer = Tracer(keep, exclude, trace_folder_parent=str(trace_folder))

    trace_name = function.__name__
    tracer.start(trace_name)
    function(*args, **kwargs)
    tracer.stop()
    tracer.full_stop()

    trace_reader = TraceReader(trace_root)

    return trace_reader.trace_path(trace_name, target_source_file)


def get_trace(function, *args, **kwargs):
    trace_file_path = trace_this(function, *args, **kwargs)
    trace, _ = read_df(trace_file_path)
    return trace
