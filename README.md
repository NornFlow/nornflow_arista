# nornflow-arista

[![CI](https://github.com/NornFlow/nornflow_arista/actions/workflows/ci.yml/badge.svg)](https://github.com/NornFlow/nornflow_arista/actions/workflows/ci.yml)
![Python Versions](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Linter: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Installer: uv](https://img.shields.io/badge/installer-uv-blue)](https://github.com/astral-sh/uv)

A [NornFlow](https://github.com/theandrelima/nornflow) companion package for Arista EOS.

**Use with NornFlow.** This package provides EOS tasks and workflows for a NornFlow project. Install both in your automation environment and declare `nornflow_arista` under `packages` in `nornflow.yaml`.

---

## What this package is (and what it isn't)

**nornflow-arista is a reference implementation**, not a feature-complete EOS automation library.

Its primary purpose is to demonstrate *how a NornFlow companion package should be structured*: what directories to create, how tasks, blueprints, workflows, Jinja2 filters, inventory filters, hooks, and processors plug in, and how to wire an eAPI connection plugin into Nornir's connection lifecycle.

The task and workflow coverage is intentionally modest. It covers a useful subset of EOS operations, but a production-grade package would go much further: more getters, richer config workflows, EVPN/VXLAN helpers, multicast, ACL management, and beyond.

**Community contributions and Arista vendor engagement are not just welcome, they are necessary for this package to grow beyond a skeleton.** If you work at Arista or operate EOS networks at scale, your PRs, issue reports, and feedback are exactly what this project needs. See [CONTRIBUTING](docs/contributing.md).

---

## Documentation

| Document | Description |
|---|---|
| [Getting Started](docs/getting_started.md) | Install, wire into NornFlow, run your first workflow |
| [Connection & Inventory](docs/connection.md) | eAPI plugin, `host.data` keys, environment variables, resolution order |
| [Tasks](docs/tasks.md) | All provided getter and config tasks with their parameters |
| [Blueprints](docs/blueprints.md) | Reusable task sequences and how to compose them |
| [Workflows](docs/workflows.md) | Example end-to-end workflows shipped with the package |
| [Jinja2 Filters](docs/j2_filters.md) | EOS-specific filters for workflow and blueprint YAML |
| [Inventory Filters](docs/filters.md) | Host-level inventory filter functions |
| [Hooks](docs/hooks.md) | Task behaviour extensions via NornFlow hooks |
| [Processors](docs/processors.md) | Nornir result processors |
| [Contributing](docs/contributing.md) | How to add tasks, filters, workflows, and report issues |

---

## Quick look

Install NornFlow and this companion package:

```bash
pip install nornflow nornflow-arista
```

Declare the package in `nornflow.yaml` (you still need a Nornir config path and inventory in your project):

```yaml
nornir_config_file: nornir_config.yaml
packages:
  - name: nornflow_arista
```

Then run a workflow:

```bash
nornflow run daily_snapshot.yaml
```

See [Getting Started](docs/getting_started.md) for the full setup. Release history: [CHANGELOG.md](CHANGELOG.md).

---

## License

MIT. See [LICENSE](LICENSE).
