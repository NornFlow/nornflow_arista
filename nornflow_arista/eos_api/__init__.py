"""Arista EOS eAPI helpers for Nornir: map inventory to 'pyeapi' connections."""

from nornflow_arista.eos_api.connect import (
    connect_kwargs_from_host,
    connect_kwargs_from_open,
    ensure_pyeapi_connection,
    node_from_host,
)
from nornflow_arista.eos_api.constants import PYEAPI_CONNECTION_NAME
from nornflow_arista.eos_api.exceptions import EapiConfigError
from nornflow_arista.eos_api.plugin import CONNECTION_NAME, Pyeapi

__all__ = [
    "CONNECTION_NAME",
    "PYEAPI_CONNECTION_NAME",
    "EapiConfigError",
    "Pyeapi",
    "connect_kwargs_from_host",
    "connect_kwargs_from_open",
    "ensure_pyeapi_connection",
    "node_from_host",
]
