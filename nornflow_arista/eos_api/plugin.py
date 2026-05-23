"""Nornir connection plugin for Arista EOS via pyeapi (eAPI).

Registered under the entry-point name 'pyeapi' (see 'pyproject.toml').
Tasks should obtain a 'Node' through 'ensure_pyeapi_connection' or
'task.host.get_connection("pyeapi", task.nornir.config)' after the host has
been opened with merged inventory data (see 'connect.ensure_pyeapi_connection').
"""

from typing import Any

import pyeapi
from nornir.core.configuration import Config
from pyeapi.client import Node

from nornflow_arista.eos_api.connect import connect_kwargs_from_open
from nornflow_arista.eos_api.constants import PYEAPI_CONNECTION_NAME

CONNECTION_NAME = PYEAPI_CONNECTION_NAME


class Pyeapi:
    """Nornir connection plugin: one cached 'pyeapi.client.Node' per host."""

    def open(
        self,
        hostname: str | None,
        username: str | None,
        password: str | None,
        port: int | None,
        platform: str | None,
        extras: dict[str, Any] | None = None,
        configuration: Config | None = None,
    ) -> None:
        """Connect and store the 'Node' on 'self.connection'.

        Args:
            hostname: Device address (from inventory / connection_options).
            username: Login user.
            password: Login password.
            port: TCP port override.
            platform: Unused for eAPI; accepted for Nornir API compatibility.
            extras: Vendor options ('eapi_*' keys); often pre-merged with
                'host.data' by 'ensure_pyeapi_connection'.
            configuration: Nornir config (unused today; reserved).
        """
        _ = platform, configuration
        host_label = hostname or "unknown"
        kwargs = connect_kwargs_from_open(
            host_label=host_label,
            hostname=hostname,
            username=username,
            password=password,
            port=port,
            extras=extras,
        )
        node = pyeapi.connect(**kwargs, return_node=True)
        if not isinstance(node, Node):
            msg = "pyeapi.connect(return_node=True) did not return a Node instance."
            raise TypeError(msg)
        self.connection = node

    def close(self) -> None:
        """Close the underlying eAPI transport when possible."""
        node = getattr(self, "connection", None)
        if node is None:
            return
        transport = getattr(node, "_connection", None)
        if transport is not None and hasattr(transport, "close"):
            try:  # noqa: SIM105
                transport.close()
            except OSError:
                pass
        self.connection = None
