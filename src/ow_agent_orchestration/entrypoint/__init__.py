"""
ow entrypoint — delegates to the bundled opencode binary.

Production lookup order for the bundled opencode:
  1. OW_OPENCODE_PATH environment variable  (used by tests and advanced users)
  2. <this_file's_dir>/opencode             (installed layout)

Signal forwarding: SIGINT, SIGTERM, and SIGWINCH received by ow are
forwarded to the opencode child process so that the child can handle
them itself (e.g. clean shutdown on SIGTERM, resize on SIGWINCH).
"""

from __future__ import annotations

import importlib.metadata
import os
import signal
import subprocess
import sys
from pathlib import Path


def _find_bundled_opencode() -> str:
    """Return the path to the bundled opencode binary.

    Lookup order:
      1. OW_OPENCODE_PATH environment variable  (tests and power users)
      2. ~/.local/share/ow/opencode              (standard install location)
    """
    env_path = os.environ.get("OW_OPENCODE_PATH")
    if env_path:
        return env_path

    return str(Path.home() / ".local" / "share" / "ow" / "opencode")


def _ow_version() -> str:
    try:
        return importlib.metadata.version("ow-agent-orchestration")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def _opencode_version(opencode_bin: str) -> str:
    try:
        result = subprocess.run(
            [opencode_bin, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return (result.stdout + result.stderr).strip()
    except Exception:
        return "unknown"


def main() -> None:  # pragma: no cover entry point
    args = sys.argv[1:]
    opencode = _find_bundled_opencode()

    # --version: print ow's version then the bundled opencode's version
    if args == ["--version"]:
        print(f"ow {_ow_version()}")
        print(f"opencode {_opencode_version(opencode)}")
        sys.exit(0)

    # Start opencode as a child process, inheriting stdin/stdout/stderr
    proc = subprocess.Popen(
        [opencode] + args,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    # Forward signals from ow to the opencode child
    def _forward(sig, _frame):
        try:
            os.kill(proc.pid, sig)
        except ProcessLookupError:
            pass

    signal.signal(signal.SIGINT, _forward)
    signal.signal(signal.SIGTERM, _forward)
    signal.signal(signal.SIGWINCH, _forward)

    proc.wait()
    sys.exit(proc.returncode)
