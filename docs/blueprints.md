# Blueprints

**Contents:**

- [state_snapshot.yaml](#state_snapshotyaml)
- [config_replace_from_file.yaml](#config_replace_from_fileyaml)
- [copy_file.yaml](#copy_fileyaml)
- [stage_and_replace.yaml](#stage_and_replaceyaml)
- [Writing your own blueprints](#writing-your-own-blueprints)

---

Blueprints are reusable, parameterised sequences of NornFlow tasks defined in YAML. They can be building blocks in a workflow: a workflow can invoke a blueprint the same way it invokes a single task, passing variables to control behaviour.

All blueprints in `nornflow-arista` live under `nornflow_arista/blueprints/`.

---

## `state_snapshot.yaml`

Captures a broad operational snapshot across facts, interfaces, routing, MLAG, LLDP, and configuration. Each getter result is stored into a runtime variable via `set_to`, making the data available to subsequent tasks or blueprints in the same workflow.

**No required variables.**

Runtime variables set by this blueprint:

| Variable | Source task |
|---|---|
| `facts` | `get_facts` |
| `interfaces` | `get_interfaces` |
| `interface_counters` | `get_interface_counters` |
| `bgp_summary` | `get_bgp_summary` |
| `ospf_neighbors` | `get_ospf_neighbors` |
| `mlag_status` | `get_mlag_status` |
| `ip_route` | `get_ip_route` |
| `lldp_neighbors` | `get_lldp_neighbors` (with `detail: true`) |
| `running_config` | `get_running_config` |

**Usage in a workflow:**

```yaml
tasks:
  - blueprint: state_snapshot.yaml
```

---

## `config_replace_from_file.yaml`

Replaces running-config, startup-config, or both, using a file already present on the device. Executes the appropriate `run_commands` step(s) conditionally based on `eos_replace_mode`.

**Required variables:**

| Variable | Values | Description |
|---|---|---|
| `eos_replace_mode` | `running`, `startup`, `both` | Which config to replace |
| `eos_replace_running_commands` | `str \| list[str]` | Command(s) to replace running-config (when mode includes `running`) |
| `eos_replace_startup_commands` | `str \| list[str]` | Command(s) to replace startup-config (when mode includes `startup`) |

**Usage:**

```yaml
vars:
  eos_replace_mode: running
  eos_replace_running_commands: "configure replace flash:my_checkpoint"

tasks:
  - blueprint: config_replace_from_file.yaml
```

---

## `copy_file.yaml`

Copies a file on the EOS device using `copy_from_remote`. Supports two forms: an explicit source/destination pair or a single full CLI copy command.

**Required variables (pick one form):**

Source/destination form:

| Variable | Description |
|---|---|
| `copy_source` | Copy source (URL or device path) |
| `copy_destination` | Copy destination path |

Full command form (set `use_copy_command: true`):

| Variable | Description |
|---|---|
| `use_copy_command` | `true` to use the command form |
| `copy_command` | Full `copy` CLI string (e.g. `copy scp://server/file.cfg flash:file.cfg`) |

**Usage:**

```yaml
vars:
  copy_source: scp://10.0.0.50/configs/spine1.cfg
  copy_destination: flash:spine1.cfg

tasks:
  - blueprint: copy_file.yaml
```

---

## `stage_and_replace.yaml`

Combines `copy_file` and `config_replace_from_file` in a single blueprint. Optionally copies a remote file to the device first (controlled by `stage_copy`), then performs a config replace.

**Variables:**

| Variable | Default | Description |
|---|---|---|
| `stage_copy` | `false` | Set to `true` to run the copy step first |
| `copy_source` | (required if stage_copy) | Source path or URL |
| `copy_destination` | (required if stage_copy) | Destination path on device |
| `eos_replace_mode` | (required) | `running`, `startup`, or `both` |
| `eos_replace_running_commands` | (required for running) | Replace command(s) for running-config |
| `eos_replace_startup_commands` | (required for startup) | Replace command(s) for startup-config |

**Usage:**

```yaml
vars:
  stage_copy: true
  copy_source: scp://10.0.0.50/baseline.cfg
  copy_destination: flash:baseline.cfg
  eos_replace_mode: running
  eos_replace_running_commands: "configure replace flash:baseline.cfg"

tasks:
  - blueprint: stage_and_replace.yaml
```

---

## Writing your own blueprints

A blueprint is a YAML file with a root `tasks:` key and an optional `description`. It uses the same task names, `args`, `if`, and `set_to` hooks as any workflow task list. Place your files under `local_blueprints` in `nornflow.yaml` to make them discoverable.

See [Contributing](contributing.md) for conventions.

---

| | |
|:--|--:|
| [<< Previous: Tasks](tasks.md) | [Next: Workflows >>](workflows.md) |
