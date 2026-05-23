"""Jinja2 filters for Arista EOS.

Register the package under 'packages' in nornflow.yaml so NornFlow loads
these filters into the Jinja2 environment used by workflows and blueprints.
"""


def eos_intf_canonical(name: str) -> str:
    """Convert a short interface name to its canonical EOS form.

    Accepts common short forms used in inventory or show output and returns
    the full interface name that EOS expects in configuration.

    Args:
        name: Short interface name (for example 'Gi0/1', 'Eth3/1', 'Po12').

    Returns:
        Canonical name (for example 'GigabitEthernet0/1', 'Ethernet3/1',
        'Port-Channel12').
    """
    mapping = {
        "Gi": "GigabitEthernet",
        "Te": "TenGigabitEthernet",
        "Fo": "FortyGigabitEthernet",
        "Hu": "HundredGigabitEthernet",
        "Et": "Ethernet",
        "Po": "Port-Channel",
        "Vl": "Vlan",
        "Lo": "Loopback",
        "Ma": "Management",
    }
    for short, full in mapping.items():
        if name.startswith(short):
            return name.replace(short, full, 1)
    return name


def eos_vlan_expand(spec: str) -> list[int]:
    """Expand a compact VLAN specification into a sorted list of integers.

    Supports comma-separated values and ranges. Useful when generating
    'switchport trunk allowed vlan' lists or VLAN creation commands.

    Args:
        spec: VLAN specification (for example '10,20-25,100').

    Returns:
        Sorted list of VLAN IDs.
    """
    vlans: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            vlans.update(range(int(start), int(end) + 1))
        else:
            vlans.add(int(part))
    return sorted(vlans)
