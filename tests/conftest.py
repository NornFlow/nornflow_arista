"""Shared fixtures for nornflow_arista tests."""

from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock

import pytest
from nornir.core.inventory import Host
from nornir.core.task import Result, Task


@pytest.fixture
def eos_host() -> Host:
    """Nornir host with typical eAPI inventory fields."""
    return Host(
        name="sw1",
        hostname="10.0.0.1",
        username="admin",
        password="secret",
        port=443,
        data={"eapi_transport": "https", "eapi_timeout": 90},
    )


@pytest.fixture
def make_task(eos_host: Host) -> Callable[..., Task]:
    """Build a Nornir Task whose ``params`` mirror workflow ``args``."""

    def _make(**params: Any) -> Task:
        dry_run = bool(params.pop("_test_dry_run", False))
        task = Task(
            task=MagicMock(),
            nornir=MagicMock(),
            global_dry_run=dry_run,
            processors=MagicMock(),
            name="test_task",
            **params,
        )
        task.host = eos_host
        return task

    return _make


def run_task_like_nornir(task_fn: Callable[..., Result], task: Task) -> Result:
    """Invoke a decorated task the way Nornir does (``fn(task, **task.params)``)."""
    return task_fn(task, **task.params)
