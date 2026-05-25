"""Read-only Nornir tasks: EOS 'show' commands, config retrieval, and system info via eAPI."""

from nornir.core.task import Result, Task
from pyeapi.client import Node

from nornflow_arista.tasks.decorators import _eos_getter, _eos_task
from nornflow_arista.tasks.task_helpers import (
    _node_for_task,
    _result_ok,
    CommandsArg,
)


@_eos_getter
def get_facts(task: Task, node: Node) -> Result:
    """Run 'show version' and return structured CLI output (JSON encoding)."""
    return node.enable("show version")


@_eos_getter
def get_interfaces(task: Task, node: Node) -> Result:
    """Run 'show interfaces' and return CLI output."""
    return node.enable("show interfaces")


@_eos_getter
def get_interfaces_status(task: Task, node: Node) -> Result:
    """Run 'show interfaces status' (oper state, line protocol, etc.)."""
    return node.enable("show interfaces status")


@_eos_getter
def get_ip_interface_brief(task: Task, node: Node) -> Result:
    """Run 'show ip interface brief'."""
    return node.enable("show ip interface brief")


@_eos_getter
def get_interface_counters(task: Task, node: Node) -> Result:
    """Run 'show interfaces counters errors' (CRC, discards, etc.)."""
    return node.enable("show interfaces counters errors")


@_eos_getter
def get_bgp_summary(task: Task, node: Node) -> Result:
    """Run 'show ip bgp summary'."""
    return node.enable("show ip bgp summary")


@_eos_getter
def get_bgp_neighbors_detail(task: Task, node: Node) -> Result:
    """Run 'show ip bgp neighbors' (detailed neighbor output)."""
    return node.enable("show ip bgp neighbors")


@_eos_getter
def get_ospf_neighbors(task: Task, node: Node) -> Result:
    """Run 'show ip ospf neighbor'."""
    return node.enable("show ip ospf neighbor")


@_eos_task
def get_ip_route(
    task: Task,
    vrf: str | None = None,
    prefix: str | None = None,
) -> Result:
    """Run 'show ip route' with optional VRF or prefix filter.

    Args:
        vrf: VRF name (adds 'vrf <name>' to the command).
        prefix: Optional IPv4/IPv6 prefix to append (device-specific filtering).
    """
    cmd = "show ip route"
    if vrf:
        vrf_label = str(vrf).strip()
        if vrf_label:
            cmd += f" vrf {vrf_label}"
    if prefix:
        prefix_label = str(prefix).strip()
        if prefix_label:
            cmd += f" {prefix_label}"
    node = _node_for_task(task)
    out = node.enable(cmd)
    return _result_ok(task, out)


@_eos_getter
def get_mlag_status(task: Task, node: Node) -> Result:
    """Run 'show mlag' and 'show mlag config-sanity'; return both outputs."""
    mlag = node.enable("show mlag")
    sanity = node.enable("show mlag config-sanity")
    return {"mlag": mlag, "mlag_config_sanity": sanity}


@_eos_getter
def get_vxlan_vteps(task: Task, node: Node) -> Result:
    """Run 'show vxlan vtep'."""
    return node.enable("show vxlan vtep")


@_eos_task
def get_lldp_neighbors(task: Task, detail: bool = False) -> Result:
    """Run LLDP neighbor listing; optional detail view.

    Args:
        detail: If True (default False), run 'show lldp neighbors detail'.
    """
    cmd = "show lldp neighbors detail" if detail else "show lldp neighbors"
    node = _node_for_task(task)
    out = node.enable(cmd)
    return _result_ok(task, out)


@_eos_getter
def get_hardware_capacity(task: Task, node: Node) -> Result:
    """Run 'show hardware capacity'."""
    return node.enable("show hardware capacity")


@_eos_getter
def get_transceiver_info(task: Task, node: Node) -> Result:
    """Run 'show interfaces transceiver' (DOM / optics; often empty on cEOS)."""
    return node.enable("show interfaces transceiver")


@_eos_getter
def get_reload_cause(task: Task, node: Node) -> Result:
    """Run 'show reload cause'."""
    return node.enable("show reload cause")


@_eos_getter
def dir_flash(task: Task, node: Node) -> Result:
    """List contents of 'flash:' ('dir flash:')."""
    return node.enable("dir flash:")


@_eos_getter
def show_filesystem(task: Task, node: Node) -> Result:
    """Run 'show filesystem' (availability and fields vary by platform and EOS release)."""
    return node.enable("show filesystem")


@_eos_getter
def show_inventory(task: Task, node: Node) -> Result:
    """Run 'show inventory' for hardware component listing (output varies by platform)."""
    return node.enable("show inventory")


@_eos_task
def get_running_config(
    task: Task,
    section: str | list[str] | None = None,
    all: bool = False,
    include_defaults: bool = False,
) -> Result:
    """Return running configuration as text, optionally filtered by section(s).

    Args:
        section: If set, runs 'show running-config section <section>'. A list repeats
            the section keyword for each entry (EOS multi-section syntax).
        all: If True, append 'all' to include default statements where supported.
        include_defaults: Deprecated alias for ``all``; kept for backward compatibility.
    """
    node = _node_for_task(task)
    sections = []
    if section is not None:
        parts = section if isinstance(section, list) else [section]
        for part in parts:
            label = str(part).strip()
            if label:
                sections.append(label)

    include_all = all or include_defaults
    params = None
    if sections:
        params = " ".join(f"section {label}" for label in sections)
        if include_all:
            params += " all"
    elif include_all:
        params = "all"
    cfg = node.get_config("running-config", params=params, as_string=True)
    return _result_ok(task, cfg)


@_eos_task
def get_startup_config(task: Task) -> Result:
    """Return startup-config as a string."""
    node = _node_for_task(task)
    cfg = node.get_config("startup-config", as_string=True)
    return _result_ok(task, cfg)


@_eos_task
def get_config_diff(task: Task) -> Result:
    """Show differences between running-config and startup-config ('show running-config diffs')."""
    node = _node_for_task(task)
    out = node.run_commands(["show running-config diffs"], encoding="text")
    first = out[0] if out else {}
    text = str(first.get("output", ""))
    return _result_ok(task, text)


@_eos_task
def run_commands(task: Task, commands: CommandsArg) -> Result:
    """Run arbitrary exec-mode commands.

    Args:
        commands: A single command string or a list of command strings.
    """
    node = _node_for_task(task)
    out = node.enable(commands)
    return _result_ok(task, out)


@_eos_task
def dir_path(task: Task, path: str = "flash:") -> Result:
    """List a path on the device ('dir <path>').

    Args:
        path: Path to list (default 'flash:').
    """
    listing_path = path
    if not listing_path or not str(listing_path).strip():
        listing_path = "flash:"
    node = _node_for_task(task)
    out = node.enable(f"dir {listing_path}")
    return _result_ok(task, out)
