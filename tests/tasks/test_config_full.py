"""Tests for config.py tasks not covered by the existing test files."""

from unittest.mock import MagicMock, patch

import pytest
from pyeapi.eapilib import CommandError

from nornflow_arista.tasks import config
from tests.conftest import run_task_like_nornir


# --------------------------------------------------------------------------- #
# configure_session                                                             #
# --------------------------------------------------------------------------- #

@patch("nornflow_arista.tasks.config._node_for_task")
def test_configure_session_commit_happy_path(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    node.diff.return_value = "--- a\n+++ b\n"
    mock_nft.return_value = node
    task = make_task(commands="hostname spine1")
    result = run_task_like_nornir(config.configure_session, task)
    assert not result.failed
    assert result.changed is True
    assert result.result["committed"] is True
    assert "diff" in result.result
    node.configure_session.assert_called_once()
    node.commit.assert_called_once()


@patch("nornflow_arista.tasks.config._node_for_task")
def test_configure_session_abort_path(mock_nft: MagicMock, make_task) -> None:
    """commit=False runs abort; changed=False."""
    node = MagicMock()
    mock_nft.return_value = node
    task = make_task(commands="hostname spine1", commit=False, include_diff=False)
    result = run_task_like_nornir(config.configure_session, task)
    assert not result.failed
    assert result.changed is False
    assert result.result["committed"] is False
    node.abort.assert_called_once()


@patch("nornflow_arista.tasks.config._node_for_task")
def test_configure_session_sets_session_name(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    mock_nft.return_value = node
    task = make_task(commands="!", session_name="my_session")
    run_task_like_nornir(config.configure_session, task)
    assert node._session_name == "my_session"


@patch("nornflow_arista.tasks.config._node_for_task")
def test_configure_session_aborts_on_command_error(mock_nft: MagicMock, make_task) -> None:
    """node.config raising CommandError triggers abort and a failed result."""
    node = MagicMock()
    node.config.side_effect = CommandError(1000, "invalid command")
    mock_nft.return_value = node
    task = make_task(commands="bad command")
    result = run_task_like_nornir(config.configure_session, task)
    assert result.failed
    node.abort.assert_called_once()


@patch("nornflow_arista.tasks.config._node_for_task")
def test_configure_session_reraises_original_error_when_abort_fails(
    mock_nft: MagicMock, make_task
) -> None:
    """Cleanup abort failures must not mask the error that triggered them."""
    original = CommandError(1000, "invalid command")
    node = MagicMock()
    node.config.side_effect = original
    node.abort.side_effect = RuntimeError("abort transport failed")
    mock_nft.return_value = node
    task = make_task(commands="bad command")
    result = run_task_like_nornir(config.configure_session, task)
    assert result.failed
    assert result.exception is original
    node.abort.assert_called_once()


def test_configure_session_dry_run(make_task) -> None:
    task = make_task(_test_dry_run=True, commands="!")
    result = run_task_like_nornir(config.configure_session, task)
    assert not result.failed
    assert result.result["dry_run"] is True


# --------------------------------------------------------------------------- #
# commit_session                                                                #
# --------------------------------------------------------------------------- #

def test_commit_session_dry_run(make_task) -> None:
    task = make_task(_test_dry_run=True, session_name="s1")
    result = run_task_like_nornir(config.commit_session, task)
    assert not result.failed
    assert result.result["dry_run"] is True


def test_commit_session_empty_name_fails(make_task) -> None:
    task = make_task(session_name="  ")
    result = run_task_like_nornir(config.commit_session, task)
    assert result.failed


@patch("nornflow_arista.tasks.config._node_for_task")
def test_commit_session_runs_correct_commands(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    node.run_commands.return_value = [{"output": ""}]
    mock_nft.return_value = node
    task = make_task(session_name="my_session")
    result = run_task_like_nornir(config.commit_session, task)
    assert not result.failed
    node.run_commands.assert_called_once_with(
        ["configure session my_session", "commit"], encoding="text"
    )


# --------------------------------------------------------------------------- #
# abort_session                                                                 #
# --------------------------------------------------------------------------- #

def test_abort_session_dry_run(make_task) -> None:
    task = make_task(_test_dry_run=True, session_name="s1")
    result = run_task_like_nornir(config.abort_session, task)
    assert not result.failed
    assert result.result["dry_run"] is True


def test_abort_session_empty_name_fails(make_task) -> None:
    task = make_task(session_name="")
    result = run_task_like_nornir(config.abort_session, task)
    assert result.failed


@patch("nornflow_arista.tasks.config._node_for_task")
def test_abort_session_runs_correct_commands(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    node.run_commands.return_value = [{"output": ""}]
    mock_nft.return_value = node
    task = make_task(session_name="bad_session")
    result = run_task_like_nornir(config.abort_session, task)
    assert not result.failed
    node.run_commands.assert_called_once_with(
        ["configure session bad_session", "abort"], encoding="text"
    )


# --------------------------------------------------------------------------- #
# configure_from_template                                                       #
# --------------------------------------------------------------------------- #

def test_configure_from_template_dry_run(make_task) -> None:
    task = make_task(_test_dry_run=True, template_string="hostname leaf01")
    result = run_task_like_nornir(config.configure_from_template, task)
    assert not result.failed
    assert result.result["dry_run"] is True


@patch("nornflow_arista.tasks.config._node_for_task")
def test_configure_from_template_with_string(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    node.config.return_value = []
    mock_nft.return_value = node
    task = make_task(template_string="hostname leaf01", variables={})
    result = run_task_like_nornir(config.configure_from_template, task)
    assert not result.failed
    assert result.changed is True
    node.config.assert_called_once_with("hostname leaf01")


@patch("nornflow_arista.tasks.config._node_for_task")
def test_configure_from_template_renders_variables(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    node.config.return_value = []
    mock_nft.return_value = node
    task = make_task(
        template_string="hostname {{ device_name }}",
        variables={"device_name": "spine1"},
    )
    result = run_task_like_nornir(config.configure_from_template, task)
    assert not result.failed
    node.config.assert_called_once_with("hostname spine1")


@patch("nornflow_arista.tasks.config._node_for_task")
def test_configure_from_template_with_file(mock_nft: MagicMock, make_task, tmp_path) -> None:
    tfile = tmp_path / "cfg.j2"
    tfile.write_text("hostname leaf01", encoding="utf-8")
    node = MagicMock()
    node.config.return_value = []
    mock_nft.return_value = node
    task = make_task(template_path=str(tfile))
    result = run_task_like_nornir(config.configure_from_template, task)
    assert not result.failed
    node.config.assert_called_once_with("hostname leaf01")


def test_configure_from_template_missing_file_fails(make_task) -> None:
    task = make_task(template_path="/nonexistent/path/template.j2")
    result = run_task_like_nornir(config.configure_from_template, task)
    assert result.failed
    assert isinstance(result.exception, FileNotFoundError)


def test_configure_from_template_no_source_fails(make_task) -> None:
    task = make_task()
    result = run_task_like_nornir(config.configure_from_template, task)
    assert result.failed
    assert isinstance(result.exception, ValueError)


# --------------------------------------------------------------------------- #
# safe_configure_from_template                                                  #
# --------------------------------------------------------------------------- #


def test_safe_configure_from_template_dry_run(make_task) -> None:
    task = make_task(
        _test_dry_run=True,
        checkpoint_name="pre_change",
        template_string="hostname leaf01",
    )
    result = run_task_like_nornir(config.safe_configure_from_template, task)
    assert not result.failed
    assert result.result["dry_run"] is True


def test_safe_configure_from_template_empty_checkpoint_name_fails(make_task) -> None:
    task = make_task(checkpoint_name="  ", template_string="hostname leaf01")
    result = run_task_like_nornir(config.safe_configure_from_template, task)
    assert result.failed


@patch("nornflow_arista.tasks.config._node_for_task")
def test_safe_configure_from_template_happy_path(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    node.run_commands.return_value = [{"output": ""}]
    node.config.return_value = []
    mock_nft.return_value = node
    task = make_task(checkpoint_name="pre_change", template_string="hostname leaf01")
    result = run_task_like_nornir(config.safe_configure_from_template, task)
    assert not result.failed
    assert result.changed is True
    assert result.result["destination"] == "flash:checkpoint_pre_change"
    node.run_commands.assert_called_once_with(
        ["copy running-config flash:checkpoint_pre_change"], encoding="text"
    )
    node.config.assert_called_once_with("hostname leaf01")


@patch("nornflow_arista.tasks.config._node_for_task")
def test_safe_configure_from_template_rollback_on_apply_failure(
    mock_nft: MagicMock, make_task
) -> None:
    node = MagicMock()
    node.run_commands.return_value = [{"output": ""}]
    node.config.side_effect = CommandError(1000, "invalid command")
    mock_nft.return_value = node
    task = make_task(checkpoint_name="pre_change", template_string="bad command")
    result = run_task_like_nornir(config.safe_configure_from_template, task)
    assert result.failed
    assert isinstance(result.exception, CommandError)
    assert node.run_commands.call_count == 2
    node.run_commands.assert_any_call(
        ["copy running-config flash:checkpoint_pre_change"], encoding="text"
    )
    node.run_commands.assert_any_call(
        ["configure replace flash:checkpoint_pre_change"], encoding="text"
    )


@patch("nornflow_arista.tasks.config._node_for_task")
def test_safe_configure_from_template_reraises_original_error_when_rollback_fails(
    mock_nft: MagicMock, make_task
) -> None:
    original = CommandError(1000, "invalid command")
    node = MagicMock()
    node.run_commands.side_effect = [[{"output": ""}], RuntimeError("replace failed")]
    node.config.side_effect = original
    mock_nft.return_value = node
    task = make_task(checkpoint_name="pre_change", template_string="bad command")
    result = run_task_like_nornir(config.safe_configure_from_template, task)
    assert result.failed
    assert result.exception is original


@patch("nornflow_arista.tasks.config._node_for_task")
def test_safe_configure_from_template_template_error_skips_rollback(
    mock_nft: MagicMock, make_task
) -> None:
    task = make_task(checkpoint_name="pre_change", template_path="/nonexistent/template.j2")
    result = run_task_like_nornir(config.safe_configure_from_template, task)
    assert result.failed
    assert isinstance(result.exception, FileNotFoundError)
    mock_nft.assert_not_called()


@pytest.mark.parametrize("bad_name", ["foo/bar", "bad;name", "has\nnewline"])
def test_safe_configure_from_template_rejects_unsafe_checkpoint_name(
    make_task, bad_name: str
) -> None:
    task = make_task(checkpoint_name=bad_name, template_string="hostname leaf01")
    result = run_task_like_nornir(config.safe_configure_from_template, task)
    assert result.failed
    assert isinstance(result.exception, ValueError)


# --------------------------------------------------------------------------- #
# configure_replace                                                             #
# --------------------------------------------------------------------------- #

def test_configure_replace_dry_run(make_task) -> None:
    task = make_task(_test_dry_run=True, path="flash:backup.cfg")
    result = run_task_like_nornir(config.configure_replace, task)
    assert not result.failed
    assert result.result["dry_run"] is True


def test_configure_replace_empty_path_fails(make_task) -> None:
    task = make_task(path="  ")
    result = run_task_like_nornir(config.configure_replace, task)
    assert result.failed


@patch("nornflow_arista.tasks.config._node_for_task")
def test_configure_replace_happy_path(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    node.run_commands.return_value = [{"output": ""}]
    mock_nft.return_value = node
    task = make_task(path="flash:backup.cfg")
    result = run_task_like_nornir(config.configure_replace, task)
    assert not result.failed
    assert result.changed is True
    node.run_commands.assert_called_once_with(
        ["configure replace flash:backup.cfg"], encoding="text"
    )


# --------------------------------------------------------------------------- #
# create_checkpoint                                                             #
# --------------------------------------------------------------------------- #

def test_create_checkpoint_dry_run(make_task) -> None:
    # 'name' conflicts with Nornir Task's own 'name' kwarg; set via params directly.
    task = make_task(_test_dry_run=True)
    task.params["name"] = "pre_change"
    result = run_task_like_nornir(config.create_checkpoint, task)
    assert not result.failed
    assert result.result["dry_run"] is True


def test_create_checkpoint_empty_name_fails(make_task) -> None:
    task = make_task()
    task.params["name"] = ""
    result = run_task_like_nornir(config.create_checkpoint, task)
    assert result.failed


@patch("nornflow_arista.tasks.config._node_for_task")
def test_create_checkpoint_builds_destination(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    node.run_commands.return_value = [{"output": ""}]
    mock_nft.return_value = node
    task = make_task()
    task.params["name"] = "pre change 001"
    result = run_task_like_nornir(config.create_checkpoint, task)
    assert not result.failed
    assert result.changed is True
    assert result.result["destination"] == "flash:checkpoint_pre_change_001"
    node.run_commands.assert_called_once_with(
        ["copy running-config flash:checkpoint_pre_change_001"], encoding="text"
    )


@patch("nornflow_arista.tasks.config._node_for_task")
def test_create_checkpoint_replaces_spaces_in_name(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    node.run_commands.return_value = [{"output": ""}]
    mock_nft.return_value = node
    task = make_task()
    task.params["name"] = "my checkpoint"
    result = run_task_like_nornir(config.create_checkpoint, task)
    assert result.result["destination"] == "flash:checkpoint_my_checkpoint"


@pytest.mark.parametrize("bad_name", ["foo/bar", "bad;name", "has\nnewline"])
def test_create_checkpoint_rejects_unsafe_name(make_task, bad_name: str) -> None:
    task = make_task()
    task.params["name"] = bad_name
    result = run_task_like_nornir(config.create_checkpoint, task)
    assert result.failed
    assert isinstance(result.exception, ValueError)


# --------------------------------------------------------------------------- #
# rollback                                                                      #
# --------------------------------------------------------------------------- #

def test_rollback_dry_run(make_task) -> None:
    task = make_task(_test_dry_run=True, steps=1)
    result = run_task_like_nornir(config.rollback, task)
    assert not result.failed
    assert result.result["dry_run"] is True


def test_rollback_non_int_steps_fails(make_task) -> None:
    task = make_task(steps="many")
    result = run_task_like_nornir(config.rollback, task)
    assert result.failed


def test_rollback_zero_steps_fails(make_task) -> None:
    task = make_task(steps=0)
    result = run_task_like_nornir(config.rollback, task)
    assert result.failed


def test_rollback_negative_steps_fails(make_task) -> None:
    task = make_task(steps=-1)
    result = run_task_like_nornir(config.rollback, task)
    assert result.failed


@patch("nornflow_arista.tasks.config._node_for_task")
def test_rollback_happy_path(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    node.run_commands.return_value = [{"output": ""}]
    mock_nft.return_value = node
    task = make_task(steps=2)
    result = run_task_like_nornir(config.rollback, task)
    assert not result.failed
    assert result.changed is True
    node.run_commands.assert_called_once_with(["configure rollback 2"], encoding="text")


@patch("nornflow_arista.tasks.config._node_for_task")
def test_rollback_default_steps_is_one(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    node.run_commands.return_value = [{"output": ""}]
    mock_nft.return_value = node
    task = make_task()
    result = run_task_like_nornir(config.rollback, task)
    assert not result.failed
    node.run_commands.assert_called_once_with(["configure rollback 1"], encoding="text")


# --------------------------------------------------------------------------- #
# copy_from_remote                                                              #
# --------------------------------------------------------------------------- #

def test_copy_from_remote_dry_run(make_task) -> None:
    task = make_task(_test_dry_run=True, command="copy tftp://1.1.1.1/cfg.txt flash:")
    result = run_task_like_nornir(config.copy_from_remote, task)
    assert not result.failed
    assert result.result["dry_run"] is True


def test_copy_from_remote_no_args_fails(make_task) -> None:
    task = make_task()
    result = run_task_like_nornir(config.copy_from_remote, task)
    assert result.failed


def test_copy_from_remote_source_only_fails(make_task) -> None:
    task = make_task(source="tftp://1.1.1.1/cfg.txt")
    result = run_task_like_nornir(config.copy_from_remote, task)
    assert result.failed


@patch("nornflow_arista.tasks.config._node_for_task")
def test_copy_from_remote_full_command(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    node.enable.return_value = {}
    mock_nft.return_value = node
    task = make_task(command="copy tftp://1.1.1.1/cfg.txt flash:cfg.txt")
    result = run_task_like_nornir(config.copy_from_remote, task)
    assert not result.failed
    assert result.changed is True
    node.enable.assert_called_once_with("copy tftp://1.1.1.1/cfg.txt flash:cfg.txt")


@patch("nornflow_arista.tasks.config._node_for_task")
def test_copy_from_remote_source_and_destination(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    node.enable.return_value = {}
    mock_nft.return_value = node
    task = make_task(source="tftp://1.1.1.1/cfg.txt", destination="flash:cfg.txt")
    result = run_task_like_nornir(config.copy_from_remote, task)
    assert not result.failed
    node.enable.assert_called_once_with("copy tftp://1.1.1.1/cfg.txt flash:cfg.txt")


# --------------------------------------------------------------------------- #
# save_config — live (non-dry-run) path                                         #
# --------------------------------------------------------------------------- #

@patch("nornflow_arista.tasks.config._node_for_task")
def test_save_config_calls_write_memory(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    node.enable.return_value = {}
    mock_nft.return_value = node
    task = make_task()
    result = run_task_like_nornir(config.save_config, task)
    assert not result.failed
    assert result.changed is True
    node.enable.assert_called_once_with("write memory")
