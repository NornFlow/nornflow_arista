# Getting Started

**Contents:**

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Wiring into NornFlow](#wiring-into-nornflow)
- [Inventory setup](#inventory-setup)
- [Running a workflow](#running-a-workflow)
- [Dry run](#dry-run)
- [Next steps](#next-steps)

---

## Prerequisites

- Python 3.10 through 3.14
- [NornFlow](https://github.com/theandrelima/nornflow) installed and configured in the same environment
- Arista EOS devices reachable over eAPI (HTTP or HTTPS)

## Installation

```bash
pip install nornflow-arista
```

Or with `uv`:

```bash
uv add nornflow-arista
```

## Wiring into NornFlow

`nornflow-arista` is a NornFlow companion package. Once installed, declare it in `nornflow.yaml` under the `packages` setting. NornFlow will automatically discover and register all assets it provides (tasks, blueprints, workflows, Jinja2 filters, inventory filters, hooks, and processors):

```yaml
packages:
  - name: nornflow_arista
```

If you only want a subset of asset types loaded, use the optional `include` key:

```yaml
packages:
  - name: nornflow_arista
    include:
      - tasks
      - blueprints
      - workflows
      - j2_filters
```

Valid values for `include` are: `tasks`, `workflows`, `blueprints`, `filters`, `hooks`, `j2_filters`, `processors`.


## Inventory setup

Each host needs credentials and connection settings. The minimal setup uses standard Nornir inventory fields:

```yaml
# inventory/hosts.yaml
sw1:
  hostname: 10.0.0.1
  username: admin
  password: secret
  data:
    eapi_transport: https
```

See [Connection & Inventory](connection.md) for the full list of `eapi_*` keys, environment variable fallbacks, and TLS options.

## Running a workflow

```bash
nornflow run daily_snapshot.yaml
```

To pass runtime variables:

```bash
nornflow run safe_config_change.yaml --vars "checkpoint_name=pre_change_001" "change_template_path=templates/acl_change.j2"
```

## Dry run

Every mutating task in this package respects NornFlow/Nornir's dry-run flag and returns a skipped result without opening a connection:

```bash
nornflow run safe_config_change.yaml --dry-run
```

## Next steps

- [Tasks](tasks.md): full task reference
- [Blueprints](blueprints.md): composing reusable task sequences
- [Workflows](workflows.md): the example workflows and how to build your own
- [Jinja2 Filters](j2_filters.md): EOS-specific template helpers
- [Contributing](contributing.md): adding more tasks, filters, and workflows

---

| | |
|:--|--:|
| | [Next: Connection & Inventory >>](connection.md) |
