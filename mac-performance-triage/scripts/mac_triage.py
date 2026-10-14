#!/usr/bin/env python3
"""
mac_triage.py — read-only macOS performance snapshot.

Measures the signals that actually explain a slow/freezing Mac, and computes
the TRUE working set by inverting the memory compressor's compression ratio.

Read-only by design: runs no destructive command, kills nothing, deletes
nothing. Deliberately avoids `log show`, which is expensive enough to worsen
the very problem being diagnosed.

Usage:
    python3 mac_triage.py            # full snapshot
    python3 mac_triage.py --json     # machine-readable
"""

import json
import re
import subprocess
import sys
from datetime import datetime

GB = 1024 ** 3


def sh(cmd, timeout=30):
    """Run a shell command, return stdout as str ('' on any failure)."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True,
                           text=True, timeout=timeout)
        return r.stdout
    except Exception:
        return ""


def hardware():
    brand = sh("sysctl -n machdep.cpu.brand_string").strip()
    memsize = int(sh("sysctl -n hw.memsize").strip() or 0)
    ncpu = int(sh("sysctl -n hw.ncpu").strip() or 0)
    # Apple Silicon max RAM depends on chip tier. Only the base tier (no
    # Pro/Max/Ultra suffix) is safe to call out; verify with Apple before
    # any purchase decision.
    tier = "base" if re.match(r"^Apple M\d+$", brand) else "Pro/Max/Ultra"
    return {"chip": brand, "cores": ncpu, "ram_bytes": memsize, "tier": tier}


def memory():
    """Parse vm_stat + top for the real memory picture."""
    vm = sh("vm_stat")
    page = 4096
    m = re.search(r"page size of (\d+) bytes", vm)
    if m:
        page = int(m.group(1))

    def stat(label):
        mm = re.search(rf"{re.escape(label)}:\s+(\d+)", vm)
        return int(mm.group(1)) if mm else 0

    stored = stat("Pages stored in compressor")
    occupied = stat("Pages occupied by compressor")
    compressions = stat("Compressions")
    decompressions = stat("Decompressions")

    # top -l 1 gives the kernel's own accounting of used/free/compressor,
    # which is more trustworthy than summing vm_stat buckets.
    t = sh("top -l 1 -n 0")
    used = unused = comp_phys = wired = 0
    pm = re.search(
        r"PhysMem:\s+([\d.]+)([MG])\s+used\s+\(([\d.]+)([MG])\s+wired,\s*"
        r"([\d.]+)([MG])\s+compressor\)[,]?\s+([\d.]+)([MG])\s+unused", t)

    def to_bytes(val, unit):
        return float(val) * (GB if unit == "G" else GB / 1024)

    if pm:
        used = to_bytes(pm.group(1), pm.group(2))
        wired = to_bytes(pm.group(3), pm.group(4))
        comp_phys = to_bytes(pm.group(5), pm.group(6))
        unused = to_bytes(pm.group(7), pm.group(8))
    else:
        # Fall back to vm_stat if top's format shifts between macOS releases.
        comp_phys = occupied * page
        unused = stat("Pages free") * page

    # THE KEY CALCULATION.
    # The compressor squeezes `stored` pages of logical data into `occupied`
    # physical pages. Inverting that ratio recovers how much memory the
    # running apps actually asked for -- the number that tells you whether
    # the machine is genuinely undersized or merely needs a restart.
    ratio = (stored / occupied) if occupied else 0.0
    comp_logical = comp_phys * ratio if ratio else 0.0
    uncompressed_resident = max(used - comp_phys, 0)
    working_set = uncompressed_resident + comp_logical

    swap = sh("sysctl -n vm.swapusage").strip()
    swap_total = 0.0
    sm = re.search(r"total = ([\d.]+)M", swap)
    if sm:
        swap_total = float(sm.group(1))

    return {
        "used": used, "unused": unused, "wired": wired,
        "compressor_physical": comp_phys, "compressor_logical": comp_logical,
        "compression_ratio": ratio, "working_set": working_set,
        "compressions": compressions, "decompressions": decompressions,
        "swap_total_mb": swap_total,
    }


def load():
    up = sh("uptime")
    m = re.search(r"load averages?:\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", up)
    avgs = [float(x) for x in m.groups()] if m else [0.0, 0.0, 0.0]
    um = re.search(r"up\s+(.*?),\s+\d+ users?", up)
    return {"avg": avgs, "uptime": um.group(1).strip() if um else "unknown"}


def disk():
    out = sh("df -k /System/Volumes/Data").splitlines()
    if len(out) < 2:
        return {}
    f = out[-1].split()
    try:
        total, avail = int(f[1]) * 1024, int(f[3]) * 1024
    except (ValueError, IndexError):
        return {}
    return {"total": total, "avail": avail,
            "pct_used": round((1 - avail / total) * 100) if total else 0}


def top_processes(n=10):
    """Instantaneous CPU from top's SECOND sample.

    `ps %cpu` is a decaying lifetime average and will badly misrank a process
    that just started spinning -- always read top's second sample instead.
    """
    out = sh("top -l 2 -n %d -o cpu -stats pid,command,cpu,mem" % n, timeout=30)
    blocks = out.split("Processes:")
    rows = []
    if len(blocks) >= 3:
        # Only rows AFTER top's "PID COMMAND ..." header are processes. Without
        # this gate the summary line ("809 total, 9 running, ...") parses as a
        # bogus process, since it also begins with a number.
        in_table = False
        for line in blocks[-1].splitlines():
            f = line.split()
            if not in_table:
                if f and f[0] == "PID":
                    in_table = True
                continue
            if len(f) >= 4 and f[0].isdigit():
                rows.append({"pid": f[0], "command": " ".join(f[1:-2]),
                             "cpu": f[-2], "mem": f[-1]})
    return rows[:n]


# Patterns match against the FULL argv. Anchor anything whose name also shows
# up inside config paths (e.g. `~/.claude/`) to the executable slot, or every
# process that merely reads that directory gets miscounted as the app itself.
APP_PATTERNS = [
    ("Chrome", r"Google Chrome"), ("Safari", r"Safari"),
    ("Claude Code (CLI)", r"^\S*/claude\b|^claude\b"),
    ("Claude desktop", r"Claude\.app"),
    ("Slack", r"Slack"), ("Notion", r"Notion"), ("Zoom", r"zoom"),
    ("Teams", r"Teams"), ("RingCentral", r"RingCentral"),
    ("WhatsApp", r"WhatsApp"), ("Wispr Flow", r"Wispr"),
    ("Spotify", r"Spotify"), ("Docker", r"[Dd]ocker"),
    ("VS Code / Cursor", r"Code Helper|Cursor|Electron"),
    ("Terminal/iTerm", r"iTerm|Terminal"),
]


def by_app():
    """Sum RSS per app family.

    RSS double-counts memory shared between a multi-process app's helpers, so
    treat every figure here as an UPPER BOUND on what quitting would reclaim.
    """
    out = sh("ps -Ao rss,args")
    totals, counts = {}, {}
    for line in out.splitlines()[1:]:
        parts = line.strip().split(None, 1)
        if len(parts) != 2:
            continue
        try:
            rss = int(parts[0]) * 1024
        except ValueError:
            continue
        args = parts[1]
        for name, pat in APP_PATTERNS:
            if re.search(pat, args):
                totals[name] = totals.get(name, 0) + rss
                counts[name] = counts.get(name, 0) + 1
                break
    return sorted(({"app": k, "bytes": v, "procs": counts[k]}
                   for k, v in totals.items()),
                  key=lambda x: -x["bytes"])


def pressure_evidence():
    """Kernel OOM kills and stalls are the hard proof of memory exhaustion."""
    dirs = "~/Library/Logs/DiagnosticReports /Library/Logs/DiagnosticReports"
    listing = sh(f"find {dirs} -type f -mtime -14 2>/dev/null")
    files = [f for f in listing.splitlines() if f.strip()]
    jetsam = [f.split("/")[-1] for f in files if "JetsamEvent" in f]
    stalls = [f.split("/")[-1] for f in files if "shutdown_stall" in f]
    panics = [f.split("/")[-1] for f in files if "panic" in f.lower()]
    return {"jetsam": jetsam, "stalls": stalls, "panics": panics,
            "total_14d": len(files)}


def capture_active():
    """Detect a live call BEFORE anyone suggests quitting apps."""
    a = sh("pmset -g assertions")
    audio_in = "audio-in" in a
    cam = sh("ps -Ao %cpu,comm | grep cameracaptured | grep -v grep")
    cam_cpu = 0.0
    if cam.strip():
        try:
            cam_cpu = float(cam.split()[0])
        except (ValueError, IndexError):
            pass
    return {"audio_in": audio_in, "camera_cpu": cam_cpu,
            "likely_on_call": audio_in and cam_cpu > 5.0}


def gb(b):
    return f"{b / GB:.1f} GB"


def report():
    hw, mem, ld = hardware(), memory(), load()
    dk, ev, cap = disk(), pressure_evidence(), capture_active()
    apps, procs = by_app(), top_processes()
    ram = hw["ram_bytes"]
    findings = []

    print("=" * 68)
    print(f"  MAC PERFORMANCE TRIAGE — {datetime.now():%Y-%m-%d %H:%M}")
    print("=" * 68)
    print(f"\nHARDWARE  {hw['chip']}, {hw['cores']} cores, {gb(ram)} "
          f"({hw['tier']} tier)")
    print(f"UPTIME    {ld['uptime']}")

    cores = hw["cores"] or 1
    flag = "OVERLOADED" if ld["avg"][0] > cores else "ok"
    print(f"LOAD      {ld['avg'][0]:.2f} / {ld['avg'][1]:.2f} / "
          f"{ld['avg'][2]:.2f}  across {cores} cores — {flag}")
    if ld["avg"][0] > cores:
        findings.append(
            f"Load {ld['avg'][0]:.1f} exceeds {cores} cores — processes are "
            f"queueing for CPU.")

    print("\n--- MEMORY " + "-" * 56)
    print(f"  Used              {gb(mem['used'])} of {gb(ram)}")
    print(f"  Free              {gb(mem['unused'])}")
    print(f"  Wired (kernel)    {gb(mem['wired'])}")
    if mem["compression_ratio"]:
        print(f"  Compressor        {gb(mem['compressor_physical'])} physical, "
              f"holding ~{gb(mem['compressor_logical'])} logical "
              f"({mem['compression_ratio']:.1f}:1)")
    print(f"  Swap              {mem['swap_total_mb']:.0f} MB "
          f"(0 is normal on Apple Silicon — it prefers compression)")
    print(f"  Lifetime          {mem['compressions']:,} compressions / "
          f"{mem['decompressions']:,} decompressions")
    print(f"\n  >> TRUE WORKING SET: ~{gb(mem['working_set'])} "
          f"vs {gb(ram)} physical")

    over = mem["working_set"] - ram
    if over > 0:
        print(f"  >> OVER CAPACITY BY ~{gb(over)}")
        findings.append(
            f"Working set ~{gb(mem['working_set'])} exceeds {gb(ram)} of RAM "
            f"by ~{gb(over)}. Compression is absorbing the gap, and every "
            f"decompression is a CPU stall — this is the freezing.")
    else:
        print(f"  >> Fits, with ~{gb(-over)} headroom")

    if mem["unused"] < 1 * GB:
        findings.append(
            f"Only {gb(mem['unused'])} free — effectively zero headroom.")
    if mem["decompressions"] > 5_000_000:
        findings.append(
            f"{mem['decompressions']:,} lifetime decompressions indicates "
            f"sustained compressor thrash. A reboot clears it.")

    print("\n--- DISK " + "-" * 58)
    if dk:
        print(f"  {gb(dk['avail'])} free of {gb(dk['total'])} "
              f"({dk['pct_used']}% used)")
        if dk["pct_used"] < 90:
            print("  NOT A BOTTLENECK — deleting files will not improve speed.")
        else:
            findings.append(
                f"Disk {dk['pct_used']}% full — under 10% free, macOS does "
                f"start to suffer. Worth reclaiming space.")

    print("\n--- TOP CPU (instantaneous) " + "-" * 39)
    for p in procs[:8]:
        print(f"  {p['pid']:<8} {p['command'][:38]:<38} "
              f"{p['cpu']:>6}%  {p['mem']:>8}")

    print("\n--- MEMORY BY APP (upper bound; RSS double-counts) " + "-" * 16)
    for a in apps[:8]:
        print(f"  {a['app']:<22} {gb(a['bytes']):>9}  ({a['procs']} procs)")

    print("\n--- PRESSURE EVIDENCE " + "-" * 45)
    if ev["jetsam"]:
        print(f"  KERNEL OOM KILLS: {len(ev['jetsam'])} in 14 days")
        for j in ev["jetsam"][:3]:
            print(f"    {j}")
        findings.append(
            f"{len(ev['jetsam'])} JetsamEvent(s) in 14 days — the kernel has "
            f"already killed processes to reclaim memory. Hard confirmation.")
    else:
        print("  No kernel OOM kills in 14 days.")
    if ev["stalls"]:
        print(f"  Shutdown stalls: {len(ev['stalls'])}")
    if ev["panics"]:
        print(f"  PANICS: {len(ev['panics'])}")
        findings.append(f"{len(ev['panics'])} kernel panic(s) — investigate "
                        f"separately; not a memory-pressure symptom.")

    print("\n--- CAPTURE STATE " + "-" * 49)
    print(f"  Mic active: {cap['audio_in']}   "
          f"cameracaptured CPU: {cap['camera_cpu']:.1f}%")
    if cap["likely_on_call"]:
        print("  >> LIKELY ON A LIVE CALL — do not quit apps right now.")

    print("\n" + "=" * 68)
    print("  FINDINGS")
    print("=" * 68)
    if findings:
        for i, f in enumerate(findings, 1):
            print(f"  {i}. {f}")
    else:
        print("  Nothing anomalous. Memory, load, and disk all within range.")
    print()
    return {"hardware": hw, "memory": mem, "load": ld, "disk": dk,
            "apps": apps, "evidence": ev, "capture": cap,
            "findings": findings}


if __name__ == "__main__":
    data = report()
    if "--json" in sys.argv:
        print(json.dumps(data, indent=2, default=str))
