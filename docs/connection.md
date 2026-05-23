# Connection & Inventory

**Contents:**

- [Overview](#overview)
- [Inventory contract](#inventory-contract)
- [connection_options](#connection_options)
- [Error handling](#error-handling)

---

## Overview

`nornflow-arista` registers a Nornir connection plugin named `pyeapi`. Tasks obtain a connected `pyeapi.client.Node` through Nornir's standard `host.get_connection("pyeapi", task.nornir.config)` machinery, which means:

- One eAPI session is opened per host per run, then reused across all tasks.
- Sessions are closed cleanly by `nornir.close_connections()` at the end of the run.
- Dry-run mode never opens a socket.

The plugin is registered automatically via the `nornir.plugins.connections` entry-point in `pyproject.toml`. No manual registration is needed after `pip install`.

## Inventory contract

Connection settings are resolved in this order for each field:

1. `host.data` key (prefixed `eapi_*`)
2. Environment variable (`NORNFLOW_ARISTA_EAPI_*`)
3. Package default (where one exists)

If neither source provides a required field (username, password), `EapiConfigError` is raised before a connection is attempted.

### Full reference

| `host.data` key | Environment variable | Default | Notes |
|---|---|---|---|
| `eapi_transport` | `NORNFLOW_ARISTA_EAPI_TRANSPORT` | `https` | `http` or `https` |
| `eapi_port` | `NORNFLOW_ARISTA_EAPI_PORT` | pyeapi default | Omit to let pyeapi choose (443 for https, 80 for http) |
| `eapi_username` | `NORNFLOW_ARISTA_EAPI_USERNAME` | (required) | Login user |
| `eapi_password` | `NORNFLOW_ARISTA_EAPI_PASSWORD` | (required) | Login password |
| `eapi_timeout` | `NORNFLOW_ARISTA_EAPI_TIMEOUT` | `60` | Seconds; must be a positive integer |
| `eapi_key_file` | `NORNFLOW_ARISTA_EAPI_KEY_FILE` | (optional) | TLS client private key path |
| `eapi_cert_file` | `NORNFLOW_ARISTA_EAPI_CERT_FILE` | (optional) | TLS client certificate path |
| `eapi_ca_file` | `NORNFLOW_ARISTA_EAPI_CA_FILE` | (optional) | CA bundle path for server verification |

`host.hostname`, `host.username`, `host.password`, and `host.port` are also read as fallbacks for the corresponding fields if the `eapi_*` key is absent.

### Example host

```yaml
# inventory/hosts.yaml
spine1:
  hostname: 192.168.1.1
  username: admin
  password: ""
  data:
    eapi_transport: https
    eapi_timeout: 30
```

### TLS example

```yaml
leaf1:
  hostname: 10.0.0.10
  data:
    eapi_transport: https
    eapi_username: nornflow
    eapi_password: changeme
    eapi_ca_file: /etc/ssl/certs/arista-ca.pem
```

### Environment-only credentials

Credentials can be kept entirely out of inventory files:

```bash
export NORNFLOW_ARISTA_EAPI_USERNAME=admin
export NORNFLOW_ARISTA_EAPI_PASSWORD=secret
```

## connection_options

For per-host connection overrides without touching `host.data`, use Nornir's `connection_options`:

```yaml
spine1:
  hostname: 192.168.1.1
  connection_options:
    pyeapi:
      extras:
        eapi_transport: http
        eapi_port: 8080
```

`extras` values take precedence over `host.data` keys for the same connection.

## Error handling

All connection and configuration errors are wrapped in `EapiConfigError` (a `ValueError` subclass) or `pyeapi.eapilib.CommandError`. Both are caught by the `_eos_task` decorator and returned as a failed `Result` so NornFlow's failure strategy applies cleanly.

---

| | |
|:--|--:|
| [<< Previous: Getting Started](getting_started.md) | [Next: Tasks >>](tasks.md) |
