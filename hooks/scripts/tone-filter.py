#!/usr/bin/env python3
"""Tone Police - Filters hostile/profane language from user prompts."""

import json
import os
import re
import sys
from pathlib import Path


def load_config():
    """Load config, checking project override first, then plugin default."""
    plugin_root = Path(
        os.environ.get("CLAUDE_PLUGIN_ROOT", Path(__file__).parent.parent.parent)
    )
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")

    # Check for project-level override
    if project_dir:
        override = Path(project_dir) / ".claude" / "tone-police.config.json"
        if override.exists():
            with open(override) as f:
                return json.load(f), plugin_root

    # Fall back to default config
    default = plugin_root / "config" / "default-config.json"
    if default.exists():
        with open(default) as f:
            return json.load(f), plugin_root

    # Hardcoded fallback
    return {
        "intensity": "moderate",
        "languages": ["en"],
        "enabled": True,
        "preserve_code_blocks": True,
        "log_transforms": False,
    }, plugin_root


def load_dictionary(plugin_root, language):
    """Load a language dictionary file."""
    dict_path = plugin_root / "dictionaries" / f"{language}.json"
    if dict_path.exists():
        with open(dict_path) as f:
            return json.load(f)
    return None


def load_common_patterns(plugin_root):
    """Load cross-language common patterns."""
    path = plugin_root / "dictionaries" / "common-patterns.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def protect_code_blocks(text):
    """Extract and replace code blocks with placeholders."""
    blocks = []
    pattern = re.compile(r"(```[\s\S]*?```|`[^`\n]+`)")

    def replacer(match):
        blocks.append(match.group(0))
        return f"__CODE_BLOCK_{len(blocks) - 1}__"

    protected = pattern.sub(replacer, text)
    return protected, blocks


def restore_code_blocks(text, blocks):
    """Restore code blocks from placeholders."""
    for i, block in enumerate(blocks):
        text = text.replace(f"__CODE_BLOCK_{i}__", block)
    return text


def get_intensity_patterns(dictionary, intensity):
    """Get cumulative patterns for the given intensity level."""
    patterns_by_category = {}
    levels = ["light", "moderate", "strict"]
    target_idx = levels.index(intensity) if intensity in levels else 1

    for level in levels[: target_idx + 1]:
        level_patterns = dictionary.get("patterns", {}).get(level, {})
        for category, pattern_list in level_patterns.items():
            if category not in patterns_by_category:
                patterns_by_category[category] = []
            patterns_by_category[category].extend(pattern_list)

    return patterns_by_category


def apply_common_patterns(text, common):
    """Apply cross-language normalization patterns."""
    if not common:
        return text

    patterns = common.get("patterns", {})

    # ALL CAPS normalization (4+ chars)
    caps_config = patterns.get("caps_normalization", {})
    if caps_config:
        caps_pattern = caps_config.get("pattern", r"\b([A-Z]{4,})\b")
        text = re.sub(caps_pattern, lambda m: m.group(0).lower(), text)

    # Excessive punctuation
    punct_config = patterns.get("excessive_punctuation", {})
    if punct_config:
        for p in punct_config.get("patterns", []):
            text = re.sub(p["pattern"], p["replacement"], text)

    # Repeated characters
    repeat_config = patterns.get("repeated_characters", {})
    if repeat_config:
        text = re.sub(
            repeat_config.get("pattern", r"(\w)\1{2,}"),
            repeat_config.get("replacement", r"\1\1"),
            text,
        )

    return text


def apply_language_patterns(text, patterns_by_category):
    """Apply language-specific replacement patterns."""
    for category, pattern_list in patterns_by_category.items():
        for entry in pattern_list:
            regex = entry["pattern"]
            replacement = entry["replacement"]
            flags = re.IGNORECASE if "i" in entry.get("flags", "i") else 0
            text = re.sub(regex, replacement, text, flags=flags)
    return text


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    user_prompt = input_data.get("user_prompt", "")
    if not user_prompt:
        sys.exit(0)

    try:
        config, plugin_root = load_config()
    except Exception:
        sys.exit(0)

    if not config.get("enabled", True):
        sys.exit(0)

    intensity = config.get("intensity", "moderate")
    languages = config.get("languages", ["en"])
    preserve_code = config.get("preserve_code_blocks", True)

    text = user_prompt

    # Protect code blocks
    blocks = []
    if preserve_code:
        text, blocks = protect_code_blocks(text)

    # Apply common patterns
    common = load_common_patterns(plugin_root)
    text = apply_common_patterns(text, common)

    # Apply language-specific patterns
    for lang in languages:
        dictionary = load_dictionary(plugin_root, lang)
        if dictionary:
            patterns = get_intensity_patterns(dictionary, intensity)
            text = apply_language_patterns(text, patterns)

    # Restore code blocks
    if preserve_code and blocks:
        text = restore_code_blocks(text, blocks)

    # Output only if text was modified
    if text != user_prompt:
        result = {
            "systemMessage": f"Note: the user's message has been adjusted for tone. Original intent preserved. Adjusted prompt: {text}"
        }
        print(json.dumps(result))

    sys.exit(0)


if __name__ == "__main__":
    main()
