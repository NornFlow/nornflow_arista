"""Mutating Nornir tasks: EOS configuration and save via eAPI."""

import os
from pathlib import Path
from typing import Any

from jinja2 import Environment, StrictUndefined
from nornir.core.task import Result, Task
from pyeapi.eapilib import CommandError

from nornflow_arista.eos_api.exceptions import EapiConfigError
from nornflow_arista.tasks.decorators import _eos_task
from nornflow_arista.tasks.task_helpers import (
    _dry_run_skipped,
    _node_for_task,
    _params,
    _result_failed,
    _result_ok,
    _flatten_template_context,
)

@_eos_task
def configure(task: Task) -> Result:
    """Push configuration lines in standard config mode (internally equivalent to
    'configure terminal' over eAPI).

    Params:
        commands: Config lines as a string, a list of strings, or 'CliVariants'
            as supported by 'pyeapi' 'Node.config'.

    Dry-run does not open a connection; it returns a skipped result.
    """
    if task.is_dry_run():
        return _dry_run_skipped(task, "would push configuration via configure terminal")
    p = _params(task)
    commands = p.get("commands")
    if commands is None:
        msg = 'Missing required task param "commands".'
        return _result_failed(task, ValueError(msg))
    node = _node_for_task(task)
    out = node.config(commands)
    return _result_ok(task, out, changed=True)


@_eos_task
def configure_session(task: Task) -> Result:
    """Apply configuration inside a 'configure session' and commit or abort.

    Params:
        commands: Same as 'configure'.
        commit: If True (default), run 'commit'; otherwise 'abort' the session.
        include_diff: If True (default), include 'show session-config diffs' text.
        session_name: Optional session name (pyeapi session id is set before opening the session).

    Dry-run does not open a connection. On failure after the session is opened,
    the session is aborted when possible so the device is not left mid-session.
    """
    if task.is_dry_run():
        return _dry_run_skipped(task, "would apply configuration in a configure session")
    p = _params(task)
    commands = p.get("commands")
    if commands is None:
        msg = 'Missing required task param "commands".'
        return _result_failed(task, ValueError(msg))
    commit = bool(p.get("commit", True))
    include_diff = bool(p.get("include_diff", True))
    session_name = p.get("session_name")

    node = _node_for_task(task)
    if session_name is not None and str(session_name).strip():
        node._session_name = str(session_name).strip()
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
    except (CommandError, EapiConfigError, TypeError, ValueError):
        try:
            node.abort()
        except CommandError:
            pass
        raise

    payload: dict[str, Any] = {"committed": commit}
    if include_diff:
        payload["diff"] = diff_text
    return _result_ok(task, payload, changed=commit)


@_eos_task
def commit_session(task: Task) -> Result:
    """Commit a named configure session ('configure session <name>' + 'commit').

    Params:
        session_name: EOS configure session name to commit (required).

    Use when you need an explicit commit step in YAML.
    """
    if task.is_dry_run():
        return _dry_run_skipped(task, "would commit configure session")
    p = _params(task)
    name = p.get("session_name")
    if name is None or not str(name).strip():
        msg = 'Missing required task param "session_name".'
        return _result_failed(task, ValueError(msg))
    node = _node_for_task(task)
    label = str(name).strip()
    out = node.run_commands([f"configure session {label}", "commit"], encoding="text")
    return _result_ok(task, out, changed=True)


@_eos_task
def abort_session(task: Task) -> Result:
    """Abort a named configure session ('configure session <name>' + 'abort').

    Params:
        session_name: EOS configure session name to abort (required).
    """
    if task.is_dry_run():
        return _dry_run_skipped(task, "would abort configure session")
    p = _params(task)
    name = p.get("session_name")
    if name is None or not str(name).strip():
        msg = 'Missing required task param "session_name".'
        return _result_failed(task, ValueError(msg))
    node = _node_for_task(task)
    label = str(name).strip()
    out = node.run_commands([f"configure session {label}", "abort"], encoding="text")
    return _result_ok(task, out, changed=True)


@_eos_task
def configure_from_template(task: Task) -> Result:
    """Render a Jinja2 template, then push the result with 'configure terminal'.

    Params:
        template_path: Path to a template file on the runner filesystem (required unless
            'template_string' is set).
        template_string: Inline template (optional; wins over template_path when both set).
        variables: Optional dict merged into the template context (host.name, host.data, etc.).
        encoding: File encoding for template_path (default 'utf-8').

    Dry-run does not open a connection.
    """
    if task.is_dry_run():
        return _dry_run_skipped(task, "would render template and push configuration")
    p = _params(task)
    inline = p.get("template_string")
    path_raw = p.get("template_path")
    variables = p.get("variables")
    if not isinstance(variables, dict):
        variables = {}
    encoding = p.get("encoding") or "utf-8"

    if inline is not None and str(inline).strip():
        tmpl_body = str(inline)
    elif path_raw is not None and str(path_raw).strip():
        path = Path(os.path.expanduser(str(path_raw).strip())).resolve()
        if not path.is_file():
            msg = f"template_path is not a file: {path}"
            return _result_failed(task, FileNotFoundError(msg))
        tmpl_body = path.read_text(encoding=encoding)
    else:
        msg = 'Provide "template_string" or "template_path".'
        return _result_failed(task, ValueError(msg))

    env = Environment(undefined=StrictUndefined, autoescape=False)
    template = env.from_string(tmpl_body)
    ctx = _flatten_template_context(task.host, variables)
    rendered = template.render(**ctx)
    node = _node_for_task(task)
    out = node.config(rendered)
    return _result_ok(task, out, changed=True)


@_eos_task
def configure_replace(task: Task) -> Result:
    """Replace running-config with contents from a file or URL the device can read.

    Params:
        path: Location the switch can read (for example 'flash:myconfig.cfg'). Passed to
            'configure replace <path>'.

    Dry-run does not open a connection.
    """
    if task.is_dry_run():
        return _dry_run_skipped(task, "would run configure replace")
    p = _params(task)
    path = p.get("path")
    if path is None or not str(path).strip():
        msg = 'Missing required task param "path".'
        return _result_failed(task, ValueError(msg))
    target = str(path).strip()
    node = _node_for_task(task)
    out = node.run_commands([f"configure replace {target}"], encoding="text")
    return _result_ok(task, out, changed=True)


@_eos_task
def create_checkpoint(task: Task) -> Result:
    """Save running-config to a checkpoint file on flash.

    Params:
        name: Checkpoint basename (required). Written to 'flash:checkpoint_<name>'.

    Dry-run does not open a connection.
    """
    if task.is_dry_run():
        return _dry_run_skipped(task, "would copy running-config to checkpoint on flash")
    p = _params(task)
    name = p.get("name")
    if name is None or not str(name).strip():
        msg = 'Missing required task param "name".'
        return _result_failed(task, ValueError(msg))
    safe = str(name).strip().replace(" ", "_")
    dest = f"flash:checkpoint_{safe}"
    node = _node_for_task(task)
    out = node.run_commands([f"copy running-config {dest}"], encoding="text")
    return _result_ok(task, {"destination": dest, "raw": out}, changed=True)


@_eos_task
def rollback(task: Task) -> Result:
    """Rollback the last configuration commit(s) ('configure rollback <n>').

    Params:
        steps: Number of commits to roll back (default 1).

    Dry-run does not open a connection.
    """
    if task.is_dry_run():
        return _dry_run_skipped(task, "would run configure rollback")
    p = _params(task)
    steps = p.get("steps", 1)
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
def copy_from_remote(task: Task) -> Result:
    """Tell the device to copy from a remote source into a local destination (pull).

    Runs a single 'copy' command in enable mode. Either pass 'command' as the full CLI line,
    or pass 'source' and 'destination' to build: 'copy <source> <destination>'.

    Params:
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
    p = _params(task)
    command = p.get("command")
    if command is not None and str(command).strip():
        cmd = str(command).strip()
    else:
        source = p.get("source")
        destination = p.get("destination")
        if source is None or destination is None:
            msg = 'Provide "command" or both "source" and "destination".'
            return _result_failed(task, ValueError(msg))
        cmd = f"copy {source} {destination}"
    node = _node_for_task(task)
    out = node.enable(cmd)
    return _result_ok(task, out, changed=True)