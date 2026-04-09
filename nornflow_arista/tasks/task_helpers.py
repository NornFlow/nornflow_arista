"""Plumbing for Nornir tasks that talk to Arista EOS over eAPI.

Import this module only from 'nornflow_arista.tasks' (task modules), not from
the package '__init__'.

NornFlow task catalog:
    Names here use a leading '_' so these helpers are not registered as
    workflow tasks (NornFlow treats callables whose '__name__' starts with
    '_' as non-public).

Decorator '_eos_task':
    Apply '@_eos_task' to real task functions in sibling modules (for example
    'getters.py'). It wraps '(task: Task) -> Result', catches expected
    eAPI/config errors, and turns them into failed 'Result' objects.
    'functools.wraps' preserves the wrapped function's name and annotations
    so the decorated callable still satisfies NornFlow's Nornir-task discovery.
"""

from collections.abc import Callable
from functools import wraps
from typing import Any

from nornir.core.task import Result, Task
from pyeapi.client import Node
from pyeapi.eapilib import CommandError

from nornflow_arista.eos_api.connect import node_from_host
from nornflow_arista.eos_api.exceptions import EapiConfigError


def _node_for_task(task: Task, **connect_overrides: Any) -> Node:
    """Return a pyeapi 'Node' for the Nornir host carried by 'task'."""
    return node_from_host(task.host, **connect_overrides)


def _result_ok(task: Task, result: Any, *, changed: bool = False) -> Result:
    """Return a successful Nornir 'Result' wrapping 'result'."""
    return Result(host=task.host, result=result, failed=False, changed=changed)


def _result_failed(task: Task, exc: BaseException) -> Result:
    """Return a failed Nornir 'Result' built from 'exc' (message on 'result')."""
    return Result(host=task.host, result=str(exc), failed=True, exception=exc)


def _dry_run_skipped(task: Task, description: str) -> Result:
    """Return a successful result describing mutating work skipped under dry-run."""
    return Result(
        host=task.host,
        result={"dry_run": True, "skipped": description},
        failed=False,
        changed=False,
    )


def _params(task: Task) -> dict[str, Any]:
    """Return 'task.params' as a dict, or an empty dict if missing or not a mapping."""
    raw = task.params
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    return {}

def _flatten_template_context(host: Any, extra: dict[str, Any] | None) -> dict[str, Any]:
    """Build a simple Jinja context from the Nornir host plus optional 'variables'."""
    ctx: dict[str, Any] = dict(extra or {})
    ctx.setdefault("host", host)
    if host is not None:
        ctx.setdefault("hostname", getattr(host, "name", None))
        hd = getattr(host, "data", None)
        if isinstance(hd, dict):
            for k, v in hd.items():
                ctx.setdefault(k, v)
    return ctx
