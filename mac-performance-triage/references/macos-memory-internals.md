# macOS Memory Internals

Background for interpreting `mac_triage.py` output. Apple Silicon specifics
noted where they differ from Intel.

## The Compressor

macOS has no traditional "free memory is good" model. It aggressively fills
RAM with file cache and compressed anonymous pages, so **low free memory is
normal**. What matters is whether the kernel can satisfy new allocations
without stalling.

When pressure rises, the kernel compresses inactive anonymous pages in place
rather than writing them to disk. Compression is roughly an order of magnitude
cheaper than NVMe I/O, which is why Apple Silicon prefers it and why swap files
often never appear.

The cost is asymmetric. Compressing happens on the reclaim path, in the
background. **Decompressing happens on the fault path — synchronously, while a
thread waits.** A working set that exceeds RAM cycles pages in and out of the
compressor continuously, and each cycle blocks a thread. That is the beachball.

### Relevant `vm_stat` fields

| Field | Meaning |
|---|---|
| `Pages stored in compressor` | Logical pages whose contents are held compressed |
| `Pages occupied by compressor` | Physical pages the compressor consumes |
| `Compressions` / `Decompressions` | Lifetime counters since boot |
| `Pages free` | Genuinely unallocated — expect this to be small |
| `Swapins` / `Swapouts` | Traffic to the swap file, usually 0 on Apple Silicon |

Divide stored by occupied for the live compression ratio. Multiply page counts
by the reported page size (16384 on Apple Silicon, 4096 on Intel) — hardcoding
4096 understates Apple Silicon figures by 4×.

### Interpreting the counters

Lifetime counters only mean something relative to uptime. 12M compressions over
27 hours is thrash; the same number over three months is unremarkable. Always
divide by uptime before drawing conclusions.

A **decompression-to-compression ratio approaching 1:1** means pages are being
pulled back almost as fast as they're stored — the working set is live, not
idle, and compression is buying nothing. A low ratio means the compressor is
holding genuinely cold pages, which is the healthy case.

## Swap on Apple Silicon

`/System/Volumes/VM/` is empty and `vm.swapusage` reads zero on many healthy
Apple Silicon machines. This is **not** a misconfiguration:

- Swap files are created lazily, on demand.
- The kernel strongly prefers compression first.
- Zero swapins/swapouts alongside millions of compressions is the expected
  signature of a machine under pressure but not yet spilling.

**Do not attempt to force swap on.** There is no supported control for it, the
common internet advice targets the long-removed `dynamic_pager`, and the
compressor is already doing the equivalent work more efficiently. Absent swap
is a symptom readout, never a fix target.

## Jetsam

Jetsam is the memory-pressure killer. When compression can no longer keep pace,
the kernel terminates processes by priority band — background and high-footprint
processes first, foreground app last.

A `JetsamEvent-*.ips` in `~/Library/Logs/DiagnosticReports` is **conclusive
proof** the machine ran out of memory. The header records `largestProcess`,
which names the biggest consumer at kill time.

Note the `.ips` schema varies by macOS release. Parsing per-process page counts
is unreliable across versions; the header fields are stable. Treat presence and
count of these files as the signal, not their internals.

## Wired Memory

Wired pages cannot be compressed or paged out — kernel, drivers, and pinned
allocations. It sets a hard floor on the working set. Wired memory growing
steadily over uptime suggests a driver or kernel-extension leak, which is a
different investigation from application pressure.

## Command Inventory

| Command | Use |
|---|---|
| `top -l 1 -n 0` | Kernel's own used/free/wired/compressor accounting. Authoritative. |
| `top -l 2 -n 15 -o cpu` | Instantaneous CPU. **Read the second sample** — the first is a lifetime average. |
| `vm_stat` | Page-level counters and the compression ratio. |
| `sysctl vm.swapusage hw.memsize hw.ncpu machdep.cpu.brand_string` | Hardware and swap facts. |
| `pmset -g assertions` | Who is holding mic, camera, and sleep assertions. |
| `pmset -g therm` | Thermal throttling. Usually clean on Apple Silicon. |
| `df -h /System/Volumes/Data` | Real user-data free space (not the read-only system volume). |
| `ps -Ao pid,ppid,%cpu,rss,etime,args` | Process inventory. `%cpu` is a lifetime average — rank with `top`. |
| `mdutil -s /` | Spotlight indexing state. |
| `tmutil status` | Time Machine activity. |
| `find ~/Library/Logs/DiagnosticReports -mtime -14` | Crash, jetsam, and stall evidence. |

### Commands to avoid during triage

`log show` over long windows builds a large index and is genuinely expensive —
a `--last 24h` query pushed load average from 8 to 21 on an already-thrashing
machine and returned nothing useful. If the unified log is truly needed, scope
to minutes and a tight predicate. `sudo powermetrics` is similarly heavy and
needs privileges triage shouldn't require.

## Ruling Out Non-Memory Causes

Check these before concluding memory, since each has a distinct fix:

| Cause | Check | Signature |
|---|---|---|
| Spotlight reindex | `mdutil -s /`, `ps` for `mds_stores`/`mdworker` | Sustained CPU in `mds*`; resolves on its own |
| Time Machine | `tmutil status` | `Running = 1` with heavy disk I/O |
| Thermal throttling | `pmset -g therm` | Warning levels recorded; rare on Apple Silicon |
| Photo/media analysis | `ps` for `photoanalysisd`, `mediaanalysisd` | High CPU after a large library import |
| Kernel/driver leak | Wired memory trend over uptime | Wired grows steadily, independent of apps |
| Disk genuinely full | `df -h` | Under ~10% free |

All of these were checked and cleared on the machine this skill was built from
— every daemon sat at 0% CPU while the compressor thrashed, which is what
isolated memory as the cause.

## Typical Consumers

Electron apps each bundle a full Chromium runtime, so a stack of four
(Slack, Notion, a phone client, a dictation tool) can rival a real browser.
Agentic CLI tools spawn per-session helper processes that are invisible in the
Dock — count them explicitly. Browsers dominate by default and respond well to
Chrome's Memory Saver, which discards idle tabs and restores them on click.
