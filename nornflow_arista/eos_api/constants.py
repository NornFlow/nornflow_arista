"""Constants for mapping Nornir hosts to Arista eAPI ('pyeapi') connections.

Resolution order for each setting (implemented in 'client.py'):

1. Nornir host fields and 'host.data' keys using the 'eapi_*' prefix (see DATA_KEY_*).
2. Environment variables (see ENV_*), if set.
3. A package default where one exists (see DEFAULT_*); optional settings may stay unset.

Credentials (username and password) have no default after step 2: if still unset, connection
configuration fails with a clear error.

The 'eapi_*' prefix keeps EOS eAPI options namespaced inside the generic 'host.data' bag.
"""

DEFAULT_EAPI_TRANSPORT: str = "https"
DEFAULT_EAPI_TIMEOUT: int = 60

DATA_KEY_TRANSPORT = "eapi_transport"
DATA_KEY_PORT = "eapi_port"
DATA_KEY_USERNAME = "eapi_username"
DATA_KEY_PASSWORD = "eapi_password" # noqa: S105
DATA_KEY_TIMEOUT = "eapi_timeout"
DATA_KEY_KEY_FILE = "eapi_key_file"
DATA_KEY_CERT_FILE = "eapi_cert_file"
DATA_KEY_CA_FILE = "eapi_ca_file"

ENV_EAPI_HOST = "NORNFLOW_ARISTA_EAPI_HOST"
ENV_EAPI_TRANSPORT = "NORNFLOW_ARISTA_EAPI_TRANSPORT"
ENV_EAPI_PORT = "NORNFLOW_ARISTA_EAPI_PORT"
ENV_EAPI_USERNAME = "NORNFLOW_ARISTA_EAPI_USERNAME"
ENV_EAPI_PASSWORD = "NORNFLOW_ARISTA_EAPI_PASSWORD" # noqa: S105
ENV_EAPI_TIMEOUT = "NORNFLOW_ARISTA_EAPI_TIMEOUT"
ENV_EAPI_KEY_FILE = "NORNFLOW_ARISTA_EAPI_KEY_FILE"
ENV_EAPI_CERT_FILE = "NORNFLOW_ARISTA_EAPI_CERT_FILE"
ENV_EAPI_CA_FILE = "NORNFLOW_ARISTA_EAPI_CA_FILE"


# Nornir connection plugin name (entry point, get_connection, connection_options).
PYEAPI_CONNECTION_NAME: str = "pyeapi"
