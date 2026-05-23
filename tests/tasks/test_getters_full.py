"""Tests for getter tasks not covered by the existing test files."""

from unittest.mock import MagicMock, patch

import pytest

from nornflow_arista.tasks import getters
from tests.conftest import run_task_like_nornir


# --------------------------------------------------------------------------- #
# Simple _eos_getter tasks (parametrized over command strings)                  #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("fn,expected_cmd", [
    (getters.get_interfaces, "show interfaces"),
    (getters.get_interfaces_status, "show interfaces status"),
    (getters.get_ip_interface_brief, "show ip interface brief"),
    (getters.get_interface_counters, "show interfaces counters errors"),
    (getters.get_bgp_summary, "show ip bgp summary"),
    (getters.get_bgp_neighbors_detail, "show ip bgp neighbors"),
    (getters.get_ospf_neighbors, "show ip ospf neighbor"),
    (getters.get_vxlan_vteps, "show vxlan vtep"),
    (getters.get_hardware_capacity, "show hardware capacity"),
    (getters.get_transceiver_info, "show interfaces transceiver"),
    (getters.get_reload_cause, "show reload cause"),
    (getters.dir_flash, "dir flash:"),
    (getters.show_filesystem, "show filesystem"),
    (getters.show_inventory, "show inventory"),
])
def test_simple_getter_calls_enable(make_task, fn, expected_cmd) -> None:
    """Each simple getter calls node.enable with exactly one command."""
    with patch("nornflow_arista.tasks.decorators._node_for_task") as mock_nft:
        node = MagicMock()
        node.enable.return_value = {}
        mock_nft.return_value = node
        task = make_task()
        result = run_task_like_nornir(fn, task)
    assert not result.failed
    node.enable.assert_called_once_with(expected_cmd)


# --------------------------------------------------------------------------- #
# get_mlag_status — two enable calls, result combined into dict                 #
# --------------------------------------------------------------------------- #

@patch("nornflow_arista.tasks.decorators._node_for_task")
def test_get_mlag_status_calls_enable_twice(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    node.enable.side_effect = [{"mlag": "data"}, {"sanity": "data"}]
    mock_nft.return_value = node
    task = make_task()
    result = run_task_like_nornir(getters.get_mlag_status, task)
    assert not result.failed
    assert result.result == {
        "mlag": {"mlag": "data"},
        "mlag_config_sanity": {"sanity": "data"},
    }
    assert node.enable.call_count == 2
    node.enable.assert_any_call("show mlag")
    node.enable.assert_any_call("show mlag config-sanity")


# --------------------------------------------------------------------------- #
# get_ip_route — additional argument combinations                               #
# --------------------------------------------------------------------------- #

@patch("nornflow_arista.tasks.getters._node_for_task")
def test_get_ip_route_no_args(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    mock_nft.return_value = node
    task = make_task()
    result = run_task_like_nornir(getters.get_ip_route, task)
    assert not result.failed
    node.enable.assert_called_once_with("show ip route")


@patch("nornflow_arista.tasks.getters._node_for_task")
def test_get_ip_route_with_prefix_only(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    mock_nft.return_value = node
    task = make_task(prefix="10.0.0.0/8")
    result = run_task_like_nornir(getters.get_ip_route, task)
    assert not result.failed
    node.enable.assert_called_once_with("show ip route 10.0.0.0/8")


@patch("nornflow_arista.tasks.getters._node_for_task")
def test_get_ip_route_with_vrf_and_prefix(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    mock_nft.return_value = node
    task = make_task(vrf="MGMT", prefix="192.168.0.0/24")
    result = run_task_like_nornir(getters.get_ip_route, task)
    assert not result.failed
    node.enable.assert_called_once_with("show ip route vrf MGMT 192.168.0.0/24")


# --------------------------------------------------------------------------- #
# get_startup_config                                                            #
# --------------------------------------------------------------------------- #

@patch("nornflow_arista.tasks.getters._node_for_task")
def test_get_startup_config(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    node.get_config.return_value = "hostname leaf01"
    mock_nft.return_value = node
    task = make_task()
    result = run_task_like_nornir(getters.get_startup_config, task)
    assert not result.failed
    assert result.result == "hostname leaf01"
    node.get_config.assert_called_once_with("startup-config", as_string=True)


# --------------------------------------------------------------------------- #
# run_commands                                                                  #
# --------------------------------------------------------------------------- #

@patch("nornflow_arista.tasks.getters._node_for_task")
def test_run_commands_string(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    node.enable.return_value = {}
    mock_nft.return_value = node
    task = make_task(commands="show version")
    result = run_task_like_nornir(getters.run_commands, task)
    assert not result.failed
    node.enable.assert_called_once_with("show version")


@patch("nornflow_arista.tasks.getters._node_for_task")
def test_run_commands_list(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    node.enable.return_value = [{"output": "ok"}]
    mock_nft.return_value = node
    task = make_task(commands=["show version", "show ip int brief"])
    result = run_task_like_nornir(getters.run_commands, task)
    assert not result.failed
    node.enable.assert_called_once_with(["show version", "show ip int brief"])


# --------------------------------------------------------------------------- #
# dir_path                                                                      #
# --------------------------------------------------------------------------- #

@patch("nornflow_arista.tasks.getters._node_for_task")
def test_dir_path_default_is_flash(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    node.enable.return_value = {}
    mock_nft.return_value = node
    task = make_task()
    result = run_task_like_nornir(getters.dir_path, task)
    assert not result.failed
    node.enable.assert_called_once_with("dir flash:")


@patch("nornflow_arista.tasks.getters._node_for_task")
def test_dir_path_custom(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    node.enable.return_value = {}
    mock_nft.return_value = node
    task = make_task(path="usb1:")
    result = run_task_like_nornir(getters.dir_path, task)
    assert not result.failed
    node.enable.assert_called_once_with("dir usb1:")


@patch("nornflow_arista.tasks.getters._node_for_task")
def test_dir_path_empty_falls_back_to_flash(mock_nft: MagicMock, make_task) -> None:
    node = MagicMock()
    node.enable.return_value = {}
    mock_nft.return_value = node
    task = make_task(path="")
    result = run_task_like_nornir(getters.dir_path, task)
    assert not result.failed
    node.enable.assert_called_once_with("dir flash:")
