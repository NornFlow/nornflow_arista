"""Mutating Nornir tasks: EOS configuration and save via eAPI."""

import contextlib
from pathlib import Path
from typing import Any

from jinja2 import Environment, StrictUndefined
from nornir.core.task import Result, Task
from pyeapi.eapilib import CommandError

from nornflow_arista.eos_api.exceptions import EapiConfigError
from nornflow_arista.tasks.decorators import _eos_task
from nornflow_arista.tasks.task_helpers import (
    _dry_run_skipped,
    _flatten_template_context,
    _node_for_task,
    _result_failed,
    _result_ok,
    CommandsArg,
)


def _checkpoint_destination(name: str) -> str:
    """Return the on-device flash path for a checkpoint basename."""
    safe = str(name).strip().replace(" ", "_")
    return f"flash:checkpoint_{safe}"


def _render_template_body(
    task: Task,
    *,
    template_path: str | None,
    template_string: str | None,
    variables: dict[str, Any] | None,
    encoding: str,
) -> str:
    """Render a Jinja2 template to EOS CLI lines for the task host.

    Raises:
        FileNotFoundError: When template_path does not exist.
        ValueError: When neither template_path nor template_string is provided.
    """
    tmpl_vars = variables if isinstance(variables, dict) else {}

    if template_string and str(template_string).strip():
        tmpl_body = str(template_string)
    elif template_path and str(template_path).strip():
        path = Path(str(template_path).strip()).expanduser().resolve()
        if not path.is_file():
            msg = f"template_path is not a file: {path}"
            raise FileNotFoundError(msg)
        tmpl_body = path.read_text(encoding=encoding)
    else:
        msg = 'Provide "template_string" or "template_path".'
        raise ValueError(msg)

    # Output is EOS CLI, not HTML; autoescape would corrupt config syntax.
    env = Environment(undefined=StrictUndefined, autoescape=False)  # noqa: S701
    template = env.from_string(tmpl_body)
    ctx = _flatten_template_context(task.host, tmpl_vars)
    return template.render(**ctx)


@_eos_task
def configure(task: Task, commands: CommandsArg) -> Result:
    """Push configuration lines in standard config mode (internally equivalent to
    'configure terminal' over eAPI).

    Args:
        commands: Config lines as a string, a list of strings, or 'CliVariants'
            as supported by 'pyeapi' 'Node.config'.

    Dry-run does not open a connection; it returns a skipped result.
    """
    if task.is_dry_run():
        return _dry_run_skipped(task, "would push configuration via configure terminal")
    node = _node_for_task(task)
    out = node.config(commands)
    return _result_ok(task, out, changed=True)


@_eos_task
def configure_session(
    task: Task,
    commands: CommandsArg,
    *,
    commit: bool = True,
    include_diff: bool = True,
    session_name: str | None = None,
) -> Result:
    """Apply configuration inside a 'configure session' and commit or abort.

    Args:
        commands: Same as 'configure'.
        commit: If True (default), run 'commit'; otherwise 'abort' the session.
        include_diff: If True (default), include 'show session-config diffs' text.
        session_name: Optional session name (pyeapi session id is set before opening the session).

    Dry-run does not open a connection. On failure after the session is opened,
    the session is aborted when possible so the device is not left mid-session.
    """
    if task.is_dry_run():
        return _dry_run_skipped(task, "would apply configuration in a configure session")
    node = _node_for_task(task)
    if session_name and str(session_name).strip():
        node._session_name = str(session_name).strip()  # noqa: SLF001
    node.configure_session()
    diff_text = None
    try:
        node.config(commands)
        if include_diff:
            diff_text = node.diff()
        if commit:
            node.commit()
        else:
            node.abort()
    except (CommandError, EapiConfigError, TypeError, ValueError) as exc:
        with contextlib.suppress(Exception):
            node.abort()
        raise exc  # noqa: TRY201

    payload: dict[str, Any] = {"committed": commit}
    if include_diff:
        payload["diff"] = diff_text
    return _result_ok(task, payload, changed=commit)


@_eos_task
def commit_session(task: Task, session_name: str) -> Result:
    """Commit a named configure session ('configure session <name>' + 'commit').

    Args:
        session_name: EOS configure session name to commit.

    Use when you need an explicit commit step in YAML.
    """
    if task.is_dry_run():
        return _dry_run_skipped(task, "would commit configure session")
    if not str(session_name).strip():
        msg = 'Task param "session_name" must be a non-empty string.'
        return _result_failed(task, ValueError(msg))
    node = _node_for_task(task)
    label = str(session_name).strip()
    out = node.run_commands([f"configure session {label}", "commit"], encoding="text")
    return _result_ok(task, out, changed=True)


@_eos_task
def abort_session(task: Task, session_name: str) -> Result:
    """Abort a named configure session ('configure session <name>' + 'abort').

    Args:
        session_name: EOS configure session name to abort.
    """
    if task.is_dry_run():
        return _dry_run_skipped(task, "would abort configure session")
    if not str(session_name).strip():
        msg = 'Task param "session_name" must be a non-empty string.'
        return _result_failed(task, ValueError(msg))
    node = _node_for_task(task)
    label = str(session_name).strip()
    out = node.run_commands([f"configure session {label}", "abort"], encoding="text")
    return _result_ok(task, out, changed=True)


@_eos_task
def configure_from_template(
    task: Task,
    *,
    template_path: str | None = None,
    template_string: str | None = None,
    variables: dict[str, Any] | None = None,
    encoding: str = "utf-8",
) -> Result:
    """Render a Jinja2 template, then push the result with 'configure terminal'.

    Args:
        template_path: Path to a template file on the runner filesystem (required unless
            'template_string' is set).
        template_string: Inline template (optional; wins over template_path when both set).
        variables: Optional dict merged into the template context (host.name, host.data, etc.).
        encoding: File encoding for template_path (default 'utf-8').

    Dry-run does not open a connection.
    """
    if task.is_dry_run():
        return _dry_run_skipped(task, "would render template and push configuration")
    try:
        rendered = _render_template_body(
            task,
            template_path=template_path,
            template_string=template_string,
            variables=variables,
            encoding=encoding,
        )
    except FileNotFoundError as exc:
        return _result_failed(task, exc)
    except ValueError as exc:
        return _result_failed(task, exc)
    node = _node_for_task(task)
    out = node.config(rendered)
    return _result_ok(task, out, changed=True)


@_eos_task
def safe_configure_from_template(
    task: Task,
    checkpoint_name: str,
    *,
    template_path: str | None = None,
    template_string: str | None = None,
    variables: dict[str, Any] | None = None,
    encoding: str = "utf-8",
) -> Result:
    """Checkpoint running-config, apply a template, and restore the checkpoint on apply failure.

    Combines 'create_checkpoint', 'configure_from_template', and conditional
    'configure_replace' in one per-host task so rollback runs even when NornFlow's
    built-in 'set_to' hook skips failed tasks (see NornFlow issue #87).

    Args:
        checkpoint_name: Checkpoint basename; stored as 'flash:checkpoint_<name>'.
        template_path: Path to a template file on the runner (required unless
            'template_string' is set).
        template_string: Inline template (optional; wins over template_path when both set).
        variables: Optional dict merged into the template context.
        encoding: File encoding for template_path (default 'utf-8').

    Dry-run does not open a connection. On apply failure after the checkpoint is
    written, 'configure replace' is attempted before returning a failed result.
    """
    if task.is_dry_run():
        return _dry_run_skipped(
            task,
            "would checkpoint, render template, push configuration, and restore on failure",
        )
    if not str(checkpoint_name).strip():
        msg = 'Task param "checkpoint_name" must be a non-empty string.'
        return _result_failed(task, ValueError(msg))
    try:
        rendered = _render_template_body(
            task,
            template_path=template_path,
            template_string=template_string,
            variables=variables,
            encoding=encoding,
        )
    except FileNotFoundError as exc:
        return _result_failed(task, exc)
    except ValueError as exc:
        return _result_failed(task, exc)

    dest = _checkpoint_destination(checkpoint_name)
    node = _node_for_task(task)
    checkpoint_out = node.run_commands([f"copy running-config {dest}"], encoding="text")
    try:
        apply_out = node.config(rendered)
    except (CommandError, EapiConfigError, TypeError, ValueError) as exc:
        with contextlib.suppress(Exception):
            node.run_commands([f"configure replace {dest}"], encoding="text")
        raise exc  # noqa: TRY201

    return _result_ok(
        task,
        {"destination": dest, "checkpoint_raw": checkpoint_out, "apply_raw": apply_out},
        changed=True,
    )


@_eos_task
def configure_replace(task: Task, path: str) -> Result:
    """Replace running-config with contents from a file or URL the device can read.

    Args:
        path: Location the switch can read (for example 'flash:myconfig.cfg'). Passed to
            'configure replace <path>'.

    Dry-run does not open a connection.
    """
    if task.is_dry_run():
        return _dry_run_skipped(task, "would run configure replace")
    if not str(path).strip():
        msg = 'Task param "path" must be a non-empty string.'
        return _result_failed(task, ValueError(msg))
    target = str(path).strip()
    node = _node_for_task(task)
    out = node.run_commands([f"configure replace {target}"], encoding="text")
    return _result_ok(task, out, changed=True)


@_eos_task
def create_checkpoint(task: Task, name: str) -> Result:
    """Save running-config to a checkpoint file on flash.

    Args:
        name: Checkpoint basename. Written to 'flash:checkpoint_<name>'.

    Dry-run does not open a connection.
    """
    if task.is_dry_run():
        return _dry_run_skipped(task, "would copy running-config to checkpoint on flash")
    if not str(name).strip():
        msg = 'Task param "name" must be a non-empty string.'
        return _result_failed(task, ValueError(msg))
    dest = _checkpoint_destination(name)
    node = _node_for_task(task)
    out = node.run_commands([f"copy running-config {dest}"], encoding="text")
    return _result_ok(task, {"destination": dest, "raw": out}, changed=True)


@_eos_task
def rollback(task: Task, steps: int = 1) -> Result:
    """Rollback the last configuration commit(s) ('configure rollback <n>').

    Args:
        steps: Number of commits to roll back (default 1).

    Dry-run does not open a connection.
    """
    if task.is_dry_run():
        return _dry_run_skipped(task, "would run configure rollback")
    try:
        n = int(steps)
    except (TypeError, ValueError):
        msg = 'Parameter "steps" must be an integer.'
        return _result_failed(task, ValueError(msg))
    if n < 1:
        msg = 'Parameter "steps" must be >= 1.'
        return _result_failed(task, ValueError(msg))
    node = _node_for_task(task)
    out = node.run_commands([f"configure rollback {n}"], encoding="text")
    return _result_ok(task, out, changed=True)


@_eos_task
def save_config(task: Task) -> Result:
    """Save running-config to startup-config ('write memory').

    Dry-run does not open a connection.
    """
    if task.is_dry_run():
        return _dry_run_skipped(task, "would save running-config to startup-config")
    node = _node_for_task(task)
    out = node.enable("write memory")
    return _result_ok(task, out, changed=True)


@_eos_task
def copy_from_remote(
    task: Task,
    *,
    command: str | None = None,
    source: str | None = None,
    destination: str | None = None,
) -> Result:
    """Tell the device to copy from a remote source into a local destination (pull).

    Runs a single 'copy' command in enable mode. Either pass 'command' as the full CLI line,
    or pass 'source' and 'destination' to build: 'copy <source> <destination>'.

    Args:
        command: Full 'copy ...' line (optional; overrides 'source' / 'destination').
        source: Remote location the device can reach (used with 'destination').
        destination: Local path (for example 'flash:file.cfg').

    Dry-run does not open a connection.
    """
    if task.is_dry_run():
        return _dry_run_skipped(
            task,
            "would run copy from remote source to destination on device",
        )
    if command and str(command).strip():
        cmd = str(command).strip()
    elif source and destination:
        cmd = f"copy {source} {destination}"
    else:
        msg = 'Provide "command" or both "source" and "destination".'
        return _result_failed(task, ValueError(msg))
    node = _node_for_task(task)
    out = node.enable(cmd)
    return _result_ok(task, out, changed=True)
