---
name: mac-performance-triage
description: >
  Use when a Mac is slow, freezing, beachballing, lagging, running hot, or
  spinning the rainbow wheel; when apps quit or get killed unexpectedly; when
  the fans are loud or kernel_task is high; when someone asks to "clean up",
  "speed up", or "free space on" a Mac; or when deciding whether to buy more
  RAM or a bigger machine. Also use for "why is my laptop so slow", "running
  out of memory", "out of storage", "should I upgrade my RAM", and post-hoc
  questions about a freeze that already happened.
---

# Mac Performance Triage

## Overview

**A slow Mac is almost always a memory-capacity problem wearing a CPU costume.**

When RAM runs out, macOS compresses pages rather than swapping. Compression is
fast, but every *de*compression is a CPU stall. Millions of them read as "the
laptop is slow" and to `top` as high CPU — while free memory looks fine and the
disk has hundreds of GB free.

Measure the **true working set** against physical RAM. Everything else is
downstream of that number.

## Run This First

```bash
python3 scripts/mac_triage.py     # add --json for machine-readable
```

Read-only: kills nothing, deletes nothing, ~5 seconds.

## The Core Calculation

macOS never reports true demand directly. Recover it by inverting the
compressor's own ratio (`vm_stat`):

```
ratio        = "Pages stored in compressor" / "Pages occupied by compressor"
working_set  = (PhysMem_used - compressor_physical) + (compressor_physical × ratio)
```

A ratio near 2:1 is typical. If `working_set` exceeds installed RAM, the
machine is genuinely oversubscribed and no amount of tidying will fix it.

## Signals That Lie

| Signal | Why it misleads |
|---|---|
| `memory_pressure` "free percentage" | Reported **70% free** on a machine with 117 MB actually free. Ignore it. |
| Activity Monitor pressure graph | Lags badly; stays green through active thrash. |
| `ps %cpu` | A decaying *lifetime* average. A process that just started spinning ranks low. Use `top -l 2` and read the **second** sample. |
| Summed RSS per app | Double-counts memory shared between helper processes. Upper bound only. |
| Empty `/System/Volumes/VM/` | **Normal** on Apple Silicon — it prefers compression and creates swap lazily. Not a missing safety net, nothing to fix. |
| Free disk space | Irrelevant to speed above ~10% free. |

## Hard Evidence of Memory Exhaustion

`JetsamEvent-*.ips` in `~/Library/Logs/DiagnosticReports` means the kernel
already killed processes to reclaim RAM — conclusive. `shutdown_stall-*.ips`
and lifetime decompressions in the millions corroborate.

## Verdict Table

| Working set vs RAM | Verdict |
|---|---|
| Under, but free < 1 GB and decompressions in the millions | Reboot — thrash accumulated over uptime. |
| Over by < 25% | Fixable in software: quit idle Electron apps, enable Chrome Memory Saver, close unused agent sessions. |
| Over by > 25%, persisting after the above | Genuinely undersized; recommend more RAM. |

Apple Silicon RAM is soldered, so this is a purchase decision. Report the chip
tier (`machdep.cpu.brand_string` — a bare `Apple M4` is base tier and caps
lower than Pro/Max) and have the user confirm ceilings with Apple first.

## Safety Rules

1. **Never kill by PID.** PIDs are recycled; a stale PID may belong to
   something else by the time it's used. Match by name (`pkill -f <pattern>`)
   after previewing with `pgrep -fl`.
2. **Check capture state before suggesting quits.** An active mic tap plus
   busy `cameracaptured` means a live call — quitting apps cuts them off. The
   script flags this.
3. **Don't run `log show` over long windows.** A `--last 24h` query drove load
   average from 8 to 21 on a machine already thrashing. Diagnostics must not
   worsen the problem; read `DiagnosticReports` files instead.
4. **Never delete user files to fix speed.** See below.

## Common Mistakes

| Mistake | Correction |
|---|---|
| Treating it as a disk problem | "Slow laptop" and "clean up my Mac" arrive together but are unrelated above ~10% free. Report free space as evidence before anyone deletes. |
| Deleting files to "free things up" | Returns zero performance, and Documents holds originals indistinguishable from drafts by size or mtime. Inventory, let the user decide, never sweep-delete. |
| Quitting apps mid-task | 1 GB isn't worth a dropped call or lost session. Prefer Chrome's Memory Saver and its Task Manager (⇧⌥Esc) over quitting the browser. |
| Chasing a 200 MB orphan | Order recommendations by GB. A leaked helper is satisfying to find and irrelevant next to a 5 GB browser. |

## Reference

`references/macos-memory-internals.md` — compressor mechanics, jetsam bands,
Apple Silicon swap semantics, and the full command inventory.
