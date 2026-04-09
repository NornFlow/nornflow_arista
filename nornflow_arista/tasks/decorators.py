"""Task decorators for Nornir tasks over Arista eAPI.

All names start with '_' so NornFlow's catalog never registers them.

'_eos_task': catch expected eAPI errors, return failed 'Result'.
'_with_node': inject a pyeapi 'Node' as second arg, wrap raw return in '_result_ok'.
'_eos_getter': '_eos_task' + '_with_node' combined — the one-stop decorator for
    read-only tasks where the body just talks to the node and returns raw output.
"""

from collections.abc import Callable
from functools import wraps

from nornir.core.task import Result, Task
from pyeapi.eapilib import CommandError

from nornflow_arista.eos_api.exceptions import EapiConfigError
from nornflow_arista.tasks.task_helpers import (
    _node_for_task,
    _result_failed,
    _result_ok,
)


def _eos_task(fn: Callable[[Task], Result]) -> Callable[[Task], Result]:
    """Catch expected eAPI errors and return a failed 'Result'.

    Other exceptions propagate. '@wraps' preserves name, doc, and annotations
    so NornFlow discovery still sees a proper '(task: Task) -> Result' task.
    """

    @wraps(fn)
    def wrapper(task: Task) -> Result:
        try:
            return fn(task)
        except (EapiConfigError, CommandError, TypeError, ValueError) as exc:
            return _result_failed(task, exc)

    return wrapper


def _with_node(fn):
    """Inject a pyeapi 'Node' as second arg; wrap the raw return in '_result_ok'.

    The inner function signature is '(task, node) -> <raw output>'.
    Raise inside the body to signal failure (pair with '_eos_task' on top).
    """

    @wraps(fn)
    def wrapper(task: Task) -> Result:
        node = _node_for_task(task)
        raw = fn(task, node)
        return _result_ok(task, raw)

    return wrapper


def _eos_getter(fn):
    """'_eos_task' + '_with_node' in one decorator.

    Use for read-only tasks whose body receives '(task, node)' and returns raw
    output. Errors become failed 'Result' objects; raw output becomes
    '_result_ok(task, raw)'.
    """
    return _eos_task(_with_node(fn))
