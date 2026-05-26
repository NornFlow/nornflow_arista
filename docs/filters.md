# Inventory Filters

**Contents:**

- [What inventory filters are](#what-inventory-filters-are)
- [What EOS-specific filters could look like](#what-eos-specific-filters-could-look-like)
- [Adding a filter](#adding-a-filter)

---

> **This category is not yet implemented.**
>
> `nornflow_arista/filters/` exists as a package placeholder. No inventory filter functions are currently provided. Contributions are welcome. See [Contributing](contributing.md).

---

## What inventory filters are

In NornFlow, inventory filters are plain Python functions with the signature:

```python
from nornir.core.inventory import Host

def my_filter(host: Host, **kwargs) -> bool:
    ...
```

They allow workflows to target a dynamic subset of hosts without modifying inventory files. NornFlow discovers inventory filters from two places:

- **Companion packages** declared under `packages` in `nornflow.yaml` (for example `nornflow_arista/filters/` when `filters` is included, or when no `include` list limits asset types)
- **Project-local directories** listed under `local_filters` in `nornflow.yaml`

Filter function names become the names you use in workflow definitions. See [Getting Started](getting_started.md#wiring-into-nornflow) for the `packages` syntax.

## What EOS-specific filters could look like

Some examples that would be useful in an Arista environment:

| Filter | Description |
|---|---|
| `is_eos` | True if `host.platform` indicates an EOS device |
| `has_mlag` | True if `host.data` contains MLAG peer configuration |
| `is_spine` | True if `host.data["role"]` equals `spine` |
| `in_pod` | True if the host belongs to a given pod/fabric |
| `eos_version_gte` | True if the device runs EOS >= a specified version |
| `has_bgp` | True if the host has BGP peers configured in inventory |


See [Contributing](contributing.md) to submit a filter to this package.

---

| | |
|:--|--:|
| [<< Previous: Jinja2 Filters](j2_filters.md) | [Next: Hooks >>](hooks.md) |
