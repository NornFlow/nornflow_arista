"""Tests for task_helpers: template context flattening and result factories."""

from unittest.mock import MagicMock

from nornflow_arista.tasks.task_helpers import (
    _dry_run_skipped,
    _flatten_template_context,
    _result_failed,
    _result_ok,
)


def _fake_task(host: object = None) -> MagicMock:
    task = MagicMock()
    task.host = host if host is not None else MagicMock()
    return task


# --------------------------------------------------------------------------- #
# _flatten_template_context                                                     #
# --------------------------------------------------------------------------- #

def test_flatten_context_includes_host() -> None:
    host = MagicMock()
    ctx = _flatten_template_context(host, {})
    assert ctx["host"] is host


def test_flatten_context_sets_hostname_from_host_name() -> None:
    host = MagicMock()
    host.name = "leaf01"
    ctx = _flatten_template_context(host, {})
    assert ctx["hostname"] == "leaf01"


def test_flatten_context_merges_host_data() -> None:
    host = MagicMock()
    host.name = "leaf01"
    host.data = {"site": "dc1", "role": "leaf"}
    ctx = _flatten_template_context(host, {})
    assert ctx["site"] == "dc1"
    assert ctx["role"] == "leaf"


def test_flatten_context_extra_wins_over_host_data() -> None:
    """Extra vars are set before host.data so setdefault skips clashing host.data keys."""
    host = MagicMock()
    host.name = "leaf01"
    host.data = {"site": "dc1"}
    ctx = _flatten_template_context(host, {"site": "override"})
    assert ctx["site"] == "override"


def test_flatten_context_none_host() -> None:
    ctx = _flatten_template_context(None, {"key": "val"})
    assert ctx["host"] is None
    assert ctx["key"] == "val"


def test_flatten_context_none_extra_treated_as_empty() -> None:
    host = MagicMock()
    host.name = "sw1"
    host.data = {"x": 1}
    ctx = _flatten_template_context(host, None)
    assert ctx["x"] == 1


# --------------------------------------------------------------------------- #
# _result_ok                                                                    #
# --------------------------------------------------------------------------- #

def test_result_ok_not_failed() -> None:
    task = _fake_task()
    r = _result_ok(task, {"data": 1})
    assert not r.failed
    assert r.result == {"data": 1}
    assert not r.changed


def test_result_ok_changed_flag() -> None:
    task = _fake_task()
    r = _result_ok(task, "ok", changed=True)
    assert r.changed


# --------------------------------------------------------------------------- #
# _result_failed                                                                #
# --------------------------------------------------------------------------- #

def test_result_failed_is_failed() -> None:
    task = _fake_task()
    exc = ValueError("bad input")
    r = _result_failed(task, exc)
    assert r.failed
    assert r.exception is exc
    assert "bad input" in r.result


# --------------------------------------------------------------------------- #
# _dry_run_skipped                                                              #
# --------------------------------------------------------------------------- #

def test_dry_run_skipped_structure() -> None:
    task = _fake_task()
    r = _dry_run_skipped(task, "would do something")
    assert not r.failed
    assert not r.changed
    assert r.result["dry_run"] is True
    assert r.result["skipped"] == "would do something"
