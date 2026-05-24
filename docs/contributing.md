# Contributing

**Contents:**

- [What to contribute](#what-to-contribute)
- [Development setup](#development-setup)
- [Conventions](#conventions)
- [Pull request process](#pull-request-process)
- [Reporting issues](#reporting-issues)
- [A note on scope](#a-note-on-scope)

---

`nornflow-arista` is intentionally minimal. It exists primarily as a **canonical reference** for what a NornFlow companion package should look like, not as a feature-complete EOS automation library. That distinction matters: the package ships just enough to be structurally correct and immediately useful, but it needs community input and real-world use cases to grow.

**All contributions are welcome**: new tasks, filters, hooks, processors, blueprints, workflows, bug reports, documentation improvements, and especially feedback from engineers running EOS at scale. Arista employees and Arista partners are particularly encouraged to engage. You know the platform better than anyone.

---

## What to contribute

The most impactful areas, roughly in priority order:

1. **More EOS getter tasks**: EVPN/VXLAN tables, multicast, ACLs, prefix lists, route maps, BFD, ISIS, PTP, OpenConfig data.
2. **Inventory filters**: host-targeting functions (by role, pod, EOS version, feature presence).
3. **Jinja2 filters**: EOS-specific helpers for config templating (MAC normalisation, prefix manipulation, EVPN RT formatting).
4. **Hooks**: pre/post task logic (change window enforcement, result assertion, structured logging).
5. **Processors**: result exporters, diff reporters, inventory writers.
6. **More workflows and blueprints**: BGP policy changes, VLAN provisioning, MLAG bring-up, upgrade workflows.
7. **Documentation**: corrections, examples, and clarifications anywhere in `docs/`.

---

## Development setup

```bash
git clone https://github.com/andrelima/nornflow_arista
cd nornflow_arista
uv sync --group dev
```

Run tests:

```bash
uv run pytest -q
```

Run the linter:

```bash
uv run ruff check .
```

---

## Conventions

### Tasks

- Define task functions in `nornflow_arista/tasks/`.
- Use `@_eos_getter` for simple read-only tasks whose body is `(task, node) -> raw_output`.
- Use `@_eos_task` for mutating tasks and for read-only tasks that need custom arguments or logic (for example `get_running_config`, `run_commands`).
- Always honour `task.is_dry_run()` in mutating tasks.
- Accept parameters as named function arguments (not via `task.params`).
- Google-style docstrings with `Args`, `Returns`, and `Raises` sections.

### Blueprints

- Place YAML files in `nornflow_arista/blueprints/`.
- Root key must be `tasks:` with an optional `description`.
- Only reference task names that exist in this package.

### Workflows

- Place YAML files in `nornflow_arista/workflows/`.
- Root key must be `workflow:`.
- Include a `description`, `vars` with defaults, and a sensible `failure_strategy`.

### Jinja2 filters

- Add filter functions to `nornflow_arista/j2_filters/eos_j2_filters.py` (or a new module in the same package).
- Function name becomes the filter name.
- Keep filters pure (no I/O, no side effects).
- Raise `ValueError` for invalid inputs; never silently return wrong data.

### Inventory filters

- Add functions to `nornflow_arista/filters/`.
- Signature: `def f(host: Host, **kwargs) -> bool`.

### Hooks and processors

- Subclass the appropriate NornFlow Hook base class.
- Place in `nornflow_arista/hooks/` or `nornflow_arista/processors/` respectively.

### Tests

- Every new public function must have at least one test.
- Use `pytest` and `unittest.mock`. No live device access in CI.
- Place tests under `tests/` mirroring the package structure.

### Style

- Python 3.10 through 3.14; use modern type hints in all function signatures (`str | None`, not `Optional[str]`).
- No type hints in function bodies.
- No `from __future__ import annotations`.
- Line length: 110 characters.
- `ruff check .` must pass with zero errors before submitting a PR.

---

## Pull request process

1. Fork the repository and create a branch from `dev` (not `main`).
2. Make your changes following the conventions above.
3. Add or update tests in `tests/`.
4. Run `uv run pytest -q` and `uv run ruff check .` locally. Both must be clean.
5. Open a PR targeting `dev`. CI runs automatically.
6. Add a clear description of what the PR adds or changes and why.

PRs from branches other than `dev` targeting `main` are blocked by CI.

---

## Reporting issues

Open a GitHub issue for:

- Bug reports (include the EOS version and `nornflow-arista` version if relevant)
- Feature requests (describe the EOS operation and what a task, filter, or workflow would look like)
- Documentation gaps or inaccuracies

---

## A note on scope

This package does not aim to be a comprehensive EOS SDK wrapper. `pyeapi` already provides that at the Python level. `nornflow-arista` adds the NornFlow-compatible layer on top: structured tasks, declarative workflows, and the conventions that make Arista automation composable and shareable across teams.

If a feature belongs in `pyeapi` itself rather than here, please consider contributing it upstream.

---

| | |
|:--|--:|
| [<< Previous: Processors](processors.md) | |
