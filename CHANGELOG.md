# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-05-26

First public release. Reference NornFlow companion package for Arista EOS over eAPI.

### Added

- Nornir connection plugin `pyeapi` with inventory merge from `host.data` and `connection_options.pyeapi.extras`
- Getter and config tasks, example blueprints, and workflows (`daily_snapshot`, `safe_config_change`)
- Jinja2 filters `eos_intf_canonical` and `eos_vlan_expand`
- `safe_configure_from_template` composite task for checkpoint, apply, and rollback on failure
- Package layout placeholders for inventory filters, hooks, and processors
- Documentation under `docs/` and CI on Python 3.10 through 3.14

[0.1.0]: https://github.com/NornFlow/nornflow_arista/releases/tag/v0.1.0
