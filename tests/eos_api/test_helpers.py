"""Tests for eos_api.helpers (pure resolution logic)."""

import pytest
from nornir.core.inventory import Host

from nornflow_arista.eos_api import helpers
from nornflow_arista.eos_api.constants import (
    DATA_KEY_PASSWORD,
    DATA_KEY_PORT,
    DATA_KEY_TIMEOUT,
    DATA_KEY_TRANSPORT,
    DEFAULT_EAPI_TRANSPORT,
    ENV_EAPI_HOST,
    ENV_EAPI_TIMEOUT,
    ENV_EAPI_USERNAME,
)
from nornflow_arista.eos_api.exceptions import EapiConfigError


def test_resolve_hostname_from_inventory(eos_host: Host) -> None:
    """Hostname comes from host.hostname when set."""
    assert helpers.resolve_hostname(eos_host) == "10.0.0.1"


def test_resolve_hostname_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """ENV_EAPI_HOST is used when host.hostname is empty."""
    host = Host(name="sw2", hostname="", username="u", password="p")
    monkeypatch.setenv(ENV_EAPI_HOST, "203.0.113.1")
    assert helpers.resolve_hostname(host) == "203.0.113.1"


def test_resolve_hostname_missing_raises() -> None:
    """Missing hostname and env raises EapiConfigError."""
    host = Host(name="sw3", hostname="", username="u", password="p")
    with pytest.raises(EapiConfigError, match="hostname"):
        helpers.resolve_hostname(host)


def test_resolve_transport_default() -> None:
    """Empty data yields DEFAULT_EAPI_TRANSPORT."""
    assert helpers.resolve_transport({}) == DEFAULT_EAPI_TRANSPORT


def test_resolve_transport_from_data() -> None:
    """eapi_transport in host.data overrides default."""
    assert helpers.resolve_transport({DATA_KEY_TRANSPORT: "http"}) == "http"


def test_resolve_port_from_data(eos_host: Host) -> None:
    """eapi_port in data is coerced to int."""
    data = {DATA_KEY_PORT: "8443"}
    assert helpers.resolve_port(eos_host, data) == 8443


def test_resolve_username_from_host_fields(eos_host: Host) -> None:
    """host.username is used when data has no eapi_username."""
    assert helpers.resolve_username(eos_host, {}) == "admin"


def test_resolve_username_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """ENV_EAPI_USERNAME wins when host fields are empty."""
    host = Host(name="sw4", hostname="1.1.1.1", username="", password="p")
    monkeypatch.setenv(ENV_EAPI_USERNAME, "envuser")
    assert helpers.resolve_username(host, {}) == "envuser"


def test_resolve_password_allows_empty_string_in_data() -> None:
    """Explicit empty password in data is valid (not treated as missing)."""
    host = Host(name="sw5", hostname="1.1.1.1", username="u", password="ignored")
    data = {DATA_KEY_PASSWORD: ""}
    assert helpers.resolve_password(host, data) == ""


def test_resolve_password_from_host_password() -> None:
    """host.password is used when data key is absent."""
    host = Host(name="sw6", hostname="1.1.1.1", username="u", password="from_host")
    assert helpers.resolve_password(host, {}) == "from_host"


def test_resolve_password_missing_raises() -> None:
    """No password source raises EapiConfigError."""
    host = Host(name="sw7", hostname="1.1.1.1", username="u", password=None)
    with pytest.raises(EapiConfigError, match="password"):
        helpers.resolve_password(host, {})


def test_parse_positive_int_rejects_bool() -> None:
    """Booleans are not valid timeout/port values."""
    with pytest.raises(EapiConfigError, match="boolean"):
        helpers.parse_positive_int("eapi_timeout", True)


def test_optional_positive_int_from_data(eos_host: Host) -> None:
    """Timeout is read from host.data when present."""
    data = helpers.host_data(eos_host)
    assert helpers.optional_positive_int_from_data_env_default(
        data,
        DATA_KEY_TIMEOUT,
        ENV_EAPI_TIMEOUT,
        60,
    ) == 90


def test_host_data_non_dict_returns_empty() -> None:
    """Invalid host.data becomes an empty dict."""
    host = Host(name="x", hostname="h", username="u", password="p", data="bad")  # type: ignore[arg-type]
    assert helpers.host_data(host) == {}
