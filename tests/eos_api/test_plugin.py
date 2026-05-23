"""Tests for the Pyeapi Nornir connection plugin."""

from unittest.mock import MagicMock, patch

import pytest
from pyeapi.client import Node

from nornflow_arista.eos_api.plugin import Pyeapi


def _open_plugin(mock_connect: MagicMock, *, node: MagicMock | None = None) -> Pyeapi:
    """Helper: configure mock_connect and call plugin.open with minimal valid args."""
    if node is None:
        node = MagicMock(spec=Node)
    mock_connect.return_value = node
    plugin = Pyeapi()
    plugin.open(
        hostname="10.0.0.1",
        username="admin",
        password="secret",
        port=443,
        platform=None,
        extras={"eapi_transport": "https"},
    )
    return plugin


# --------------------------------------------------------------------------- #
# open                                                                          #
# --------------------------------------------------------------------------- #

@patch("nornflow_arista.eos_api.plugin.pyeapi.connect")
def test_pyeapi_open_stores_node(mock_connect: MagicMock) -> None:
    node = MagicMock(spec=Node)
    plugin = _open_plugin(mock_connect, node=node)
    assert plugin.connection is node


@patch("nornflow_arista.eos_api.plugin.pyeapi.connect")
def test_pyeapi_open_calls_connect_with_return_node(mock_connect: MagicMock) -> None:
    _open_plugin(mock_connect)
    call_kwargs = mock_connect.call_args.kwargs
    assert call_kwargs["return_node"] is True


@patch("nornflow_arista.eos_api.plugin.pyeapi.connect")
def test_pyeapi_open_wrong_return_type_raises(mock_connect: MagicMock) -> None:
    mock_connect.return_value = "not-a-node"
    plugin = Pyeapi()
    with pytest.raises(TypeError, match="Node"):
        plugin.open(
            hostname="10.0.0.1",
            username="admin",
            password="secret",
            port=None,
            platform=None,
        )


# --------------------------------------------------------------------------- #
# close                                                                         #
# --------------------------------------------------------------------------- #

def test_pyeapi_close_no_prior_open_is_noop() -> None:
    """close() before open() must not raise."""
    plugin = Pyeapi()
    plugin.close()


@patch("nornflow_arista.eos_api.plugin.pyeapi.connect")
def test_pyeapi_close_calls_transport_close(mock_connect: MagicMock) -> None:
    node = MagicMock(spec=Node)
    transport = MagicMock()
    node._connection = transport
    plugin = _open_plugin(mock_connect, node=node)

    plugin.close()

    transport.close.assert_called_once()
    assert plugin.connection is None


@patch("nornflow_arista.eos_api.plugin.pyeapi.connect")
def test_pyeapi_close_swallows_oserror(mock_connect: MagicMock) -> None:
    node = MagicMock(spec=Node)
    transport = MagicMock()
    transport.close.side_effect = OSError("connection reset")
    node._connection = transport
    plugin = _open_plugin(mock_connect, node=node)

    plugin.close()  # must not raise

    assert plugin.connection is None


@patch("nornflow_arista.eos_api.plugin.pyeapi.connect")
def test_pyeapi_close_node_without_transport_attr(mock_connect: MagicMock) -> None:
    """Node with no _connection attribute: close() completes without error."""
    node = MagicMock(spec=Node)
    del node._connection  # remove the attribute so getattr returns None
    mock_connect.return_value = node
    plugin = Pyeapi()
    plugin.open(
        hostname="10.0.0.1",
        username="admin",
        password="secret",
        port=None,
        platform=None,
        extras={"eapi_transport": "https"},
    )
    plugin.close()
    assert plugin.connection is None
