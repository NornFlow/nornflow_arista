"""Tests for eos_api.connect."""

from nornir.core.inventory import ConnectionOptions, Host

from nornflow_arista.eos_api.connect import connect_kwargs_from_host


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
