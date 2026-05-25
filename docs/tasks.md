# Tasks

**Contents:**

- [Getter tasks (read-only)](#getter-tasks-read-only)
- [Arguments for parametrised getters](#arguments-for-parametrised-getters)
- [Config tasks (mutating)](#config-tasks-mutating)
- [Adding your own tasks](#adding-your-own-tasks)

---

All tasks in `nornflow-arista` are standard NornFlow tasks: Python functions decorated with internal decorators that handle connection lifecycle, error wrapping, and dry-run behaviour.

Tasks are split into two modules:

- `nornflow_arista/tasks/getters.py`: read-only `show` commands
- `nornflow_arista/tasks/config.py`: mutating configuration operations

Every mutating task checks `task.is_dry_run()` and returns a skipped `Result` without opening an eAPI connection when dry-run is active.

---

## Getter tasks (read-only)

These tasks run `show` commands and return EOS output. Most return structured JSON from the eAPI; config-oriented getters such as `get_running_config` and `get_startup_config` return plain text. None of them modify device state.

| Task name | EOS command | Notes |
|---|---|---|
| `get_facts` | `show version` | Platform, software version, serial, MAC |
| `get_interfaces` | `show interfaces` | Full interface detail for all interfaces |
| `get_interfaces_status` | `show interfaces status` | Oper state, line protocol, description |
| `get_ip_interface_brief` | `show ip interface brief` | IP address summary per interface |
| `get_interface_counters` | `show interfaces counters errors` | CRC, discards, errors per interface |
| `get_bgp_summary` | `show ip bgp summary` | BGP peer summary (IPv4 unicast) |
| `get_bgp_neighbors_detail` | `show ip bgp neighbors` | Full per-neighbor BGP state |
| `get_ospf_neighbors` | `show ip ospf neighbor` | OSPF adjacency table |
| `get_ip_route` | `show ip route [vrf <vrf>] [<prefix>]` | Optional `vrf` and `prefix` args |
| `get_mlag_status` | `show mlag` + `show mlag config-sanity` | Returns both outputs as a dict |
| `get_vxlan_vteps` | `show vxlan vtep` | VXLAN VTEP table |
| `get_lldp_neighbors` | `show lldp neighbors [detail]` | Pass `detail: true` for extended output |
| `get_hardware_capacity` | `show hardware capacity` | TCAM / FIB utilisation |
| `get_transceiver_info` | `show interfaces transceiver` | DOM readings and optics info |
| `get_reload_cause` | `show reload cause` | Reason for last reload |
| `get_running_config` | `show running-config [section <s>] [all]` | Optional `section` and `all` args |
| `get_startup_config` | `show startup-config` | Returns startup-config as text |
| `get_config_diff` | `show running-config diffs` | Uncommitted session diffs |
| `dir_flash` | `dir flash:` | Contents of flash filesystem |
| `dir_path` | `dir <path>` | Optional `path` arg (default `flash:`) |
| `show_filesystem` | `show filesystem` | Filesystem usage summary |
| `show_inventory` | `show inventory` | Hardware inventory (cards, modules) |
| `run_commands` | _(arbitrary exec-mode commands)_ | Pass `commands` as string or list |

## Arguments for parametrised getters

**`get_ip_route`**

| Arg | Type | Required | Description |
|---|---|---|---|
| `vrf` | `str` | No | VRF name (default: default VRF) |
| `prefix` | `str` | No | Specific prefix to look up |

**`get_lldp_neighbors`**

| Arg | Type | Required | Description |
|---|---|---|---|
| `detail` | `bool` | No | If `true`, runs `show lldp neighbors detail` |

**`get_running_config`**

| Arg | Type | Required | Description |
|---|---|---|---|
| `section` | `str \| list[str]` | No | One or more section filters |
| `all` | `bool` | No | If `true`, includes default and non-default config |
| `include_defaults` | `bool` | No | Deprecated alias for `all` |

**`dir_path`**

| Arg | Type | Required | Description |
|---|---|---|---|
| `path` | `str` | No | Filesystem path (default `flash:`; blank input also falls back to `flash:`) |

**`run_commands`**

| Arg | Type | Required | Description |
|---|---|---|---|
| `commands` | `str \| list[str]` | Yes | One or more exec-mode commands |

---

## Config tasks (mutating)

These tasks modify device state. All honour dry-run.

### `configure`

Push configuration lines directly via `configure terminal`.

| Arg | Type | Required | Description |
|---|---|---|---|
| `commands` | `str \| list[str]` | Yes | One or more config-mode lines |

### `configure_session`

Open a named `configure session`, stage commands, and commit or abort. Optionally capture the session diff.

| Arg | Type | Default | Description |
|---|---|---|---|
| `commands` | `str \| list[str]` | (required) | Config lines to stage |
| `commit` | `bool` | `true` | Commit the session; set to `false` to abort |
| `include_diff` | `bool` | `true` | Include `show session-config diffs` in result |
| `session_name` | `str` | pyeapi default | Optional EOS session name |

On failure after the session is opened, an abort is attempted automatically.

### `commit_session`

Commit a previously opened named session.

| Arg | Type | Required | Description |
|---|---|---|---|
| `session_name` | `str` | Yes | EOS configure session name |

### `abort_session`

Abort a previously opened named session.

| Arg | Type | Required | Description |
|---|---|---|---|
| `session_name` | `str` | Yes | EOS configure session name |

### `configure_from_template`

Render a Jinja2 template and push the result via `configure terminal`.

| Arg | Type | Required | Description |
|---|---|---|---|
| `template_path` | `str` | One of the two | Path to a `.j2` file on the runner |
| `template_string` | `str` | One of the two | Inline template string |
| `variables` | `dict` | No | Extra vars merged into template context |
| `encoding` | `str` | `utf-8` | File encoding for `template_path` |

`template_string` takes precedence when both are provided. The template context automatically includes `host.name` and `host.data`.

### `safe_configure_from_template`

Checkpoint running-config, render a Jinja2 template, push via `configure terminal`, and run `configure replace` from the checkpoint if the apply step fails. Used by the `safe_config_change` workflow.

| Arg | Type | Required | Description |
|---|---|---|---|
| `checkpoint_name` | `str` | Yes | Checkpoint basename; stored as `flash:checkpoint_<name>` |
| `template_path` | `str` | One of the two | Path to a `.j2` file on the runner |
| `template_string` | `str` | One of the two | Inline template string |
| `variables` | `dict` | No | Extra vars merged into template context |
| `encoding` | `str` | `utf-8` | File encoding for `template_path` |

On success, the result includes `destination` (checkpoint path), `checkpoint_raw`, and `apply_raw`. On apply failure after the checkpoint is written, rollback is attempted before the task returns failed.

### `configure_replace`

Replace the running configuration using a file already on the device.

| Arg | Type | Required | Description |
|---|---|---|---|
| `path` | `str` | Yes | On-device path (e.g. `flash:checkpoint_pre_change`) |

### `create_checkpoint`

Save a copy of the running-config to flash as a named checkpoint.

| Arg | Type | Required | Description |
|---|---|---|---|
| `name` | `str` | Yes | Checkpoint name; stored as `flash:checkpoint_<name>` |

Result includes `destination` (the full flash path), which can be captured with `set_to` for use in a subsequent `configure_replace`.

### `rollback`

Roll back to a previous commit in EOS's configure session history.

| Arg | Type | Default | Description |
|---|---|---|---|
| `steps` | `int` | `1` | Number of commits to roll back |

> **Note:** This runs `configure rollback <steps>` on EOS's configure-session commit history, not on checkpoint files. Use `configure_replace` to restore a checkpoint file.

### `save_config`

Write the running configuration to startup-config (`write memory`). Takes no arguments.

### `copy_from_remote`

Run a `copy` command on the device, either from an explicit source/destination pair or as a full CLI string.

| Arg | Type | Required | Description |
|---|---|---|---|
| `source` | `str` | One of the two forms | Copy source (URL or on-device path) |
| `destination` | `str` | One of the two forms | Copy destination |
| `command` | `str` | One of the two forms | Full `copy` CLI line (alternative form) |

---

## Adding your own tasks

Tasks are plain Python functions. See [Contributing](contributing.md) for the conventions this package uses.

---

| | |
|:--|--:|
| [<< Previous: Connection & Inventory](connection.md) | [Next: Blueprints >>](blueprints.md) |
