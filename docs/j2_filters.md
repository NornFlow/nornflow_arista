# Jinja2 Filters

**Contents:**

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

Once loaded, filters are available in all templates, blueprints, and workflow variable expressions.

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

### In a template

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

### In a template

```jinja2
vlan {{ vlan_spec | eos_vlan_expand | join(',') }}
{% for vlan in vlan_spec | eos_vlan_expand %}
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
{{ some_value | my_new_filter }}
```

See [Contributing](contributing.md) for how to add new filters to this package.

---

| | |
|:--|--:|
| [<< Previous: Workflows](workflows.md) | [Next: Inventory Filters >>](filters.md) |
