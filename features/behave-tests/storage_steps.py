import os
import subprocess
from pathlib import Path

from behave import when, then


def _run_ow(context, args=None):
    result = subprocess.run(
        [context.ow] + (args or []),
        env=context.env,
        capture_output=True,
        text=True,
    )
    context.ow_result = result


def _read_xdg_file(work_dir, filename):
    with open(os.path.join(work_dir, filename)) as f:
        return f.read().strip()


@when("the user runs ow")
def step_run_ow(context):
    _run_ow(context)


@then("opencode receives XDG_DATA_HOME pointing to an ow-specific directory")
def step_xdg_data_home_ow_specific(context):
    value = _read_xdg_file(context.work_dir, "xdg_data_home.txt")
    assert value, "XDG_DATA_HOME was not set by ow"
    assert Path(value).name == "ow", (
        f"XDG_DATA_HOME {value!r} does not end with an ow-specific path component"
    )


@then("opencode receives XDG_CONFIG_HOME pointing to an ow-specific directory")
def step_xdg_config_home_ow_specific(context):
    value = _read_xdg_file(context.work_dir, "xdg_config_home.txt")
    assert value, "XDG_CONFIG_HOME was not set by ow"
    assert Path(value).name == "ow", (
        f"XDG_CONFIG_HOME {value!r} does not end with an ow-specific path component"
    )


@then("opencode receives XDG_CACHE_HOME pointing to an ow-specific directory")
def step_xdg_cache_home_ow_specific(context):
    value = _read_xdg_file(context.work_dir, "xdg_cache_home.txt")
    assert value, "XDG_CACHE_HOME was not set by ow"
    assert Path(value).name == "ow", (
        f"XDG_CACHE_HOME {value!r} does not end with an ow-specific path component"
    )


@then("opencode receives XDG_STATE_HOME pointing to an ow-specific directory")
def step_xdg_state_home_ow_specific(context):
    value = _read_xdg_file(context.work_dir, "xdg_state_home.txt")
    assert value, "XDG_STATE_HOME was not set by ow"
    assert Path(value).name == "ow", (
        f"XDG_STATE_HOME {value!r} does not end with an ow-specific path component"
    )


@then("opencode does not receive XDG_DATA_HOME pointing to the system default")
def step_xdg_data_home_not_system_default(context):
    value = _read_xdg_file(context.work_dir, "xdg_data_home.txt")
    assert value, (
        "XDG_DATA_HOME was empty — opencode would fall back to ~/.local/share "
        "and collide with stock opencode"
    )
    system_default = str(Path.home() / ".local" / "share")
    assert value != system_default, (
        f"XDG_DATA_HOME was the system default {value!r} — "
        "sessions would collide with stock opencode"
    )
