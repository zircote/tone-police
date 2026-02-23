"""Shared fixtures for tone-police tests."""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).parent.parent


def _load_tone_filter_module():
    """Import tone-filter.py despite the hyphen in the filename."""
    spec = importlib.util.spec_from_file_location(
        "tone_filter",
        PLUGIN_ROOT / "hooks" / "scripts" / "tone-filter.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


tone_filter = _load_tone_filter_module()


@pytest.fixture
def plugin_root():
    """Return the absolute path to the plugin root directory."""
    return PLUGIN_ROOT


@pytest.fixture
def default_config():
    """Load and return the default configuration."""
    with open(PLUGIN_ROOT / "config" / "default-config.json") as f:
        return json.load(f)


@pytest.fixture
def tmp_config_dir(tmp_path):
    """Create a temporary directory mimicking a project .claude dir with config."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    return claude_dir


@pytest.fixture
def en_dictionary(plugin_root):
    """Load the English dictionary."""
    return tone_filter.load_dictionary(plugin_root, "en")


@pytest.fixture
def common_patterns(plugin_root):
    """Load common patterns."""
    return tone_filter.load_common_patterns(plugin_root)


def run_filter(user_prompt, config_override=None, env_extra=None):
    """Run the tone-filter.py script via subprocess and return parsed output.

    Args:
        user_prompt: The user prompt text to filter.
        config_override: If provided, written to a temp project config file.
        env_extra: Extra environment variables to set.

    Returns:
        Parsed JSON dict if the filter produced output, else None.
    """
    script = str(PLUGIN_ROOT / "hooks" / "scripts" / "tone-filter.py")
    input_data = json.dumps({"user_prompt": user_prompt})

    env = os.environ.copy()
    env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    if env_extra:
        env.update(env_extra)

    result = subprocess.run(
        [sys.executable, script],
        input=input_data,
        capture_output=True,
        text=True,
        env=env,
    )

    if result.stdout.strip():
        return json.loads(result.stdout.strip())
    return None
