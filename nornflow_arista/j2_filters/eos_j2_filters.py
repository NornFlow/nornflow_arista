"""Jinja2 filters for Arista EOS.

Register the package under 'packages' in nornflow.yaml so NornFlow loads
these filters into the Jinja2 environment used by workflows and blueprints.
"""

_INTF_PREFIXES = {
    "gi": "GigabitEthernet",
    "te": "TenGigabitEthernet",
    "fo": "FortyGigabitEthernet",
    "hu": "HundredGigabitEthernet",
    "et": "Ethernet",
    "po": "Port-Channel",
    "vl": "Vlan",
    "lo": "Loopback",
    "ma": "Management",
}


def eos_intf_canonical(name: str) -> str:
    """Convert a short interface name to its canonical EOS form.

    Matching is case-insensitive so 'gi0/1', 'Gi0/1', and 'GI0/1' all
    produce 'GigabitEthernet0/1'. Already-canonical names are returned
    unchanged.

    Args:
        name: Short or canonical interface name.

    Returns:
        Canonical EOS interface name, or the original string if no prefix matches.
    """
    name_lower = name.lower()
    for short_lower, full in _INTF_PREFIXES.items():
        if name_lower.startswith(short_lower) and not name_lower.startswith(full.lower()):
            return full + name[len(short_lower):]
    return name


def eos_vlan_expand(spec: str) -> list[int]:
    """Expand a compact VLAN specification into a sorted list of integers.

    Supports comma-separated values and ranges. Useful when generating
    'switchport trunk allowed vlan' lists or VLAN creation commands.

    Args:
        spec: VLAN specification (for example '10,20-25,100').

    Returns:
        Sorted list of VLAN IDs.

    Raises:
        ValueError: If a range is reversed (start > end).
    """
    vlans = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            s, e = int(start), int(end)
            if s > e:
                raise ValueError(f"Invalid VLAN range '{part}': start {s} is greater than end {e}")
            vlans.update(range(s, e + 1))
        else:
            vlans.add(int(part))
    return sorted(vlans)
