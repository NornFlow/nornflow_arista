"""Task decorators for Nornir tasks over Arista eAPI.

All names start with '_' so NornFlow's catalog never registers them.

'_eos_task': catch expected eAPI errors, return failed 'Result'.
'_with_node': inject a pyeapi 'Node' as second arg, wrap raw return in '_result_ok'.
'_eos_getter': '_eos_task' + '_with_node' combined — the one-stop decorator for
    read-only tasks where the body just talks to the node and returns raw output.
"""

from collections.abc import Callable
from functools import wraps
from typing import Any

from nornir.core.task import Result, Task
from pyeapi.eapilib import CommandError

from nornflow_arista.eos_api.exceptions import EapiConfigError
from nornflow_arista.tasks.task_helpers import (
    _node_for_task,
    _result_failed,
    _result_ok,
)


def _eos_task(fn: Callable[..., Result]) -> Callable[..., Result]:
    """Catch expected eAPI errors and return a failed 'Result'.

    Forwards workflow ``args`` as ``**kwargs`` to the wrapped task.
    """

    @wraps(fn)
    def wrapper(task: Task, **kwargs: Any) -> Result:
        try:
            return fn(task, **kwargs)
        except (EapiConfigError, CommandError, TypeError, ValueError) as exc:
            return _result_failed(task, exc)

    return wrapper


def _with_node(fn: Callable[..., Any]) -> Callable[..., Result]:
    """Inject a pyeapi 'Node' as second arg; wrap the raw return in '_result_ok'."""

    @wraps(fn)
    def wrapper(task: Task, **kwargs: Any) -> Result:
        node = _node_for_task(task)
        raw = fn(task, node, **kwargs)
        return _result_ok(task, raw)

    return wrapper


def _eos_getter(fn: Callable[..., Any]) -> Callable[..., Result]:
    """'_eos_task' + '_with_node' in one decorator."""
    return _eos_task(_with_node(fn))
