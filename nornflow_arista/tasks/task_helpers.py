"""Plumbing for Nornir tasks that talk to Arista EOS over eAPI.

Import this module only from 'nornflow_arista.tasks' (task modules), not from
the package '__init__'.

NornFlow task catalog:
    Names here use a leading '_' so these helpers are not registered as
    workflow tasks (NornFlow treats callables whose '__name__' starts with
    '_' as non-public).

Task functions declare workflow parameters explicitly; decorators forward
``**kwargs`` from Nornir ``task.params``.
"""

from typing import Any

from nornir.core.task import Result, Task
from pyeapi.client import Node
from pyeapi.utils import CliVariants

from nornflow_arista.eos_api.connect import ensure_pyeapi_connection, node_from_host

CommandsArg = str | list[str] | CliVariants


def _node_for_task(task: Task, **connect_overrides: Any) -> Node:
    """Return a pyeapi 'Node' for the task host, reusing Nornir's connection cache.

    Uses the 'pyeapi' connection plugin so NornFlow/Nornir 'close_connections()'
    can tear down sessions. Pass 'connect_overrides' only when you intentionally
    need a one-off connection outside the cache (for example a custom SSL context).
    """
    if connect_overrides:
        return node_from_host(task.host, **connect_overrides)
    return ensure_pyeapi_connection(task.host, task.nornir.config)


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
