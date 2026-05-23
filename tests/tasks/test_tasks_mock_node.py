"""Task execution against a mocked pyeapi Node (no network)."""

from unittest.mock import MagicMock, patch

from nornflow_arista.tasks import config, getters
from tests.conftest import run_task_like_nornir


@patch("nornflow_arista.tasks.decorators._node_for_task")
def test_get_facts_runs_show_version(mock_node_for_task: MagicMock, make_task) -> None:
    """Read-only getter calls enable with the expected command."""
    node = MagicMock()
    node.enable.return_value = {"version": "4.28.0"}
    mock_node_for_task.return_value = node
    task = make_task()
    result = run_task_like_nornir(getters.get_facts, task)
    assert not result.failed
    assert result.result == {"version": "4.28.0"}
    node.enable.assert_called_once_with("show version")


@patch("nornflow_arista.tasks.config._node_for_task")
def test_configure_marks_result_changed(mock_node_for_task: MagicMock, make_task) -> None:
    """Mutating configure sets changed=True on success."""
    node = MagicMock()
    node.config.return_value = []
    mock_node_for_task.return_value = node
    task = make_task(commands="hostname test")
    result = run_task_like_nornir(config.configure, task)
    assert not result.failed
    assert result.changed is True
    node.config.assert_called_once_with("hostname test")
