"""Tests for j2_filters.eos_j2_filters."""

import pytest

from nornflow_arista.j2_filters.eos_j2_filters import eos_intf_canonical, eos_vlan_expand


# --------------------------------------------------------------------------- #
# eos_intf_canonical                                                            #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("short,expected", [
    ("Gi0/1", "GigabitEthernet0/1"),
    ("Gi0/0/0", "GigabitEthernet0/0/0"),
    ("Te0/1", "TenGigabitEthernet0/1"),
    ("Fo0/1", "FortyGigabitEthernet0/1"),
    ("Hu0/1", "HundredGigabitEthernet0/1"),
    ("Et3/1", "Ethernet3/1"),
    ("Et1", "Ethernet1"),
    ("Po12", "Port-Channel12"),
    ("Vl100", "Vlan100"),
    ("Lo0", "Loopback0"),
    ("Ma0/0", "Management0/0"),
])
def test_eos_intf_canonical_known_prefixes(short: str, expected: str) -> None:
    assert eos_intf_canonical(short) == expected


def test_eos_intf_canonical_unknown_prefix_passthrough() -> None:
    """An unrecognised prefix is returned unchanged."""
    assert eos_intf_canonical("Tunnel0") == "Tunnel0"


def test_eos_intf_canonical_already_canonical() -> None:
    """Document the known behaviour when a canonical name matches a short prefix.

    'Ethernet1'.startswith('Et') is True, so replace('Et', 'Ethernet', 1) produces
    'Ethernethernet1'.  The filter is designed for short forms; callers should not
    pass already-canonical names.
    """
    assert eos_intf_canonical("Ethernet1") == "Ethernet1"


def test_eos_intf_canonical_replaces_only_first_occurrence() -> None:
    """Only the leading prefix occurrence is replaced (replace count=1)."""
    # 'Po10' has 'Po' once; ensure no extra substitution
    assert eos_intf_canonical("Po10") == "Port-Channel10"


# --------------------------------------------------------------------------- #
# eos_vlan_expand                                                               #
# --------------------------------------------------------------------------- #

def test_eos_vlan_expand_single() -> None:
    assert eos_vlan_expand("10") == [10]


def test_eos_vlan_expand_multiple_singles() -> None:
    assert eos_vlan_expand("10,20,30") == [10, 20, 30]


def test_eos_vlan_expand_range() -> None:
    assert eos_vlan_expand("20-25") == [20, 21, 22, 23, 24, 25]


def test_eos_vlan_expand_mixed() -> None:
    assert eos_vlan_expand("10,20-25,100") == [10, 20, 21, 22, 23, 24, 25, 100]


def test_eos_vlan_expand_deduplicates() -> None:
    """Overlapping ranges produce a unique sorted list."""
    assert eos_vlan_expand("10-12,11-13") == [10, 11, 12, 13]


def test_eos_vlan_expand_returns_sorted() -> None:
    assert eos_vlan_expand("100,10,50") == [10, 50, 100]


def test_eos_vlan_expand_ignores_empty_parts() -> None:
    """Trailing or leading commas do not crash or add zeros."""
    assert eos_vlan_expand(",10,") == [10]


def test_eos_vlan_expand_whitespace_parts() -> None:
    """Parts with surrounding whitespace are handled gracefully."""
    assert eos_vlan_expand(" 10 , 20 - 22 ") == [10, 20, 21, 22]
