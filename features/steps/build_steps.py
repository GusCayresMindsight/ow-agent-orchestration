import os
import re
import subprocess

from behave import given, then

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# ---------------------------------------------------------------------------
# Shared setup
# ---------------------------------------------------------------------------

@given("the ow-agent-orchestration repository is checked out")
def step_repo_checked_out(context):
    context.repo_root = _REPO_ROOT


# ---------------------------------------------------------------------------
# Repository structure
# ---------------------------------------------------------------------------

@then("the directory {path} exists")
def step_directory_exists(context, path):
    full = os.path.join(context.repo_root, path)
    assert os.path.isdir(full), f"Expected directory to exist: {full}"


@then("the file {path} exists")
def step_file_exists(context, path):
    full = os.path.join(context.repo_root, path)
    assert os.path.isfile(full), f"Expected file to exist: {full}"


# ---------------------------------------------------------------------------
# Logo patch — logo.ts
# ---------------------------------------------------------------------------

_LOGO_HALF_RE = re.compile(r'(left|right)\s*:\s*\[([^\]]+)\]')
_QUOTED_STR_RE = re.compile(r'"([^"]*)"')


@then('opencode/packages/opencode/src/cli/logo.ts defines a logo with two halves named "left" and "right"')
def step_logo_has_two_halves(context):
    logo_ts = os.path.join(
        context.repo_root,
        "opencode", "packages", "opencode", "src", "cli", "logo.ts",
    )
    content = open(logo_ts, encoding="utf-8").read()
    halves = {
        m.group(1): _QUOTED_STR_RE.findall(m.group(2))
        for m in _LOGO_HALF_RE.finditer(content)
    }
    assert "left" in halves, "logo.ts: 'left' half not found in logo constant"
    assert "right" in halves, "logo.ts: 'right' half not found in logo constant"
    context.logo_left = halves["left"]
    context.logo_right = halves["right"]


@then("each half has exactly 4 rows")
def step_each_half_has_4_rows(context):
    assert len(context.logo_left) == 4, \
        f"logo.left has {len(context.logo_left)} rows, expected 4"
    assert len(context.logo_right) == 4, \
        f"logo.right has {len(context.logo_right)} rows, expected 4"


@then("no row in either half is wider than 8 characters")
def step_no_row_wider_than_8(context):
    for row in context.logo_left + context.logo_right:
        assert len(row) <= 8, \
            f"Row {row!r} is {len(row)} chars wide — too wide for a 2-letter logo (max 8)"


# ---------------------------------------------------------------------------
# Logo patch — ui.ts wordmark
# ---------------------------------------------------------------------------

_WORDMARK_RE = re.compile(r'const wordmark\s*=\s*\[([^\]]+)\]', re.DOTALL)


@then('opencode/packages/opencode/src/cli/ui.ts defines a wordmark that reads "ow"')
def step_wordmark_reads_ow(context):
    ui_ts = os.path.join(
        context.repo_root,
        "opencode", "packages", "opencode", "src", "cli", "ui.ts",
    )
    content = open(ui_ts, encoding="utf-8").read()
    match = _WORDMARK_RE.search(content)
    assert match, "ui.ts: 'wordmark' constant not found"
    rows = _QUOTED_STR_RE.findall(match.group(1))
    assert rows, "ui.ts: wordmark has no rows"
    # "opencode" wordmark rows were ~41 chars wide; "ow" must be much narrower
    max_width = max(len(r) for r in rows)
    assert max_width <= 20, (
        f"Wordmark max row width is {max_width} chars — "
        f"expected ≤ 20 for a 2-letter 'ow' wordmark"
    )


# ---------------------------------------------------------------------------
# Git history shape
# ---------------------------------------------------------------------------

@given("the git log of the opencode/ prefix")
def step_git_log_opencode(context):
    result = subprocess.run(
        ["git", "log", "--oneline", "--", "opencode/"],
        capture_output=True,
        text=True,
        cwd=_REPO_ROOT,
    )
    assert result.returncode == 0, f"git log failed: {result.stderr}"
    commits = result.stdout.strip().splitlines()
    assert commits, "No commits found touching opencode/"
    # Reverse so oldest is first
    context.opencode_commits = list(reversed(commits))


@then("the oldest commit touching opencode/ is a squash of the upstream source")
def step_oldest_is_squash(context):
    oldest_msg = context.opencode_commits[0].split(" ", 1)[-1]
    assert "as 'opencode'" in oldest_msg, (
        f"Expected oldest opencode/ commit to be a git subtree merge "
        f"(containing \"as 'opencode'\"), got: {oldest_msg!r}"
    )


@then("at least one subsequent commit to opencode/ carries an ow-specific patch message")
def step_subsequent_has_ow_patch(context):
    subsequent = context.opencode_commits[1:]
    assert subsequent, "No commits found after the initial subtree squash"
    assert any("patch:" in c or "ow" in c.lower() for c in subsequent), (
        f"No ow-specific patch commit found among subsequent commits: {subsequent}"
    )


# ---------------------------------------------------------------------------
# Release workflow
# ---------------------------------------------------------------------------

@given("the release workflow at .github/workflows/release.yml")
def step_load_release_workflow(context):
    workflow_path = os.path.join(_REPO_ROOT, ".github", "workflows", "release.yml")
    assert os.path.isfile(workflow_path), f"release.yml not found at {workflow_path}"
    with open(workflow_path, encoding="utf-8") as f:
        context.release_workflow = f.read()


@then("it installs dependencies from opencode/")
def step_workflow_installs_from_opencode(context):
    assert "working-directory: opencode" in context.release_workflow, \
        "release.yml: no step with 'working-directory: opencode' found"
    assert "bun install" in context.release_workflow, \
        "release.yml: 'bun install' command not found"


@then("it runs the build script at opencode/packages/opencode/script/build.ts")
def step_workflow_runs_build_script(context):
    assert "script/build.ts" in context.release_workflow, \
        "release.yml: 'script/build.ts' reference not found"


@then("it uploads the resulting opencode-linux-x64.tar.gz as a release asset")
def step_workflow_uploads_tarball(context):
    assert "opencode-linux-x64.tar.gz" in context.release_workflow, \
        "release.yml: 'opencode-linux-x64.tar.gz' not referenced"


@then("it does not download a pre-built binary from any external URL")
def step_workflow_no_download(context):
    hits = re.findall(r'(?:curl|wget)[^\n]*opencode', context.release_workflow)
    assert not hits, (
        f"release.yml appears to download a pre-built opencode binary: {hits}"
    )
