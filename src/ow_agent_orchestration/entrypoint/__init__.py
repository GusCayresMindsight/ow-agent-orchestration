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

    return str(Path.home() / ".local" / "share" / "ow" / "bin" / "opencode")


def _ow_xdg_env() -> dict[str, str]:
    """Return XDG base-dir overrides that scope opencode's storage under ow's
    own namespace, keeping it separate from the user's stock opencode install.

    With these set, opencode writes to:
      ~/.local/share/ow/opencode/   (data — sessions, SQLite DB)
      ~/.config/ow/opencode/        (config)
      ~/.cache/ow/opencode/         (cache / binary downloads)
      ~/.local/state/ow/opencode/   (state)
    """
    home = Path.home()
    return {
        "XDG_DATA_HOME":  str(home / ".local" / "share" / "ow"),
        "XDG_CONFIG_HOME": str(home / ".config" / "ow"),
        "XDG_CACHE_HOME":  str(home / ".cache" / "ow"),
        "XDG_STATE_HOME":  str(home / ".local" / "state" / "ow"),
    }


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

    # Start opencode as a child process, inheriting stdin/stdout/stderr.
    # XDG overrides ensure opencode's storage is scoped to ow's own namespace
    # and does not collide with the user's stock opencode installation.
    xdg = _ow_xdg_env()
    proc = subprocess.Popen(
        [opencode] + args,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
        env={**os.environ, **xdg},
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
