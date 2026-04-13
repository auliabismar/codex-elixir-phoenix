# Tidewave Debug Playbook

This document lists common introspection commands and patterns for diagnosing complex BEAM state and concurrency issues using the Tidewave MCP server.

## Common Tools

| Tool | Usage | Purpose |
|------|-------|---------|
| `list_processes` | `list_processes()` | Overview of all running processes, their memory usage, and status. |
| `get_process_info` | `get_process_info(pid)` | Deep dive into a specific process: status, stacktrace, dictionary, links, and monitors. |
| `trace_call` | `trace_call(module, function, args_pattern)` | Trace function calls in real-time. Crucial for race conditions. |
| `trace_send` | `trace_send(pid_pattern)` | Observe messages being sent from specific processes. |
| `trace_receive` | `trace_receive(pid_pattern)` | Observe messages being received by specific processes. |
| `get_ets_info` | `get_ets_info(table_id)` | Inspect ETS table status and contents. |

## Diagnostic Patterns

### 1. GenServer Deadlock Diagnosis
**Symptoms**: Task timeouts, "waiting" process status in logs.
1. Run `list_processes` and look for processes with status `waiting`.
2. For specific PIDs, run `get_process_info(pid)`.
3. Check `current_stacktrace` to see where the process is blocked (often a `GenServer.call`).
4. Trace the linked/monitored processes to find the circular dependency.

### 2. LiveView Racing Patterns
**Symptoms**: State flickering, inconsistent UI updates, socket reconnect loops.
1. Run `trace_call(MyModule.MyLiveView, :handle_event, :any)`.
2. Run `trace_call(MyModule.MyLiveView, :handle_info, :any)`.
3. Compare the arrival order of events vs info messages.
4. Use `get_process_info` on the LiveView PID to check its internal state after specific events.

### 3. ETS Table Corruption / Leak
**Symptoms**: `badarg` errors on ETS operations, memory creep.
1. Run `get_ets_info(table_name)`.
2. Check `size` and `memory` attributes.
3. Compare `owner` PID with current process list to ensure the owner is alive.

### 4. Supervisor Restart Storms
**Symptoms**: High CPU usage, Rapid log output of process starts/stops.
1. Run `trace_call(Supervisor, :handle_info, :any)`.
2. Filter for `{:EXIT, pid, reason}` messages.
3. Identify the child that keeps failing and the reason for its exit.

## Escalation Workflow
1. **Detect**: primary agent fails 2+ times on state/concurrency task.
2. **Authorize**: Orchestrator authorizes `deep-bug-investigator` or `call-tracer`.
3. **Inspect**: Specialist uses Tidewave tools to find root cause.
4. **Fix**: Specialist returns diagnosis; implementer applies fix.
5. **Verify**: Run `mix compile` and `mix test`.
