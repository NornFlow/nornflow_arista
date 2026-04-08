"""Arista EOS eAPI helpers for Nornir: map inventory to 'pyeapi' connections."""

from nornflow_arista.eos_api.connect import connect_kwargs_from_host, node_from_host
from nornflow_arista.eos_api.exceptions import EapiConfigError

__all__ = [
    "EapiConfigError",
    "connect_kwargs_from_host",
    "node_from_host",
]