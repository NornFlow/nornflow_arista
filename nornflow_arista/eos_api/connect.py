"""Map a Nornir 'Host' to 'pyeapi.connect' kwargs and to a 'Node'.

Resolution rules live in 'helpers' and names in 'constants'. This module only
assembles the final keyword dict and, for 'node_from_host', calls 'pyeapi.connect'.

Typical usage:

    from nornflow_arista.eos_api.connect import node_from_host

    node = node_from_host(host)
    node.enable("show version")

For tests or inspection without opening a socket, use 'connect_kwargs_from_host'.
"""

from typing import Any

import pyeapi
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
)


def connect_kwargs_from_host(host: Host) -> dict[str, Any]:
    """Build keyword arguments for 'pyeapi.connect' from a Nornir host.

    Order of resolution for each field is implemented in 'helpers': inventory
    ('host.data' and host fields), then environment variables from 'constants',
    then defaults where defined (for example timeout).

    This function does not perform network I/O.

    Args:
        host: Nornir inventory host.

    Returns:
        A dict suitable for 'pyeapi.connect(**kwargs)' without 'return_node'.

    Raises:
        EapiConfigError: If required settings (for example hostname, username,
            password) cannot be resolved or a numeric field is invalid.
    """
    data = helpers.host_data(host)

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


def node_from_host(host: Host, **connect_overrides: Any) -> Node:
    """Open a 'pyeapi.client.Node' for 'host'.

    Builds kwargs with 'connect_kwargs_from_host', merges 'connect_overrides',
    then calls 'pyeapi.connect(..., return_node=True)'.

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
