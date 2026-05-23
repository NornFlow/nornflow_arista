"""Additional tests for eos_api.helpers: low-level utilities and env fallback paths."""

import pytest
from nornir.core.inventory import ConnectionOptions, Host

from nornflow_arista.eos_api import helpers
from nornflow_arista.eos_api.constants import (
    DATA_KEY_PORT,
    DATA_KEY_TIMEOUT,
    DATA_KEY_USERNAME,
    ENV_EAPI_PASSWORD,
    ENV_EAPI_PORT,
    ENV_EAPI_TIMEOUT,
    ENV_EAPI_TRANSPORT,
    PYEAPI_CONNECTION_NAME,
)
from nornflow_arista.eos_api.exceptions import EapiConfigError


# --------------------------------------------------------------------------- #
# first_not_none                                                                #
# --------------------------------------------------------------------------- #

def test_first_not_none_returns_first_non_none() -> None:
    assert helpers.first_not_none(None, None, "found", "ignored") == "found"


def test_first_not_none_all_none_returns_none() -> None:
    assert helpers.first_not_none(None, None) is None


def test_first_not_none_falsy_non_none_returned() -> None:
    """0 and '' are not None, so they should be returned."""
    assert helpers.first_not_none(None, 0, "ignored") == 0


# --------------------------------------------------------------------------- #
# first_non_empty_str                                                           #
# --------------------------------------------------------------------------- #

def test_first_non_empty_str_skips_empty_and_blank() -> None:
    assert helpers.first_non_empty_str(None, "", "  ", "actual") == "actual"


def test_first_non_empty_str_all_empty_returns_none() -> None:
    assert helpers.first_non_empty_str(None, "", "  ") is None


def test_first_non_empty_str_returns_first_valid() -> None:
    assert helpers.first_non_empty_str("first", "second") == "first"


# --------------------------------------------------------------------------- #
# non_empty_str                                                                 #
# --------------------------------------------------------------------------- #

def test_non_empty_str_strips_whitespace() -> None:
    assert helpers.non_empty_str("  hello  ") == "hello"


def test_non_empty_str_blank_returns_none() -> None:
    assert helpers.non_empty_str("   ") is None


def test_non_empty_str_none_returns_none() -> None:
    assert helpers.non_empty_str(None) is None


def test_non_empty_str_coerces_non_string() -> None:
    assert helpers.non_empty_str(42) == "42"


# --------------------------------------------------------------------------- #
# coerce_port                                                                   #
# --------------------------------------------------------------------------- #

def test_coerce_port_none_returns_none() -> None:
    assert helpers.coerce_port(None) is None


def test_coerce_port_int_passthrough() -> None:
    assert helpers.coerce_port(8443) == 8443


def test_coerce_port_string_int_coerced() -> None:
    assert helpers.coerce_port("8443") == 8443


def test_coerce_port_blank_string_returns_none() -> None:
    assert helpers.coerce_port("") is None


def test_coerce_port_invalid_raises() -> None:
    with pytest.raises(EapiConfigError, match="integer"):
        helpers.coerce_port("notaport")


# --------------------------------------------------------------------------- #
# merged_eapi_data                                                              #
# --------------------------------------------------------------------------- #

def test_merged_eapi_data_returns_host_data_copy(eos_host: Host) -> None:
    result = helpers.merged_eapi_data(eos_host)
    assert result["eapi_transport"] == "https"
    assert result["eapi_timeout"] == 90


def test_merged_eapi_data_extras_override_host_data(eos_host: Host) -> None:
    """connection_options.pyeapi.extras override host.data for the same key."""
    eos_host.connection_options[PYEAPI_CONNECTION_NAME] = ConnectionOptions(
        extras={DATA_KEY_USERNAME: "override_user"},
    )
    result = helpers.merged_eapi_data(eos_host)
    assert result[DATA_KEY_USERNAME] == "override_user"


# --------------------------------------------------------------------------- #
# resolve_transport — env fallback                                              #
# --------------------------------------------------------------------------- #

def test_resolve_transport_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_EAPI_TRANSPORT, "http")
    assert helpers.resolve_transport({}) == "http"


def test_resolve_transport_data_beats_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_EAPI_TRANSPORT, "http")
    assert helpers.resolve_transport({"eapi_transport": "https"}) == "https"


# --------------------------------------------------------------------------- #
# resolve_port — env fallback                                                   #
# --------------------------------------------------------------------------- #

def test_resolve_port_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_EAPI_PORT, "8080")
    host = Host(name="x", hostname="1.1.1.1", username="u", password="p", port=None)
    assert helpers.resolve_port(host, {}) == 8080


# --------------------------------------------------------------------------- #
# resolve_password — env fallback                                               #
# --------------------------------------------------------------------------- #

def test_resolve_password_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_EAPI_PASSWORD, "envpass")
    host = Host(name="sw8", hostname="1.1.1.1", username="u", password=None)
    assert helpers.resolve_password(host, {}) == "envpass"


# --------------------------------------------------------------------------- #
# optional_str_from_data_or_env                                                 #
# --------------------------------------------------------------------------- #

def test_optional_str_from_data_or_env_data_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NORNFLOW_ARISTA_EAPI_KEY_FILE", "/env/key.pem")
    data = {"eapi_key_file": "/data/key.pem"}
    result = helpers.optional_str_from_data_or_env(data, "eapi_key_file", "NORNFLOW_ARISTA_EAPI_KEY_FILE")
    assert result == "/data/key.pem"


def test_optional_str_from_data_or_env_falls_back_to_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NORNFLOW_ARISTA_EAPI_KEY_FILE", "/env/key.pem")
    result = helpers.optional_str_from_data_or_env({}, "eapi_key_file", "NORNFLOW_ARISTA_EAPI_KEY_FILE")
    assert result == "/env/key.pem"


def test_optional_str_from_data_or_env_returns_none_when_absent() -> None:
    result = helpers.optional_str_from_data_or_env({}, "eapi_key_file", "NORNFLOW_ARISTA_EAPI_KEY_FILE_ABSENT")
    assert result is None


# --------------------------------------------------------------------------- #
# parse_positive_int — extra branches                                           #
# --------------------------------------------------------------------------- #

def test_parse_positive_int_from_string() -> None:
    assert helpers.parse_positive_int("eapi_timeout", "30") == 30


def test_parse_positive_int_zero_raises() -> None:
    with pytest.raises(EapiConfigError, match="positive"):
        helpers.parse_positive_int("eapi_timeout", 0)


def test_parse_positive_int_negative_raises() -> None:
    with pytest.raises(EapiConfigError, match="positive"):
        helpers.parse_positive_int("eapi_timeout", -5)


def test_parse_positive_int_non_numeric_string_raises() -> None:
    with pytest.raises(EapiConfigError, match="integer"):
        helpers.parse_positive_int("eapi_timeout", "fast")


def test_parse_positive_int_string_zero_raises() -> None:
    with pytest.raises(EapiConfigError, match="positive"):
        helpers.parse_positive_int("eapi_timeout", "0")


# --------------------------------------------------------------------------- #
# optional_positive_int_from_data_env_default — env path                       #
# --------------------------------------------------------------------------- #

def test_optional_positive_int_uses_env_when_data_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_EAPI_TIMEOUT, "120")
    result = helpers.optional_positive_int_from_data_env_default(
        {}, DATA_KEY_TIMEOUT, ENV_EAPI_TIMEOUT, 60
    )
    assert result == 120


def test_optional_positive_int_uses_default_when_nothing_set() -> None:
    result = helpers.optional_positive_int_from_data_env_default(
        {}, DATA_KEY_TIMEOUT, "NORNFLOW_ARISTA_NONEXISTENT_ENV_XYZ", 42
    )
    assert result == 42


def test_optional_positive_int_data_beats_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_EAPI_TIMEOUT, "120")
    result = helpers.optional_positive_int_from_data_env_default(
        {DATA_KEY_TIMEOUT: 30}, DATA_KEY_TIMEOUT, ENV_EAPI_TIMEOUT, 60
    )
    assert result == 30
