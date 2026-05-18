import os
import shutil
import stat
import sys
import tempfile

_FAKE_OPENCODE_SCRIPT = """\
#!/bin/bash
set -euo pipefail

WORK_DIR="${FAKE_OPENCODE_WORK_DIR:-/tmp}"

# Record argv (everything passed to this script)
echo "$*" > "${WORK_DIR}/argv.txt"

# Record which instance was invoked
echo "${FAKE_OPENCODE_IDENTITY:-bundled}" > "${WORK_DIR}/invoked_by.txt"

# Handle --version
if [ "${1:-}" = "--version" ]; then
    echo "${FAKE_OPENCODE_VERSION:-0.0.0-fake}"
    exit 0
fi

# Optionally write to stdout
if [ -n "${FAKE_OPENCODE_STDOUT:-}" ]; then
    echo "${FAKE_OPENCODE_STDOUT}"
fi

# Optionally write to stderr
if [ -n "${FAKE_OPENCODE_STDERR:-}" ]; then
    echo "${FAKE_OPENCODE_STDERR}" >&2
fi

# Optionally read stdin and record it
if [ -n "${FAKE_OPENCODE_READ_STDIN:-}" ]; then
    cat > "${WORK_DIR}/stdin.txt"
fi

# Optionally catch signals, record them, and stay alive
if [ -n "${FAKE_OPENCODE_CATCH_SIGNALS:-}" ]; then
    trap "echo SIGINT >> '${WORK_DIR}/signals.txt'" INT
    trap "echo SIGTERM >> '${WORK_DIR}/signals.txt'; exit 0" TERM
    trap "echo SIGWINCH >> '${WORK_DIR}/signals.txt'" WINCH
    # Signal readiness by writing PID
    echo $$ > "${WORK_DIR}/opencode.pid"
    # Stay alive until killed
    while true; do
        sleep 0.1
    done
fi

exit "${FAKE_OPENCODE_EXIT_CODE:-0}"
"""


def before_scenario(context, scenario):
    context.tmpdir = tempfile.mkdtemp(prefix="ow_test_")

    # Directory for fake opencode to record invocation data
    context.work_dir = os.path.join(context.tmpdir, "work")
    os.makedirs(context.work_dir)

    # Write the configurable fake opencode binary
    context.bundled_opencode = os.path.join(context.tmpdir, "bundled_opencode")
    with open(context.bundled_opencode, "w") as f:
        f.write(_FAKE_OPENCODE_SCRIPT)
    os.chmod(context.bundled_opencode, os.stat(context.bundled_opencode).st_mode | stat.S_IEXEC)

    # Isolated HOME for installation scenarios
    context.fake_home = os.path.join(context.tmpdir, "home")
    os.makedirs(context.fake_home)

    # Base environment passed to all ow invocations
    context.env = os.environ.copy()
    context.env["OW_OPENCODE_PATH"] = context.bundled_opencode
    context.env["FAKE_OPENCODE_WORK_DIR"] = context.work_dir
    # Clear any inherited fake-opencode config from the outer environment
    for key in list(context.env):
        if key.startswith("FAKE_OPENCODE_") and key != "FAKE_OPENCODE_WORK_DIR":
            del context.env[key]

    # Locate the ow binary.  Prefer the one in the same bin/ directory as the
    # Python interpreter that is running behave (i.e. the active venv), so we
    # don't accidentally pick up a pre-existing system ow.
    venv_ow = os.path.join(os.path.dirname(sys.executable), "ow")
    context.ow = venv_ow if os.path.isfile(venv_ow) else shutil.which("ow")

    # Runtime state — populated by step functions
    context.ow_process = None   # long-running background process (signal tests)
    context.ow_result = None    # CompletedProcess (run-and-exit tests)
    context.install_result = None  # CompletedProcess for install steps
    context.mock_server = None  # HTTPServer for installation tests
    context.mock_server_thread = None


def after_scenario(context, scenario):
    # Terminate any background ow process
    if context.ow_process is not None:
        try:
            context.ow_process.terminate()
            context.ow_process.wait(timeout=5)
        except Exception:
            try:
                context.ow_process.kill()
            except Exception:
                pass
        context.ow_process = None

    # Stop mock HTTP server if running
    if context.mock_server is not None:
        context.mock_server.shutdown()
        context.mock_server = None

    # Remove all temp files
    shutil.rmtree(context.tmpdir, ignore_errors=True)
