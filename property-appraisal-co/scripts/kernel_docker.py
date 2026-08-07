"""Boot / reuse the local Kernel Chromium-headful container and return its CDP WS URL."""
from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

KERNEL_REPO = Path.home() / "Documents/Claude/Agents/kernel-images/images/chromium-headful"
IMAGE_TAG = "kernel-docker"
CONTAINER_NAME = "kernel-docker"
CDP_HTTP = "http://localhost:9222/json/version"


class KernelError(RuntimeError):
    pass


def _container_running() -> bool:
    out = subprocess.run(
        ["docker", "ps", "--filter", f"name=^{CONTAINER_NAME}$", "--format", "{{.Names}}"],
        capture_output=True, text=True, check=False,
    )
    return CONTAINER_NAME in out.stdout.split()


def _cdp_ws_url(timeout_s: int = 60) -> str:
    deadline = time.time() + timeout_s
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(CDP_HTTP, timeout=2) as resp:
                data = json.loads(resp.read())
                ws = data.get("webSocketDebuggerUrl")
                if ws:
                    return ws
        except Exception as e:
            last_err = e
            time.sleep(1.5)
    raise KernelError(f"CDP endpoint never came up at {CDP_HTTP}: {last_err}")


def ensure_running() -> str:
    """Return the CDP WS URL. Boot the container if it isn't running."""
    if _container_running():
        return _cdp_ws_url(timeout_s=10)

    if not KERNEL_REPO.exists():
        raise KernelError(f"kernel-images repo missing at {KERNEL_REPO}")

    env = {**os.environ, "IMAGE": IMAGE_TAG}
    # Run the kernel run-docker.sh in the background; it daemonizes via `docker run -d`
    proc = subprocess.run(
        ["bash", "./run-docker.sh"],
        cwd=str(KERNEL_REPO),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise KernelError(
            f"run-docker.sh failed (exit {proc.returncode})\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return _cdp_ws_url(timeout_s=60)


def stop() -> None:
    subprocess.run(["docker", "stop", CONTAINER_NAME], capture_output=True, check=False)


if __name__ == "__main__":
    print(ensure_running())
