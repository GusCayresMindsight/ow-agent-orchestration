import http.server
import os
import platform
import shutil
import stat
import subprocess
import tarfile
import tempfile
import threading

from behave import given, when, then

# Path to the install script and project root
_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
_INSTALL_SCRIPT = os.path.join(_REPO_ROOT, "scripts", "install.sh")

# Fake opencode binary content for the mock tarball
_FAKE_OPENCODE_SCRIPT = "#!/bin/bash\necho 'opencode 0.0.0-fake'\n"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _arch_suffix() -> str:
    """Return the opencode architecture string for the current machine."""
    machine = platform.machine()
    return "arm64" if machine == "aarch64" else "x64"


def _start_mock_server(context):
    """
    Start a local HTTP server serving context.tmpdir/serve/.

    The serve directory is populated with a fake opencode tarball so the
    install script can download it without hitting the real GitHub Releases.
    """
    serve_dir = os.path.join(context.tmpdir, "serve")
    os.makedirs(serve_dir, exist_ok=True)

    # Write the fake opencode binary
    fake_oc_bin = os.path.join(serve_dir, "opencode")
    with open(fake_oc_bin, "w") as f:
        f.write(_FAKE_OPENCODE_SCRIPT)
    os.chmod(fake_oc_bin, os.stat(fake_oc_bin).st_mode | stat.S_IEXEC)

    # Pack it into the tarball the install script expects
    arch = _arch_suffix()
    tarball_name = f"opencode-linux-{arch}.tar.gz"
    tarball_path = os.path.join(serve_dir, tarball_name)
    with tarfile.open(tarball_path, "w:gz") as tf:
        tf.add(fake_oc_bin, arcname="opencode")

    class _Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=serve_dir, **kwargs)

        def log_message(self, fmt, *args):  # silence request logging
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    context.mock_server = server
    context.mock_server_thread = thread
    context.mock_server_url = f"http://127.0.0.1:{port}"


def _run_install(context):
    """
    Run scripts/install.sh in an isolated HOME, mocking external downloads.

    OW_PACKAGE        points to the local project directory so uv installs
                      from source without reaching PyPI.
    OW_OPENCODE_BASE_URL  points to the mock HTTP server for the opencode
                      tarball.
    HOME              is set to context.fake_home for full isolation.
    """
    if context.mock_server is None:
        _start_mock_server(context)

    env = os.environ.copy()
    env["HOME"] = context.fake_home
    env["OW_PACKAGE"] = _REPO_ROOT          # install from local source
    env["OW_OPENCODE_BASE_URL"] = context.mock_server_url

    result = subprocess.run(
        ["bash", _INSTALL_SCRIPT],
        env=env,
        capture_output=True,
        text=True,
    )
    context.install_result = result


# ---------------------------------------------------------------------------
# Background
# ---------------------------------------------------------------------------

@given("curl and bash are available on the system")
def step_curl_and_bash_available(context):
    missing = [cmd for cmd in ("curl", "bash", "uv") if shutil.which(cmd) is None]
    if missing:
        context.scenario.skip(f"Required tools not found: {', '.join(missing)}")


# ---------------------------------------------------------------------------
# Scenario: The ow command becomes available after install
# ---------------------------------------------------------------------------

@given("the ow command is not installed")
def step_ow_not_installed(context):
    ow_path = os.path.join(context.fake_home, ".local", "bin", "ow")
    if os.path.exists(ow_path):
        os.remove(ow_path)


@when("the user runs the install script")
def step_run_install_script(context):
    _run_install(context)


@then("the ow command is available at ~/.local/bin/ow")
def step_ow_available(context):
    ow_path = os.path.join(context.fake_home, ".local", "bin", "ow")
    assert os.path.isfile(ow_path), (
        f"ow not found at {ow_path}\n"
        f"stdout: {context.install_result.stdout}\n"
        f"stderr: {context.install_result.stderr}"
    )
    assert os.access(ow_path, os.X_OK), f"ow at {ow_path} is not executable"


# ---------------------------------------------------------------------------
# Scenario: The install script does not expose opencode to the PATH
# ---------------------------------------------------------------------------

@then("the opencode command is not added to the PATH")
def step_opencode_not_in_path(context):
    local_bin = os.path.join(context.fake_home, ".local", "bin")
    opencode_path = os.path.join(local_bin, "opencode")
    assert not os.path.exists(opencode_path), (
        f"opencode was unexpectedly placed at {opencode_path}"
    )


# ---------------------------------------------------------------------------
# Scenario: The install does not affect an existing opencode installation
# ---------------------------------------------------------------------------

@given('the user has their own opencode installed at "/usr/local/bin/opencode"')
def step_user_has_system_opencode(context):
    # Simulate a system opencode at a path we fully control.
    user_bin = os.path.join(context.tmpdir, "user_system_bin")
    os.makedirs(user_bin, exist_ok=True)
    context.existing_opencode = os.path.join(user_bin, "opencode")
    sentinel_content = "#!/bin/bash\necho 'original opencode'\n"
    with open(context.existing_opencode, "w") as f:
        f.write(sentinel_content)
    os.chmod(context.existing_opencode, os.stat(context.existing_opencode).st_mode | stat.S_IEXEC)
    context.existing_opencode_mtime = os.path.getmtime(context.existing_opencode)
    context.existing_opencode_content = sentinel_content


@then('"/usr/local/bin/opencode" is unchanged')
def step_existing_opencode_unchanged(context):
    current_mtime = os.path.getmtime(context.existing_opencode)
    with open(context.existing_opencode) as f:
        current_content = f.read()
    assert current_mtime == context.existing_opencode_mtime, (
        "Existing opencode mtime changed — install script may have touched it"
    )
    assert current_content == context.existing_opencode_content, (
        "Existing opencode content changed — install script modified it"
    )


# ---------------------------------------------------------------------------
# Scenario: Install is idempotent
# ---------------------------------------------------------------------------

@given("the ow command is already installed")
def step_ow_already_installed(context):
    _run_install(context)
    ow_path = os.path.join(context.fake_home, ".local", "bin", "ow")
    assert os.path.isfile(ow_path), (
        f"Pre-condition failed: first install did not create ow\n"
        f"stdout: {context.install_result.stdout}\n"
        f"stderr: {context.install_result.stderr}"
    )


@when("the user runs the install script again")
def step_run_install_script_again(context):
    _run_install(context)


@then("the command exits successfully")
def step_install_exits_successfully(context):
    assert context.install_result.returncode == 0, (
        f"Install exited with code {context.install_result.returncode}\n"
        f"stdout: {context.install_result.stdout}\n"
        f"stderr: {context.install_result.stderr}"
    )


@then("the ow command still works")
def step_ow_still_works(context):
    ow_path = os.path.join(context.fake_home, ".local", "bin", "ow")
    assert os.path.isfile(ow_path), f"ow not found at {ow_path} after second install"
    assert os.access(ow_path, os.X_OK), f"ow at {ow_path} is not executable after second install"
