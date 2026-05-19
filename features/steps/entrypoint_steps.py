import os
import signal
import stat
import subprocess
import time

from behave import given, when, then


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_ow(context, args, stdin_data=None):
    """Run ow synchronously and store the CompletedProcess in context."""
    result = subprocess.run(
        [context.ow] + args,
        env=context.env,
        input=stdin_data,
        capture_output=True,
        text=True,
    )
    context.ow_result = result


def _start_ow_background(context, args=None):
    """Start ow as a background process and store the Popen in context."""
    context.ow_process = subprocess.Popen(
        [context.ow] + (args or ["--stay-alive"]),
        env=context.env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _wait_for_file(path, timeout=5.0, poll=0.05):
    """Poll until a file exists and is non-empty, or raise TimeoutError."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return
        time.sleep(poll)
    raise TimeoutError(f"File never appeared or stayed empty: {path}")


def _make_user_opencode(context, path):
    """Create a fake opencode at an arbitrary path with identity 'user'."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    script = (
        "#!/bin/bash\n"
        f"echo user > \"{context.work_dir}/invoked_by.txt\"\n"
        f"exit 0\n"
    )
    with open(path, "w") as f:
        f.write(script)
    os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)


# ---------------------------------------------------------------------------
# Scenario: ow passes arguments through to opencode
# ---------------------------------------------------------------------------

@when('the user runs "ow <subcommand> [args]"')
def step_run_ow_with_subcommand_and_args(context):
    _run_ow(context, ["mysubcommand", "arg1", "arg2"])


@then("the bundled opencode receives the same subcommand and args")
def step_bundled_opencode_receives_args(context):
    argv_file = os.path.join(context.work_dir, "argv.txt")
    with open(argv_file) as f:
        received = f.read().strip()
    assert received == "mysubcommand arg1 arg2", (
        f"Expected 'mysubcommand arg1 arg2', got {received!r}"
    )


# ---------------------------------------------------------------------------
# Scenario: ow uses its bundled opencode, not the user's
# ---------------------------------------------------------------------------

@given('the user has their own opencode at "/usr/local/bin/opencode"')
def step_user_has_own_opencode(context):
    # We simulate the user's opencode at a path we control, then prepend it to PATH.
    context.user_opencode_dir = os.path.join(context.tmpdir, "user_bin")
    context.user_opencode_path = os.path.join(context.user_opencode_dir, "opencode")
    _make_user_opencode(context, context.user_opencode_path)
    context.env["PATH"] = context.user_opencode_dir + os.pathsep + context.env.get("PATH", "")


@when("the user runs any ow command")
def step_run_ow_any_command(context):
    _run_ow(context, ["some-command"])


@then('the bundled opencode is invoked, not the one at "/usr/local/bin/opencode"')
def step_bundled_invoked_not_user(context):
    invoked_file = os.path.join(context.work_dir, "invoked_by.txt")
    with open(invoked_file) as f:
        identity = f.read().strip()
    assert identity == "bundled", (
        f"Expected bundled opencode to be invoked, but got identity={identity!r}"
    )


# ---------------------------------------------------------------------------
# Scenario: ow propagates opencode's exit code
# ---------------------------------------------------------------------------

@when("the bundled opencode exits with a non-zero code")
def step_opencode_exits_nonzero(context):
    context.env["FAKE_OPENCODE_EXIT_CODE"] = "42"
    _run_ow(context, [])


@then("ow exits with the same code")
def step_ow_exits_same_code(context):
    assert context.ow_result.returncode == 42, (
        f"Expected exit code 42, got {context.ow_result.returncode}"
    )


# ---------------------------------------------------------------------------
# Scenario: ow passes stdout through from opencode
# ---------------------------------------------------------------------------

@when("opencode writes to stdout")
def step_opencode_writes_stdout(context):
    context.env["FAKE_OPENCODE_STDOUT"] = "hello from opencode stdout"
    _run_ow(context, [])


@then("ow's stdout contains the same output")
def step_ow_stdout_contains_output(context):
    assert "hello from opencode stdout" in context.ow_result.stdout, (
        f"stdout was: {context.ow_result.stdout!r}"
    )


# ---------------------------------------------------------------------------
# Scenario: ow passes stderr through from opencode
# ---------------------------------------------------------------------------

@when("opencode writes to stderr")
def step_opencode_writes_stderr(context):
    context.env["FAKE_OPENCODE_STDERR"] = "hello from opencode stderr"
    _run_ow(context, [])


@then("ow's stderr contains the same output")
def step_ow_stderr_contains_output(context):
    assert "hello from opencode stderr" in context.ow_result.stderr, (
        f"stderr was: {context.ow_result.stderr!r}"
    )


# ---------------------------------------------------------------------------
# Scenario: ow passes stdin through to opencode
# ---------------------------------------------------------------------------

@when("the user provides input on stdin")
def step_user_provides_stdin(context):
    context.env["FAKE_OPENCODE_READ_STDIN"] = "1"
    _run_ow(context, [], stdin_data="test input from user\n")


@then("opencode receives that input")
def step_opencode_receives_stdin(context):
    stdin_file = os.path.join(context.work_dir, "stdin.txt")
    with open(stdin_file) as f:
        received = f.read()
    assert "test input from user" in received, (
        f"stdin.txt contained: {received!r}"
    )


# ---------------------------------------------------------------------------
# Scenario: ow forwards SIGINT / SIGTERM / SIGWINCH to opencode
# ---------------------------------------------------------------------------

@given("opencode is running under ow")
def step_opencode_running_under_ow(context):
    context.env["FAKE_OPENCODE_CATCH_SIGNALS"] = "1"
    _start_ow_background(context)
    # Wait until fake opencode writes its PID (signals it is ready)
    pid_file = os.path.join(context.work_dir, "opencode.pid")
    _wait_for_file(pid_file, timeout=10)


@when("the user sends SIGINT")
def step_send_sigint(context):
    os.kill(context.ow_process.pid, signal.SIGINT)


@then("opencode receives SIGINT")
def step_opencode_receives_sigint(context):
    signals_file = os.path.join(context.work_dir, "signals.txt")
    _wait_for_file(signals_file, timeout=5)
    with open(signals_file) as f:
        content = f.read()
    assert "SIGINT" in content, f"signals.txt: {content!r}"


@when("the user sends SIGTERM")
def step_send_sigterm(context):
    os.kill(context.ow_process.pid, signal.SIGTERM)


@then("opencode receives SIGTERM")
def step_opencode_receives_sigterm(context):
    signals_file = os.path.join(context.work_dir, "signals.txt")
    _wait_for_file(signals_file, timeout=5)
    with open(signals_file) as f:
        content = f.read()
    assert "SIGTERM" in content, f"signals.txt: {content!r}"


@when("the terminal is resized")
def step_terminal_resized(context):
    os.kill(context.ow_process.pid, signal.SIGWINCH)


@then("opencode receives SIGWINCH")
def step_opencode_receives_sigwinch(context):
    signals_file = os.path.join(context.work_dir, "signals.txt")
    _wait_for_file(signals_file, timeout=5)
    with open(signals_file) as f:
        content = f.read()
    assert "SIGWINCH" in content, f"signals.txt: {content!r}"


# ---------------------------------------------------------------------------
# Scenario: ow --version shows ow's version and the bundled opencode version
# ---------------------------------------------------------------------------

@when('the user runs "ow --version"')
def step_run_ow_version(context):
    context.env["FAKE_OPENCODE_VERSION"] = "9.8.7-opencode-fake"
    _run_ow(context, ["--version"])


@then("the output includes the ow version")
def step_output_includes_ow_version(context):
    output = context.ow_result.stdout + context.ow_result.stderr
    assert "ow" in output.lower(), f"ow version not found in output: {output!r}"


@then("the output includes the bundled opencode version")
def step_output_includes_opencode_version(context):
    output = context.ow_result.stdout + context.ow_result.stderr
    assert "9.8.7-opencode-fake" in output, (
        f"opencode version not found in output: {output!r}"
    )
