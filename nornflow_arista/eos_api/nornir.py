"""Map Nornir inventory hosts to Arista EOS eAPI ('pyeapi') connections.

This module bridges 'nornir.core.inventory.Host' objects to the keyword
arguments expected by 'pyeapi.connect'.

Typical usage:

    from nornflow_arista.eapi_client import node_from_host

    node = node_from_host(host)
    node.enable("show version")

See 'nornflow_arista.eapi_client.constants' for DATA_KEY_*, ENV_*, and DEFAULT_* names.
"""

import os
from typing import Any

import pyeapi
from nornir.core.inventory import Host
from pyeapi.client import Node

from nornflow_arista.eapi_client.constants import (
    DATA_KEY_CA_FILE,
    DATA_KEY_CERT_FILE,
    DATA_KEY_KEY_FILE,
    DATA_KEY_PASSWORD,
    DATA_KEY_PORT,
    DATA_KEY_TIMEOUT,
    DATA_KEY_TRANSPORT,
    DATA_KEY_USERNAME,
    DEFAULT_EAPI_TIMEOUT,
    DEFAULT_EAPI_TRANSPORT,
    ENV_EAPI_CA_FILE,
    ENV_EAPI_CERT_FILE,
    ENV_EAPI_HOST,
    ENV_EAPI_KEY_FILE,
    ENV_EAPI_PASSWORD,
    ENV_EAPI_PORT,
    ENV_EAPI_TIMEOUT,
    ENV_EAPI_TRANSPORT,
    ENV_EAPI_USERNAME,
)


class EapiConfigError(ValueError):
    """Raised when a Nornir host cannot be mapped to eAPI settings.

    Subclass of ValueError so callers may catch broadly with ValueError
    or narrowly with EapiConfigError.
    """


def _host_data(host: Host) -> dict[str, Any]:
    """Return the host's 'data' mapping, or an empty dict if missing or invalid.

    Args:
        host: Nornir host; 'data' is normally a dict of inventory extras.

    Returns:
        A shallow dict usable for 'eapi_*' lookups, or '{}' if 'data' is absent
        or not a dict.
    """
    raw = getattr(host, "data", None) or {}
    if not isinstance(raw, dict):
        return {}
    return raw


def _non_empty_str(value: object | None) -> str | None:
    """Normalize a value to a stripped non-empty string, or None.

    Args:
        value: Any object; None yields None.

    Returns:
        Stripped string if non-empty after stripping; otherwise None.
    """
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coerce_port(value: object | None) -> int | None:
    """Parse an optional TCP port from inventory, env, or Nornir 'port'.

    Args:
        value: Integer-like value, or None, or whitespace string.

    Returns:
        Integer port, or None if 'value' is None or blank after stripping.

    Raises:
        EapiConfigError: If the value is present but not a valid integer.
    """
    if value is None:
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError as exc:
        msg = f"eAPI port must be an integer, got {value!r}"
        raise EapiConfigError(msg) from exc


def _resolve_hostname(host: Host) -> str:
    """Resolve target host: 'host.hostname', then 'ENV_EAPI_HOST'.

    Args:
        host: Nornir host.

    Returns:
        Non-empty hostname or IP string.

    Raises:
        EapiConfigError: If no hostname can be resolved.
    """
    for candidate in (_non_empty_str(host.hostname), _non_empty_str(os.environ.get(ENV_EAPI_HOST))):
        if candidate is not None:
            return candidate
    msg = (
        f"Host {host.name!r}: set 'host.hostname', or environment {ENV_EAPI_HOST}, "
        "to a non-empty address."
    )
    raise EapiConfigError(msg)


def _resolve_transport(data: dict[str, Any]) -> str:
    """Resolve transport: 'eapi_transport', then 'ENV_EAPI_TRANSPORT', then default."""
    from_data = _non_empty_str(data.get(DATA_KEY_TRANSPORT))
    if from_data is not None:
        return from_data
    from_env = _non_empty_str(os.environ.get(ENV_EAPI_TRANSPORT))
    if from_env is not None:
        return from_env
    return DEFAULT_EAPI_TRANSPORT


def _resolve_port(host: Host, data: dict[str, Any]) -> int | None:
    """Resolve port: 'eapi_port', 'host.port', 'ENV_EAPI_PORT', else None (pyeapi default)."""
    for candidate in (
        _coerce_port(data.get(DATA_KEY_PORT)),
        _coerce_port(host.port),
        _coerce_port(os.environ.get(ENV_EAPI_PORT)),
    ):
        if candidate is not None:
            return candidate
    return None


def _resolve_username(host: Host, data: dict[str, Any]) -> str:
    """Resolve username: 'eapi_username', 'host.username', 'ENV_EAPI_USERNAME', else error."""
    if DATA_KEY_USERNAME in data:
        chosen = _non_empty_str(data.get(DATA_KEY_USERNAME))
        if chosen is not None:
            return chosen
    if host.username:
        chosen = _non_empty_str(host.username)
        if chosen is not None:
            return chosen
    env_u = _non_empty_str(os.environ.get(ENV_EAPI_USERNAME))
    if env_u is not None:
        return env_u
    msg = (
        f"Host {host.name!r}: set non-empty username via 'host.data[{DATA_KEY_USERNAME!r}]', "
        f"'host.username', or {ENV_EAPI_USERNAME}."
    )
    raise EapiConfigError(msg)


def _resolve_password(host: Host, data: dict[str, Any]) -> str:
    """Resolve password: 'eapi_password', 'host.password', 'ENV_EAPI_PASSWORD', else error."""
    if DATA_KEY_PASSWORD in data:
        raw = data[DATA_KEY_PASSWORD]
        if raw is not None:
            return str(raw)
    if host.password is not None:
        return str(host.password)
    if ENV_EAPI_PASSWORD in os.environ:
        return os.environ[ENV_EAPI_PASSWORD]
    msg = (
        f"Host {host.name!r}: set password via 'host.data[{DATA_KEY_PASSWORD!r}]', "
        f"'host.password', or {ENV_EAPI_PASSWORD}."
    )
    raise EapiConfigError(msg)


def _optional_str_from_data_or_env(
    data: dict[str, Any],
    data_key: str,
    env_name: str,
) -> str | None:
    """Optional path or string: 'data_key', then 'env_name', else None."""
    if data_key in data:
        raw = data[data_key]
        if raw is None:
            pass
        else:
            text = str(raw).strip()
            if text:
                return text
    env_val = _non_empty_str(os.environ.get(env_name))
    if env_val is not None:
        return env_val
    return None


def _optional_positive_int_from_data_env_default(
    data: dict[str, Any],
    data_key: str,
    env_name: str,
    default: int,
) -> int:
    """Positive timeout: 'data_key', then 'env_name', then 'default'.

    Raises:
        EapiConfigError: If a present value is not a positive integer.
    """
    if data_key in data:
        raw = data[data_key]
        if raw is not None:
            return _parse_positive_int(data_key, raw)
    if env_name in os.environ:
        return _parse_positive_int(env_name, os.environ[env_name])
    return default


def _parse_positive_int(label: str, raw: object) -> int:
    if isinstance(raw, bool):
        msg = f"{label!r} must be a number, not a boolean."
        raise EapiConfigError(msg)
    if isinstance(raw, int):
        if raw <= 0:
            msg = f"{label!r} must be positive, got {raw!r}."
            raise EapiConfigError(msg)
        return raw
    try:
        n = int(str(raw).strip())
    except ValueError as exc:
        msg = f"{label!r} must be an integer, got {raw!r}."
        raise EapiConfigError(msg) from exc
    if n <= 0:
        msg = f"{label!r} must be positive, got {raw!r}."
        raise EapiConfigError(msg)
    return n


def connect_kwargs_from_host(host: Host) -> dict[str, Any]:
    """Build keyword arguments for 'pyeapi.connect' from a Nornir host.

    Resolution order for each parameter is: inventory ('host.data' / host fields),
    then environment variables (names in 'nornflow_arista.eapi_client.constants'),
    then defaults where defined there.

    Hostname uses 'host.hostname', then 'NORNFLOW_ARISTA_EAPI_HOST'. There is no
    default hostname.

    Transport defaults to DEFAULT_EAPI_TRANSPORT ('https') if unset everywhere.

    Port defaults to None so pyeapi chooses the transport default (e.g. 443 for https).

    Timeout defaults to DEFAULT_EAPI_TIMEOUT (60), matching pyeapi's default.

    Optional TLS file paths default to omission (None) if unset everywhere.

    Username and password have no default after inventory and env: missing values
    raise EapiConfigError.

    This function performs no network I/O.

    Args:
        host: Nornir inventory host.

    Returns:
        Keyword arguments for 'pyeapi.connect' except 'return_node'.

    Raises:
        EapiConfigError: If required values are missing or invalid.
    """
    data = _host_data(host)

    hostname = _resolve_hostname(host)
    transport = _resolve_transport(data)
    port = _resolve_port(host, data)
    username = _resolve_username(host, data)
    password = _resolve_password(host, data)
    timeout = _optional_positive_int_from_data_env_default(
        data,
        DATA_KEY_TIMEOUT,
        ENV_EAPI_TIMEOUT,
        DEFAULT_EAPI_TIMEOUT,
    )

    kwargs: dict[str, Any] = {
        "transport": transport,
        "host": hostname,
        "username": username,
        "password": password,
        "port": port,
        "timeout": timeout,
    }

    key_file = _optional_str_from_data_or_env(data, DATA_KEY_KEY_FILE, ENV_EAPI_KEY_FILE)
    if key_file is not None:
        kwargs["key_file"] = key_file
    cert_file = _optional_str_from_data_or_env(data, DATA_KEY_CERT_FILE, ENV_EAPI_CERT_FILE)
    if cert_file is not None:
        kwargs["cert_file"] = cert_file
    ca_file = _optional_str_from_data_or_env(data, DATA_KEY_CA_FILE, ENV_EAPI_CA_FILE)
    if ca_file is not None:
        kwargs["ca_file"] = ca_file

    return kwargs


def node_from_host(host: Host, **connect_overrides: Any) -> Node:
    """Open an eAPI Node for 'host'.

    Builds kwargs with 'connect_kwargs_from_host', merges 'connect_overrides',
    then calls 'pyeapi.connect(..., return_node=True)'.

    Args:
        host: Nornir inventory host.
        **connect_overrides: Extra or replacement keywords for 'pyeapi.connect'
            (for example 'context=' for 'ssl.SSLContext').

    Returns:
        Connected 'pyeapi.client.Node'.

    Raises:
        EapiConfigError: When inventory and environment do not yield a valid mapping.
        pyeapi.eapilib.ConnectionError: When the TCP/TLS session cannot be established.
        TypeError: If 'pyeapi.connect' does not return a Node when 'return_node' is True.
    """
    kwargs = connect_kwargs_from_host(host)
    kwargs.update(connect_overrides)
    node = pyeapi.connect(**kwargs, return_node=True)
    if not isinstance(node, Node):
        msg = "pyeapi.connect(return_node=True) did not return a Node instance."
        raise TypeError(msg)
    return node
