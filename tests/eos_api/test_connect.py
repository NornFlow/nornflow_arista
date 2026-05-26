"""Tests for eos_api.connect (kwargs assembly, no real sockets)."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from nornir.core.inventory import ConnectionOptions, Host
from pyeapi.client import Node

from nornflow_arista.eos_api.connect import connect_kwargs_from_host, node_from_host
from nornflow_arista.eos_api.constants import DATA_KEY_CA_FILE, ENV_EAPI_KEY_FILE
from nornflow_arista.eos_api.exceptions import EapiConfigError


def _host_with_extras(**extras: object) -> Host:
    return Host(
        name="sw1",
        hostname="10.0.0.1",
        username="admin",
        password="secret",
        data={
            "eapi_transport": "https",
            "eapi_port": 443,
            "eapi_timeout": 30,
        },
        connection_options={
            "pyeapi": ConnectionOptions(extras=extras),
        },
    )


def test_connect_kwargs_from_host_inventory(eos_host: Host) -> None:
    """Required connect fields are assembled from inventory."""
    kwargs = connect_kwargs_from_host(eos_host)
    assert kwargs == {
        "transport": "https",
        "host": "10.0.0.1",
        "username": "admin",
        "password": "secret",
        "port": 443,
        "timeout": 90,
    }


def test_connect_kwargs_from_host_uses_connection_options_extras() -> None:
    host = _host_with_extras(eapi_port=8080, eapi_transport="http")

    kwargs = connect_kwargs_from_host(host)

    assert kwargs["port"] == 8080
    assert kwargs["transport"] == "http"
    assert kwargs["timeout"] == 30


def test_connect_kwargs_from_host_without_extras_uses_host_data() -> None:
    host = Host(
        name="sw1",
        hostname="10.0.0.1",
        username="admin",
        password="secret",
        data={"eapi_transport": "https", "eapi_port": 443},
    )

    kwargs = connect_kwargs_from_host(host)

    assert kwargs["port"] == 443
    assert kwargs["transport"] == "https"


def test_connect_kwargs_optional_tls_files(
    eos_host: Host,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Optional key/cert/ca paths are included when set."""
    eos_host.data[DATA_KEY_CA_FILE] = "/etc/ssl/ca.pem"
    monkeypatch.setenv(ENV_EAPI_KEY_FILE, "/etc/ssl/key.pem")
    kwargs = connect_kwargs_from_host(eos_host)
    assert kwargs["ca_file"] == "/etc/ssl/ca.pem"
    assert kwargs["key_file"] == "/etc/ssl/key.pem"


def test_connect_kwargs_missing_credentials_raises() -> None:
    """Incomplete inventory cannot build connect kwargs."""
    host = Host(name="bad", hostname="1.1.1.1", username="", password=None)
    with pytest.raises(EapiConfigError):
        connect_kwargs_from_host(host)


@patch("nornflow_arista.eos_api.connect.pyeapi.connect")
def test_node_from_host_returns_node(
    mock_connect: MagicMock,
    eos_host: Host,
) -> None:
    """node_from_host delegates to pyeapi.connect with return_node=True."""
    sentinel = MagicMock(spec=Node)
    mock_connect.return_value = sentinel
    node = node_from_host(eos_host, context="custom")
    mock_connect.assert_called_once()
    call_kwargs: dict[str, Any] = mock_connect.call_args.kwargs
    assert call_kwargs["return_node"] is True
    assert call_kwargs["host"] == "10.0.0.1"
    assert call_kwargs["context"] == "custom"
    assert node is sentinel


@patch("nornflow_arista.eos_api.connect.pyeapi.connect")
def test_node_from_host_wrong_return_type_raises(
    mock_connect: MagicMock,
    eos_host: Host,
) -> None:
    """Non-Node return from connect raises TypeError."""
    mock_connect.return_value = "not-a-node"
    with pytest.raises(TypeError, match="Node"):
        node_from_host(eos_host)
