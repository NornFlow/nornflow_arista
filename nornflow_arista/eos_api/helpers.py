"""Internal helpers: normalize inventory and environment into eAPI connect inputs.

No public API here; import from the package '__init__' or the dedicated API module.
"""

import os
from typing import Any

from nornir.core.inventory import Host

from nornflow_arista.eos_api.constants import (
    DATA_KEY_PASSWORD,
    DATA_KEY_PORT,
    DATA_KEY_TRANSPORT,
    DATA_KEY_USERNAME,
    DEFAULT_EAPI_TRANSPORT,
    ENV_EAPI_HOST,
    ENV_EAPI_PASSWORD,
    ENV_EAPI_PORT,
    ENV_EAPI_TRANSPORT,
    ENV_EAPI_USERNAME,
    PYEAPI_CONNECTION_NAME,
)
from nornflow_arista.eos_api.exceptions import EapiConfigError


def first_not_none(*values: object | None) -> object | None:
    """Return the first argument that is not 'None'.

    Args:
        *values: Optional values, typically tried in precedence order.

    Returns:
        The first non-None value, or None if every argument is None.
    """
    for v in values:
        if v is not None:
            return v
    return None


def first_non_empty_str(*candidates: object | None) -> str | None:
    """Return the first candidate that becomes a non-empty string after strip.

    Args:
        *candidates: Objects passed through 'non_empty_str' in order.

    Returns:
        First non-empty result, or None.
    """
    for c in candidates:
        v = non_empty_str(c)
        if v is not None:
            return v
    return None


def host_data(host: Host) -> dict[str, Any]:
    """Return the host's 'data' mapping, or an empty dict if missing or invalid.

    Args:
        host: Nornir host; 'data' is normally a dict of inventory extras.

    Returns:
        A shallow dict for 'eapi_*' lookups, or '{}' if 'data' is absent or not a dict.
    """
    raw = getattr(host, "data", None) or {}
    if not isinstance(raw, dict):
        return {}
    return raw


def merged_eapi_data(host: Host) -> dict[str, Any]:
    """Merge 'host.data' with 'connection_options[pyeapi].extras'.

    Connection-specific extras override top-level 'host.data' keys when both
    define the same name. Used when opening the Nornir connection so 'eapi_*'
    keys in inventory 'data' reach the connection plugin.

    Args:
        host: Nornir inventory host.

    Returns:
        Shallow merged mapping for eAPI option lookups.
    """
    data = dict(host_data(host))
    params = host.get_connection_parameters(PYEAPI_CONNECTION_NAME)
    extras = params.extras
    if isinstance(extras, dict):
        data.update(extras)
    return data


def non_empty_str(value: object | None) -> str | None:
    """Strip; return None if missing or blank.

    Args:
        value: Any object, often a string from YAML or the environment.

    Returns:
        Stripped string, or None if 'value' is None or whitespace-only.
    """
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def coerce_port(value: object | None) -> int | None:
    """Parse optional port; None if absent/blank.

    Args:
        value: Integer-like value, or None, or blank string.

    Returns:
        Port as 'int', or None if absent/blank.

    Raises:
        EapiConfigError: If 'value' is present but not a valid TCP port (1-65535).
    """
    if value is None:
        return None
    if isinstance(value, int):
        port = value
    else:
        text = str(value).strip()
        if not text:
            return None
        try:
            port = int(text)
        except ValueError as exc:
            msg = f"eAPI port must be an integer, got {value!r}"
            raise EapiConfigError(msg) from exc

    if not 1 <= port <= 65535:
        msg = f"eAPI port must be between 1 and 65535, got {port!r}"
        raise EapiConfigError(msg)
    return port


def resolve_hostname_from_values(host_label: str, hostname: str | None) -> str:
    """Resolve device address from Nornir 'open()' args and environment.

    Args:
        host_label: Host name or hostname string for error messages.
        hostname: Value passed into the connection plugin 'open()'.

    Returns:
        Non-empty hostname or IP.

    Raises:
        EapiConfigError: If no address can be resolved.
    """
    found = first_non_empty_str(hostname, os.environ.get(ENV_EAPI_HOST))

    if found is not None:
        return found

    msg = (
        f"Host {host_label!r}: set 'host.hostname', or environment {ENV_EAPI_HOST}, "
        "to a non-empty address."
    )
    raise EapiConfigError(msg)


def resolve_username_from_values(
    host_label: str,
    username: str | None,
    data: dict[str, Any],
) -> str:
    """Resolve non-empty username from data, 'open()' arg, or environment.

    Args:
        host_label: Host name for error messages.
        username: Value passed into the connection plugin 'open()'.
        data: Merged 'host.data' and connection 'extras'.

    Returns:
        Non-empty username.

    Raises:
        EapiConfigError: If no non-empty username can be resolved.
    """
    found = first_non_empty_str(
        data.get(DATA_KEY_USERNAME),
        username,
        os.environ.get(ENV_EAPI_USERNAME),
    )
    if found is not None:
        return found
    msg = (
        f"Host {host_label!r}: set non-empty username via 'host.data[{DATA_KEY_USERNAME!r}]', "
        f"'host.username', or {ENV_EAPI_USERNAME}."
    )
    raise EapiConfigError(msg)


def resolve_password_from_values(
    host_label: str,
    password: str | None,
    data: dict[str, Any],
) -> str:
    """Resolve password from data, 'open()' arg, or environment.

    Args:
        host_label: Host name for error messages.
        password: Value passed into the connection plugin 'open()'.
        data: Merged 'host.data' and connection 'extras'.

    Returns:
        Password string (may be '').

    Raises:
        EapiConfigError: If no password source is available.
    """
    if DATA_KEY_PASSWORD in data:
        raw = data[DATA_KEY_PASSWORD]
        if raw is not None:
            return str(raw)

    if password is not None:
        return str(password)

    if ENV_EAPI_PASSWORD in os.environ:
        return os.environ[ENV_EAPI_PASSWORD]

    msg = (
        f"Host {host_label!r}: set password via 'host.data[{DATA_KEY_PASSWORD!r}]', "
        f"'host.password', or {ENV_EAPI_PASSWORD}."
    )
    raise EapiConfigError(msg)


def resolve_port_from_values(port: int | None, data: dict[str, Any]) -> int | None:
    """Resolve TCP port from data, 'open()' arg, or environment.

    Args:
        port: Value passed into the connection plugin 'open()'.
        data: Merged 'host.data' and connection 'extras'.

    Returns:
        TCP port, or None to let 'pyeapi' choose defaults for the transport.
    """
    result = first_not_none(
        coerce_port(data.get(DATA_KEY_PORT)),
        coerce_port(port),
        coerce_port(os.environ.get(ENV_EAPI_PORT)),
    )
    return int(result) if result is not None else None


def resolve_hostname(host: Host) -> str:
    """Resolve device address: 'host.hostname', then 'ENV_EAPI_HOST'.

    Args:
        host: Nornir inventory host.

    Returns:
        Non-empty hostname or IP string.

    Raises:
        EapiConfigError: If no non-empty value is found.
    """
    return resolve_hostname_from_values(host.name, host.hostname)


def resolve_transport(data: dict[str, Any]) -> str:
    """Resolve transport: 'eapi_transport', env, else 'DEFAULT_EAPI_TRANSPORT'.

    Args:
        data: Host 'data' mapping.

    Returns:
        Transport string for 'pyeapi.connect'.
    """
    found = first_non_empty_str(
        data.get(DATA_KEY_TRANSPORT),
        os.environ.get(ENV_EAPI_TRANSPORT),
    )
    return found if found is not None else DEFAULT_EAPI_TRANSPORT


def resolve_port(host: Host, data: dict[str, Any]) -> int | None:
    """Resolve port: 'eapi_port', 'host.port', env; else None for pyeapi default.

    Args:
        host: Nornir host.
        data: Host 'data' mapping.

    Returns:
        TCP port, or None to let 'pyeapi' choose defaults for the transport.
    """
    return resolve_port_from_values(host.port, data)


def resolve_username(host: Host, data: dict[str, Any]) -> str:
    """Resolve non-empty username: data key, 'host.username', env.

    Args:
        host: Nornir host.
        data: Host 'data' mapping.

    Returns:
        Non-empty username.

    Raises:
        EapiConfigError: If no non-empty username can be resolved.
    """
    return resolve_username_from_values(host.name, host.username, data)


def resolve_password(host: Host, data: dict[str, Any]) -> str:
    """Resolve password; allows explicit '' from 'data' when the key is present.

    Args:
        host: Nornir host.
        data: Host 'data' mapping.

    Returns:
        Password string (may be '').

    Raises:
        EapiConfigError: If no password source is available.
    """
    return resolve_password_from_values(host.name, host.password, data)


def optional_str_from_data_or_env(
    data: dict[str, Any],
    data_key: str,
    env_name: str,
) -> str | None:
    """Non-empty string from 'data_key', else from env, else None.

    Args:
        data: Host 'data' mapping.
        data_key: Key under 'data'.
        env_name: Environment variable name.

    Returns:
        First non-empty string found, or None.
    """
    first = data.get(data_key)
    return first_non_empty_str(first, os.environ.get(env_name))


def optional_positive_int_from_data_env_default(
    data: dict[str, Any],
    data_key: str,
    env_name: str,
    default: int,
) -> int:
    """Positive int from data, else env, else 'default'.

    Args:
        data: Host 'data' mapping.
        data_key: Key under 'data'.
        env_name: Environment variable name.
        default: Fallback when neither source is set.

    Returns:
        Positive integer.

    Raises:
        EapiConfigError: If a present value is not a positive integer.
    """
    if data_key in data and data[data_key] is not None:
        return parse_positive_int(data_key, data[data_key])

    if env_name in os.environ:
        return parse_positive_int(env_name, os.environ[env_name])

    return default


def parse_positive_int(label: str, raw: object) -> int:
    """Parse a strictly positive integer; reject booleans.

    Args:
        label: Name for error messages (data key or env name).
        raw: Raw value from inventory or environment.

    Returns:
        Integer strictly greater than zero.

    Raises:
        EapiConfigError: If 'raw' is invalid.
    """
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
