"""Tests for connect_kwargs_from_open and ensure_pyeapi_connection."""

from unittest.mock import MagicMock, patch

import pytest
from pyeapi.client import Node

from nornflow_arista.eos_api.connect import connect_kwargs_from_open, ensure_pyeapi_connection
from nornflow_arista.eos_api.constants import (
    DATA_KEY_CA_FILE,
    PYEAPI_CONNECTION_NAME,
)
from nornflow_arista.eos_api.exceptions import EapiConfigError


# --------------------------------------------------------------------------- #
# connect_kwargs_from_open                                                      #
# --------------------------------------------------------------------------- #

def test_connect_kwargs_from_open_basic() -> None:
    """Standard inventory values produce a well-formed kwargs dict."""
    kwargs = connect_kwargs_from_open(
        host_label="sw1",
        hostname="10.0.0.1",
        username="admin",
        password="secret",
        port=443,
        extras={"eapi_transport": "https"},
    )
    assert kwargs == {
        "transport": "https",
        "host": "10.0.0.1",
        "username": "admin",
        "password": "secret",
        "port": 443,
        "timeout": 60,
    }


def test_connect_kwargs_from_open_extras_none_uses_defaults() -> None:
    """extras=None is treated as empty dict; defaults apply."""
    kwargs = connect_kwargs_from_open(
        host_label="sw1",
        hostname="10.0.0.1",
        username="admin",
        password="secret",
        port=None,
        extras=None,
    )
    assert kwargs["host"] == "10.0.0.1"
    assert kwargs["transport"] == "https"
    assert kwargs["port"] is None
    assert kwargs["timeout"] == 60


def test_connect_kwargs_from_open_optional_tls_from_extras() -> None:
    """TLS file paths passed via extras are included in the result."""
    kwargs = connect_kwargs_from_open(
        host_label="sw1",
        hostname="10.0.0.1",
        username="admin",
        password="secret",
        port=None,
        extras={DATA_KEY_CA_FILE: "/etc/ssl/ca.pem"},
    )
    assert kwargs["ca_file"] == "/etc/ssl/ca.pem"


def test_connect_kwargs_from_open_missing_hostname_raises() -> None:
    with pytest.raises(EapiConfigError, match="hostname"):
        connect_kwargs_from_open(
            host_label="sw_no_ip",
            hostname=None,
            username="admin",
            password="secret",
            port=None,
            extras=None,
        )


def test_connect_kwargs_from_open_missing_credentials_raises() -> None:
    with pytest.raises(EapiConfigError):
        connect_kwargs_from_open(
            host_label="sw1",
            hostname="10.0.0.1",
            username=None,
            password=None,
            port=None,
            extras=None,
        )


# --------------------------------------------------------------------------- #
# ensure_pyeapi_connection                                                      #
# --------------------------------------------------------------------------- #

def _mock_host(already_connected: bool = False) -> MagicMock:
    """Build a host mock that mimics the subset of nornir.Host used by ensure_pyeapi_connection."""
    host = MagicMock()
    host.connections = {PYEAPI_CONNECTION_NAME: MagicMock()} if already_connected else {}
    params = MagicMock()
    params.hostname = "10.0.0.1"
    params.username = "admin"
    params.password = "secret"
    params.port = 443
    params.platform = None
    params.extras = None
    host.get_connection_parameters.return_value = params
    return host


def test_ensure_pyeapi_connection_opens_when_not_cached() -> None:
    host = _mock_host(already_connected=False)
    config = MagicMock()
    sentinel = MagicMock(spec=Node)
    host.get_connection.return_value = sentinel

    result = ensure_pyeapi_connection(host, config)

    host.open_connection.assert_called_once()
    assert result is sentinel


def test_ensure_pyeapi_connection_reuses_cached_connection() -> None:
    host = _mock_host(already_connected=True)
    config = MagicMock()
    sentinel = MagicMock(spec=Node)
    host.get_connection.return_value = sentinel

    result = ensure_pyeapi_connection(host, config)

    host.open_connection.assert_not_called()
    assert result is sentinel


def test_ensure_pyeapi_connection_wrong_type_raises() -> None:
    host = _mock_host(already_connected=False)
    config = MagicMock()
    host.get_connection.return_value = "not-a-node"

    with pytest.raises(TypeError, match="Node"):
        ensure_pyeapi_connection(host, config)


def test_ensure_pyeapi_connection_open_call_includes_merged_extras() -> None:
    """open_connection is called with the merged host data as extras."""
    host = _mock_host(already_connected=False)
    host.data = {"eapi_transport": "https"}
    config = MagicMock()
    sentinel = MagicMock(spec=Node)
    host.get_connection.return_value = sentinel

    ensure_pyeapi_connection(host, config)

    call_kwargs = host.open_connection.call_args.kwargs
    assert call_kwargs["connection"] == PYEAPI_CONNECTION_NAME
    assert call_kwargs["default_to_host_attributes"] is True
