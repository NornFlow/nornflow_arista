# Jinja2 Filters

**Contents:**

- [Where filters apply](#where-filters-apply)
- [eos_intf_canonical](#eos_intf_canonical)
- [eos_vlan_expand](#eos_vlan_expand)
- [Adding your own filters](#adding-your-own-filters)

---

`nornflow-arista` provides EOS-specific Jinja2 filters. Declare the installed companion package under `packages` in `nornflow.yaml`; NornFlow loads filter functions from the package's `j2_filters` tree (see [NornFlow `packages` setting](https://github.com/theandrelima/nornflow/blob/develop/docs/nornflow_settings.md#packages)).

```yaml
# nornflow.yaml — all asset types from the package (includes j2_filters)
packages:
  - name: nornflow_arista
```

To load only Jinja2 filters:

```yaml
packages:
  - name: nornflow_arista
    include:
      - j2_filters
```

## Where filters apply

Filters registered from this package are loaded into **NornFlow's orchestration Jinja environment**. Use them in:

- Workflow and blueprint YAML (for example task `args`, `if` conditions, and `vars`)
- Any other expression NornFlow renders before a task runs

They are **not** available inside device config `.j2` files rendered by `configure_from_template` or `safe_configure_from_template`. Those tasks use a separate, task-local Jinja environment for EOS CLI output. Pass workflow-derived values into device templates via task `args` (especially the `variables` dict). Apply filters in the workflow layer first, then hand the results to the task.

See [Device config templates](tasks.md#device-config-templates-two-jinja-layers) in the Tasks reference for the full data-flow pattern.

---

## `eos_intf_canonical`

Converts a short or abbreviated interface name to its canonical EOS long form.

Matching is **case-insensitive**: `gi0/1`, `Gi0/1`, and `GI0/1` all produce the same result. Already-canonical names pass through unchanged.

### Supported prefixes

| Short prefix | Canonical form |
|---|---|
| `Gi` | `GigabitEthernet` |
| `Te` | `TenGigabitEthernet` |
| `Fo` | `FortyGigabitEthernet` |
| `Hu` | `HundredGigabitEthernet` |
| `Et` | `Ethernet` |
| `Po` | `Port-Channel` |
| `Vl` | `Vlan` |
| `Lo` | `Loopback` |
| `Ma` | `Management` |

Unrecognised prefixes are returned unchanged.

### Usage

```jinja2
{{ "Gi0/1"         | eos_intf_canonical }}  {# GigabitEthernet0/1  #}
{{ "gi0/1"         | eos_intf_canonical }}  {# GigabitEthernet0/1  #}
{{ "GI0/1"         | eos_intf_canonical }}  {# GigabitEthernet0/1  #}
{{ "Te1/1"         | eos_intf_canonical }}  {# TenGigabitEthernet1/1 #}
{{ "Po10"          | eos_intf_canonical }}  {# Port-Channel10       #}
{{ "Ethernet1"     | eos_intf_canonical }}  {# Ethernet1 (unchanged) #}
{{ "Tunnel0"       | eos_intf_canonical }}  {# Tunnel0 (unknown prefix, unchanged) #}
```

### In a workflow or blueprint

```jinja2
{% for intf in interfaces %}
interface {{ intf | eos_intf_canonical }}
   description {{ intf_descriptions[intf] }}
{% endfor %}
```

---

## `eos_vlan_expand`

Expands a compact VLAN specification string into a sorted list of integer VLAN IDs. Supports comma-separated values and dash-delimited ranges. Duplicate IDs are deduplicated.

Raises `ValueError` if a range has start greater than end (e.g. `25-20`).

### Usage

```jinja2
{{ "10"           | eos_vlan_expand }}  {# [10]                          #}
{{ "10,20,30"     | eos_vlan_expand }}  {# [10, 20, 30]                  #}
{{ "20-25"        | eos_vlan_expand }}  {# [20, 21, 22, 23, 24, 25]      #}
{{ "10,20-25,100" | eos_vlan_expand }}  {# [10, 20, 21, 22, 23, 24, 25, 100] #}
{{ "10-12,11-13"  | eos_vlan_expand }}  {# [10, 11, 12, 13]              #}
```

### Passing expanded VLANs into a device template

Apply the filter in workflow task `args`, then reference the result from the device `.j2` file:

```yaml
tasks:
  - name: configure_from_template
    args:
      template_path: "{{ change_template_path }}"
      variables:
        vlans: "{{ vlan_spec | eos_vlan_expand }}"
```

```jinja2
{# templates/vlans.j2 — device config layer; no package filters here #}
{% for vlan in vlans %}
vlan {{ vlan }}
   name VLAN_{{ vlan }}
{% endfor %}
```

---

## Adding your own filters

Any Python function in `nornflow_arista/j2_filters/` is registered as a Jinja2 filter (function name = filter name) when `nornflow_arista` is declared under `packages` with `j2_filters` in `include`, or with no `include` to load every asset type from the package.

```python
# nornflow_arista/j2_filters/eos_j2_filters.py

def my_new_filter(value: str) -> str:
    ...
```

```jinja2
{{ some_value | my_new_filter }}  {# in workflow YAML / blueprint YAML #}
```

See [Contributing](contributing.md) for how to add new filters to this package.

---

| | |
|:--|--:|
| [<< Previous: Workflows](workflows.md) | [Next: Inventory Filters >>](filters.md) |
