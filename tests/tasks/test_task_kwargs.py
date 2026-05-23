"""Tests that workflow args reach tasks via **kwargs (Nornir calling convention)."""

from unittest.mock import MagicMock, patch

from nornflow_arista.tasks import config, getters
from tests.conftest import run_task_like_nornir


def test_save_config_accepts_no_args(make_task) -> None:
    """Parameterless task succeeds with empty args."""
    task = make_task(_test_dry_run=True)
    result = run_task_like_nornir(config.save_config, task)
    assert not result.failed


def test_save_config_rejects_unknown_arg(make_task) -> None:
    """Extra workflow args raise TypeError and become a failed Result."""
    task = make_task(foo=1)
    result = run_task_like_nornir(config.save_config, task)
    assert result.failed
    assert result.exception is not None
    assert "unexpected keyword" in str(result.exception).lower()


def test_configure_requires_commands(make_task) -> None:
    """Missing required 'commands' param fails the task."""
    task = make_task()
    result = run_task_like_nornir(config.configure, task)
    assert result.failed
    assert result.exception is not None
    assert "commands" in str(result.exception).lower()


@patch("nornflow_arista.tasks.config._node_for_task")
def test_configure_forwards_commands(
    mock_node_for_task: MagicMock,
    make_task,
) -> None:
    """commands from workflow args are passed to node.config."""
    node = MagicMock()
    node.config.return_value = [{"command": "ok"}]
    mock_node_for_task.return_value = node
    task = make_task(commands=["vlan 10", "name TEN"])
    result = run_task_like_nornir(config.configure, task)
    assert not result.failed
    node.config.assert_called_once_with(["vlan 10", "name TEN"])


def test_get_lldp_neighbors_default_detail(make_task) -> None:
    """Omitted detail uses default False."""
    with patch("nornflow_arista.tasks.getters._node_for_task") as mock_node:
        node = MagicMock()
        mock_node.return_value = node
        task = make_task()
        result = run_task_like_nornir(getters.get_lldp_neighbors, task)
        assert not result.failed
        node.enable.assert_called_once_with("show lldp neighbors")


def test_get_lldp_neighbors_detail_true(make_task) -> None:
    """detail=True selects the detail command."""
    with patch("nornflow_arista.tasks.getters._node_for_task") as mock_node:
        node = MagicMock()
        mock_node.return_value = node
        task = make_task(detail=True)
        result = run_task_like_nornir(getters.get_lldp_neighbors, task)
        node.enable.assert_called_once_with("show lldp neighbors detail")
