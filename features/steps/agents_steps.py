import os
from pathlib import Path

from behave import given, then


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _agents_dir(context):
    """Return the path where ow writes built-in agents (inside the fake home).

    Mirrors the XDG_CONFIG_HOME override in _ow_xdg_env():
      XDG_CONFIG_HOME = {home}/.config/ow
      agents dir      = {XDG_CONFIG_HOME}/opencode/agents
    """
    return Path(context.fake_home) / ".config" / "ow" / "opencode" / "agents"


def _read_test_agent(context):
    """Read the test.md file written by ow, asserting it exists first."""
    test_md = _agents_dir(context) / "test.md"
    assert test_md.exists(), (
        f"test.md not found at {test_md}\n"
        f"ow exit code: {context.ow_result.returncode}\n"
        f"ow stderr: {context.ow_result.stderr!r}"
    )
    return test_md.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Background
# ---------------------------------------------------------------------------

@given("ow is installed")
def step_ow_is_installed(context):
    assert context.ow is not None and os.path.isfile(context.ow), (
        "ow binary not found — is the package installed in the venv?"
    )
    # Redirect ow's HOME to the per-scenario fake home so built-in agents
    # are written there and not into the real user home.
    context.env["HOME"] = context.fake_home


# ---------------------------------------------------------------------------
# Scenario: ow writes the test agent definition into the ow config directory
# ---------------------------------------------------------------------------

@then('a "test.md" agent file exists under the ow opencode config agents directory')
def step_test_agent_file_exists(context):
    _read_test_agent(context)  # asserts existence


# ---------------------------------------------------------------------------
# Scenario: The test agent is configured as a primary agent
# ---------------------------------------------------------------------------

@then('the test agent config declares mode "primary"')
def step_test_agent_mode_primary(context):
    content = _read_test_agent(context)
    assert "mode: primary" in content, (
        f"'mode: primary' not found in test.md:\n{content}"
    )


# ---------------------------------------------------------------------------
# Scenario: The test agent requires confirmation before editing files
# ---------------------------------------------------------------------------

@then('the test agent config sets edit permission to "ask"')
def step_test_agent_edit_ask(context):
    content = _read_test_agent(context)
    assert "edit: ask" in content, (
        f"'edit: ask' not found in test.md:\n{content}"
    )


# ---------------------------------------------------------------------------
# Scenario: The test agent requires confirmation before running shell commands
# ---------------------------------------------------------------------------

@then('the test agent config sets bash permission to "ask"')
def step_test_agent_bash_ask(context):
    content = _read_test_agent(context)
    assert "bash: ask" in content, (
        f"'bash: ask' not found in test.md:\n{content}"
    )


# ---------------------------------------------------------------------------
# Scenario: The test agent definition is refreshed on every ow invocation
# ---------------------------------------------------------------------------

_STALE_CONTENT = "STALE_AGENT_CONTENT_DO_NOT_SHIP"


@given('a stale "test.md" exists under the ow opencode config agents directory')
def step_stale_test_agent_exists(context):
    agents_dir = _agents_dir(context)
    agents_dir.mkdir(parents=True, exist_ok=True)
    (agents_dir / "test.md").write_text(_STALE_CONTENT, encoding="utf-8")


@then("the stale content is replaced with the current bundled agent definition")
def step_stale_content_replaced(context):
    content = _read_test_agent(context)
    assert _STALE_CONTENT not in content, (
        "test.md still contains stale content — ow did not overwrite it"
    )
    assert "mode: primary" in content, (
        f"test.md was overwritten but lacks 'mode: primary':\n{content}"
    )
