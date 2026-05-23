# Hooks

**Contents:**

- [What hooks are](#what-hooks-are)
- [What EOS-specific hooks could look like](#what-eos-specific-hooks-could-look-like)
- [Adding a hook](#adding-a-hook)

---

> **This category is not yet implemented.**
>
> `nornflow_arista/hooks/` exists as a package placeholder. No hook classes are currently provided. Contributions are welcome. See [Contributing](contributing.md).

---

## What hooks are

NornFlow hooks extend task behaviour without modifying task code. They can run before or after a task, inspect or mutate the result, conditionally skip execution, and set runtime variables.

The hooks that ship with NornFlow core (`if`, `set_to`) are inline YAML hooks written directly in workflow and blueprint task entries. The special `set_to` value `"_failed"` stores whether the task failed; it is not a separate hook name. Custom Python hooks go further: they can implement complex pre/post logic that would be unwieldy in YAML.

See the NornFlow [hooks guide](https://github.com/theandrelima/nornflow/blob/main/docs/hooks_guide.md) for the full API.

## What EOS-specific hooks could look like

Some examples that would be meaningful in an Arista context:

| Hook | Description |
|---|---|
| `LogEosResult` | Emit structured logs from EOS command output |
| `AssertNoConfigDiff` | Fail the task if a configure-session diff is non-empty |
| `SkipIfMlagDown` | Skip a task on hosts where MLAG is not operational |
| `EnforceChangeWindow` | Abort mutating tasks outside a defined change window |
| `StoreResultToFile` | Write task output to a per-host file for later diffing |

## Adding a hook

Define a subclass of NornFlow's `Hook` base class in `nornflow_arista/hooks/` and register it in your `nornflow.yaml`. See the upstream hooks guide for the class interface and registration mechanism.

See [Contributing](contributing.md) to submit a hook to this package.

---

| | |
|:--|--:|
| [<< Previous: Inventory Filters](filters.md) | [Next: Processors >>](processors.md) |
