# Processors

**Contents:**

- [What processors are](#what-processors-are)
- [What EOS-specific processors could look like](#what-eos-specific-processors-could-look-like)
- [Adding a processor](#adding-a-processor)

---

> **This category is not yet implemented.**
>
> `nornflow_arista/processors/` exists as a package placeholder. No processor classes are currently provided. Contributions are welcome. See [Contributing](contributing.md).

---

## What processors are

Nornir processors observe task execution as it happens. They implement callbacks that fire at the start and end of each task and aggregated result, making them suitable for real-time logging, result formatting, alerting, or writing output to external systems.

Processors are configured by import path in `nornflow.yaml` or directly in a workflow file.

## What EOS-specific processors could look like

Some examples relevant to EOS automation:

| Processor | Description |
|---|---|
| `EosJsonResultPrinter` | Pretty-print structured EOS JSON output per host |
| `ConfigDiffReporter` | Extract and display session diffs from configure-session results |
| `SnapshotExporter` | Write getter results to per-host JSON files for change detection |
| `SyslogForwarder` | Forward task results to a syslog receiver |
| `InventoryUpdater` | Write back facts (e.g. EOS version, serial) to inventory after a run |

See [Contributing](contributing.md) to submit a processor to this package.

---

| | |
|:--|--:|
| [<< Previous: Hooks](hooks.md) | [Next: Contributing >>](contributing.md) |
