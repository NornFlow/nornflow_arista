# Workflows

**Contents:**

- [daily_snapshot](#daily_snapshot)
- [safe_config_change](#safe_config_change)
- [Adding your own workflows](#adding-your-own-workflows)

---

Workflows are top-level YAML files that NornFlow discovers and runs by name. Unlike blueprints, workflows are complete automation units: they define their own variables, task sequences, and failure strategies.

All workflows in `nornflow-arista` live under `nornflow_arista/workflows/`.

---

## `daily_snapshot`

**File:** `nornflow_arista/workflows/daily_snapshot.yaml`

Captures a full operational snapshot across your fleet using the `state_snapshot` blueprint. Designed to be run on a schedule (cron, CI, etc.) as a baseline for change detection or auditing.

**No required variables.**

The blueprint stores 9 getter results as runtime variables (`facts`, `interfaces`, `bgp_summary`, etc.) that are available to any post-processing hooks or processors you attach.

```yaml
workflow:
  name: daily_snapshot
  description: >
    Capture a full operational snapshot using the state_snapshot blueprint
    and store key facts for later comparison or auditing.

  tasks:
    - blueprint: state_snapshot.yaml
```

**Run:**

```bash
nornflow run daily_snapshot.yaml
```

---

## `safe_config_change`

**File:** `nornflow_arista/workflows/safe_config_change.yaml`

Applies a configuration change safely by:
1. Creating a checkpoint of the current running-config.
2. Applying the change via a Jinja2 template.
3. Restoring the checkpoint on any host where step 2 fails.

The `failure_strategy: run-all` ensures all three steps execute on every host regardless of individual failures, so no host is left without an attempted rollback.

**Required variables** (pass via `--vars` or domain/workflow variables):

| Variable | Description |
|---|---|
| `checkpoint_name` | Name for the checkpoint file (e.g. `pre_change_20260523`) |
| `change_template_path` | Path to the Jinja2 template on the runner filesystem |

```yaml
workflow:
  name: safe_config_change
  failure_strategy: run-all

  vars:
    checkpoint_name: "pre_change_checkpoint"
    change_template_path: ~

  tasks:
    - name: create_checkpoint
      args:
        name: "{{ checkpoint_name }}"
      set_to:
        checkpoint_dest: "destination"

    - name: configure_from_template
      args:
        template_path: "{{ change_template_path }}"
      set_to:
        configure_failed: "_failed"

    - name: configure_replace
      if: "{{ configure_failed }}"
      args:
        path: "{{ checkpoint_dest }}"
```

**Run:**

```bash
nornflow run safe_config_change.yaml \
  --vars "checkpoint_name=pre_acl_change" \
         "change_template_path=templates/acl_update.j2"
```

**Dry run:**

```bash
nornflow run safe_config_change.yaml --dry-run \
  --vars "checkpoint_name=pre_acl_change" \
         "change_template_path=templates/acl_update.j2"
```

No connections are opened; each mutating task returns a skipped result.

---

## Adding your own workflows

Workflows are YAML files with a root `workflow:` key. See [Contributing](contributing.md) for the conventions this package uses.

---

| | |
|:--|--:|
| [<< Previous: Blueprints](blueprints.md) | [Next: Jinja2 Filters >>](j2_filters.md) |
