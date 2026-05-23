# Workflows

**Contents:**

- [daily_snapshot](#daily_snapshot)
- [safe_config_change](#safe_config_change)
- [Writing your own workflows](#writing-your-own-workflows)
- [Failure strategies](#failure-strategies)
- [Hooks available in tasks](#hooks-available-in-tasks)

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

## Writing your own workflows

A workflow file requires a root `workflow:` key. Minimal structure:

```yaml
workflow:
  name: my_workflow
  description: >
    Optional human-readable description.

  vars:
    my_var: default_value

  tasks:
    - name: some_task
      args:
        param: "{{ my_var }}"
```

Place workflow files under a directory listed in `local_workflows` in `nornflow.yaml`. NornFlow discovers them by filename (without the `.yaml` extension).

### Failure strategies

| Strategy | Behaviour |
|---|---|
| `fail-fast` (default) | Stop processing the task list on the first failed host |
| `skip-failed` | Skip failed hosts for subsequent tasks but continue |
| `run-all` | Run all tasks on all hosts regardless of failures |

`run-all` is the right choice when you need a cleanup or rollback step to always run.

### Hooks available in tasks

| Hook | Description |
|---|---|
| `if` | Jinja2 expression; task runs only if it evaluates truthy |
| `set_to` | Store a value from the task result into a runtime variable |

`set_to` with value `"_result"` stores `Result.result`; with `"_failed"` stores `Result.failed`.

See the NornFlow [hooks guide](https://github.com/theandrelima/nornflow/blob/main/docs/hooks_guide.md) for the full reference.

---

| | |
|:--|--:|
| [<< Previous: Blueprints](blueprints.md) | [Next: Jinja2 Filters >>](j2_filters.md) |
