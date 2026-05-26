"""Map a Nornir 'Host' to 'pyeapi.connect' kwargs and to a 'Node'.

Resolution rules live in 'helpers' and names in 'constants'. This module only
assembles the final keyword dict and, for 'node_from_host', calls 'pyeapi.connect'.

Typical usage:

    from nornflow_arista.eos_api.connect import ensure_pyeapi_connection, node_from_host

    node = ensure_pyeapi_connection(host, configuration)
    node.enable("show version")

For tests or inspection without opening a socket, use 'connect_kwargs_from_host'
or 'connect_kwargs_from_open'.
"""

from typing import Any

import pyeapi
from nornir.core.configuration import Config
from nornir.core.inventory import Host
from pyeapi.client import Node

from nornflow_arista.eos_api import helpers
from nornflow_arista.eos_api.constants import (
    DATA_KEY_CA_FILE,
    DATA_KEY_CERT_FILE,
    DATA_KEY_KEY_FILE,
    DATA_KEY_TIMEOUT,
    DEFAULT_EAPI_TIMEOUT,
    ENV_EAPI_CA_FILE,
    ENV_EAPI_CERT_FILE,
    ENV_EAPI_KEY_FILE,
    ENV_EAPI_TIMEOUT,
    PYEAPI_CONNECTION_NAME,
)


def _build_connect_kwargs(
    *,
    hostname: str,
    transport: str,
    port: int | None,
    username: str,
    password: str,
    timeout: int,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Assemble the final keyword dict for 'pyeapi.connect'.

    Args:
        hostname: Resolved device address.
        transport: 'https' or 'http'.
        port: TCP port, or None for pyeapi defaults.
        username: Login user.
        password: Login password.
        timeout: Connection timeout in seconds.
        data: Mapping with optional 'eapi_*' keys and TLS file paths.

    Returns:
        Keyword dict for 'pyeapi.connect'.
    """
    kwargs: dict[str, Any] = {
        "transport": transport,
        "host": hostname,
        "username": username,
        "password": password,
        "port": port,
        "timeout": timeout,
    }

    key_file = helpers.optional_str_from_data_or_env(
        data,
        DATA_KEY_KEY_FILE,
        ENV_EAPI_KEY_FILE,
    )
    if key_file is not None:
        kwargs["key_file"] = key_file

    cert_file = helpers.optional_str_from_data_or_env(
        data,
        DATA_KEY_CERT_FILE,
        ENV_EAPI_CERT_FILE,
    )
    if cert_file is not None:
        kwargs["cert_file"] = cert_file

    ca_file = helpers.optional_str_from_data_or_env(
        data,
        DATA_KEY_CA_FILE,
        ENV_EAPI_CA_FILE,
    )
    if ca_file is not None:
        kwargs["ca_file"] = ca_file

    return kwargs


def connect_kwargs_from_host(host: Host) -> dict[str, Any]:
    """Build keyword arguments for 'pyeapi.connect' from a Nornir host.

    Order of resolution for each field is implemented in 'helpers': merged
    inventory ('host.data' plus 'connection_options[pyeapi].extras', with extras
    overriding 'host.data'), then standard Nornir host fields where applicable,
    then environment variables from 'constants', then defaults where defined
    (for example timeout).

    This function does not perform network I/O.

    Args:
        host: Nornir inventory host.

    Returns:
        A dict suitable for 'pyeapi.connect(**kwargs)' without 'return_node'.

    Raises:
        EapiConfigError: If required settings (for example hostname, username,
            password) cannot be resolved or a numeric field is invalid.
    """
    data = helpers.merged_eapi_data(host)

    hostname = helpers.resolve_hostname(host)
    transport = helpers.resolve_transport(data)
    port = helpers.resolve_port(host, data)
    username = helpers.resolve_username(host, data)
    password = helpers.resolve_password(host, data)
    timeout = helpers.optional_positive_int_from_data_env_default(
        data,
        DATA_KEY_TIMEOUT,
        ENV_EAPI_TIMEOUT,
        DEFAULT_EAPI_TIMEOUT,
    )

    return _build_connect_kwargs(
        hostname=hostname,
        transport=transport,
        port=port,
        username=username,
        password=password,
        timeout=timeout,
        data=data,
    )


def connect_kwargs_from_open(
    *,
    host_label: str,
    hostname: str | None,
    username: str | None,
    password: str | None,
    port: int | None,
    extras: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build 'pyeapi.connect' kwargs from Nornir connection plugin 'open()' args.

    Used by the registered Nornir connection plugin. Does not perform network I/O.

    Args:
        host_label: Host name or address for error messages.
        hostname: Device address from Nornir.
        username: Login user from Nornir.
        password: Login password from Nornir.
        port: TCP port from Nornir.
        extras: Merged vendor options (see 'helpers.merged_eapi_data').

    Returns:
        Keyword dict for 'pyeapi.connect'.

    Raises:
        EapiConfigError: If required settings cannot be resolved.
    """
    data = extras if isinstance(extras, dict) else {}

    resolved_hostname = helpers.resolve_hostname_from_values(host_label, hostname)
    transport = helpers.resolve_transport(data)
    resolved_port = helpers.resolve_port_from_values(port, data)
    resolved_username = helpers.resolve_username_from_values(host_label, username, data)
    resolved_password = helpers.resolve_password_from_values(host_label, password, data)
    timeout = helpers.optional_positive_int_from_data_env_default(
        data,
        DATA_KEY_TIMEOUT,
        ENV_EAPI_TIMEOUT,
        DEFAULT_EAPI_TIMEOUT,
    )

    return _build_connect_kwargs(
        hostname=resolved_hostname,
        transport=transport,
        port=resolved_port,
        username=resolved_username,
        password=resolved_password,
        timeout=timeout,
        data=data,
    )


def ensure_pyeapi_connection(host: Host, configuration: Config) -> Node:
    """Return a cached 'Node' for 'host', opening via Nornir if needed.

    Merges 'host.data' and 'connection_options.pyeapi.extras' before the
    first 'open()' so 'eapi_*' inventory keys apply to the cached session.
    Participates in 'nornir.close_connections()' and NornFlow's
    'NornirManager.close_connections()'.

    Args:
        host: Nornir inventory host.
        configuration: Nornir 'Config' from 'task.nornir.config'.

    Returns:
        Connected 'pyeapi.client.Node'.

    Raises:
        EapiConfigError: If connection settings cannot be resolved.
        pyeapi.eapilib.ConnectionError: If the transport connection fails.
        TypeError: If the plugin does not return a 'Node'.
    """
    conn_name = PYEAPI_CONNECTION_NAME
    if conn_name not in host.connections:
        merged = helpers.merged_eapi_data(host)
        params = host.get_connection_parameters(conn_name)
        host.open_connection(
            connection=conn_name,
            configuration=configuration,
            hostname=params.hostname,
            username=params.username,
            password=params.password,
            port=params.port,
            platform=params.platform,
            extras=merged,
            default_to_host_attributes=True,
        )
    conn = host.get_connection(conn_name, configuration)
    if not isinstance(conn, Node):
        msg = f"Connection {conn_name!r} did not return a pyeapi Node instance."
        raise TypeError(msg)
    return conn


def node_from_host(host: Host, **connect_overrides: Any) -> Node:
    """Open a 'pyeapi.client.Node' for 'host' outside Nornir's connection cache.

    Builds kwargs with 'connect_kwargs_from_host', merges 'connect_overrides',
    then calls 'pyeapi.connect(..., return_node=True)'. Prefer
    'ensure_pyeapi_connection' from tasks so sessions are reused and closed
    with NornFlow/Nornir lifecycle.

    Args:
        host: Nornir inventory host.
        **connect_overrides: Extra or replacement keywords for 'pyeapi.connect'
            (for example 'context=' for an 'ssl.SSLContext').

    Returns:
        A connected 'pyeapi.client.Node'.

    Raises:
        EapiConfigError: If kwargs cannot be built from inventory and environment.
        pyeapi.eapilib.ConnectionError: If the transport connection fails.
        TypeError: If 'pyeapi.connect' with 'return_node=True' does not return a 'Node'.
    """
    kwargs = connect_kwargs_from_host(host)
    kwargs.update(connect_overrides)
    node = pyeapi.connect(**kwargs, return_node=True)
    if not isinstance(node, Node):
        msg = "pyeapi.connect(return_node=True) did not return a Node instance."
        raise TypeError(msg)
    return node
