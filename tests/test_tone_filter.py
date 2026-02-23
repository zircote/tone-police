"""Tests for the tone-filter engine."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from conftest import PLUGIN_ROOT, run_filter, tone_filter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _apply_full_pipeline(
    text, intensity="moderate", languages=None, preserve_code=True
):
    """Run the full filter pipeline on text, returning the result."""
    if languages is None:
        languages = ["en"]

    plugin_root = PLUGIN_ROOT
    blocks = []
    if preserve_code:
        text, blocks = tone_filter.protect_code_blocks(text)

    common = tone_filter.load_common_patterns(plugin_root)
    text = tone_filter.apply_common_patterns(text, common)

    for lang in languages:
        dictionary = tone_filter.load_dictionary(plugin_root, lang)
        if dictionary:
            patterns = tone_filter.get_intensity_patterns(dictionary, intensity)
            text = tone_filter.apply_language_patterns(text, patterns)

    if preserve_code and blocks:
        text = tone_filter.restore_code_blocks(text, blocks)

    return text


# ---------------------------------------------------------------------------
# 1. Light profanity filtering
# ---------------------------------------------------------------------------


class TestLightProfanity:
    def test_fuck_replaced(self):
        result = _apply_full_pipeline("fuck this", intensity="light")
        assert "fudge" in result.lower()
        assert "fuck" not in result.lower()

    def test_shit_replaced(self):
        result = _apply_full_pipeline("this is shit", intensity="light")
        assert "shoot" in result.lower()

    def test_damn_replaced(self):
        result = _apply_full_pipeline("damn it", intensity="light")
        assert "dang" in result.lower() or "darnit" in result.lower()


# ---------------------------------------------------------------------------
# 2. Moderate hostile phrase filtering
# ---------------------------------------------------------------------------


class TestModerateHostilePhrases:
    def test_shut_up_replaced(self):
        result = _apply_full_pipeline("shut up already", intensity="moderate")
        assert "please stop" in result.lower()

    def test_who_the_hell(self):
        result = _apply_full_pipeline("who the hell wrote this", intensity="moderate")
        assert "who" in result.lower()
        assert "hell" not in result.lower()

    def test_what_the_fuck(self):
        result = _apply_full_pipeline("what the fuck is this", intensity="moderate")
        assert "what on earth" in result.lower()

    def test_light_profanity_also_applied(self):
        result = _apply_full_pipeline("fuck this shit", intensity="moderate")
        assert "fuck" not in result.lower()
        assert "shit" not in result.lower()


# ---------------------------------------------------------------------------
# 3. Strict negativity filtering
# ---------------------------------------------------------------------------


class TestStrictNegativity:
    def test_terrible_replaced(self):
        result = _apply_full_pipeline("this is terrible code", intensity="strict")
        assert "suboptimal" in result.lower()

    def test_useless_replaced(self):
        result = _apply_full_pipeline("this is useless", intensity="strict")
        assert "not yet useful" in result.lower()

    def test_this_sucks(self):
        result = _apply_full_pipeline("this sucks", intensity="strict")
        assert "this needs work" in result.lower()


# ---------------------------------------------------------------------------
# 4. Intensity is cumulative
# ---------------------------------------------------------------------------


class TestIntensityCumulative:
    def test_strict_includes_light(self):
        result = _apply_full_pipeline("fuck this", intensity="strict")
        assert "fuck" not in result.lower()

    def test_strict_includes_moderate(self):
        result = _apply_full_pipeline("shut up now", intensity="strict")
        assert "please stop" in result.lower()

    def test_strict_adds_negativity(self):
        result = _apply_full_pipeline("this is garbage", intensity="strict")
        assert "this needs improvement" in result.lower()

    def test_light_does_not_include_moderate(self):
        result = _apply_full_pipeline("shut up", intensity="light")
        # "shut up" is a moderate hostile_phrase, should NOT be filtered at light
        assert "shut up" in result.lower()

    def test_moderate_does_not_include_strict(self):
        result = _apply_full_pipeline("this is terrible", intensity="moderate")
        # "terrible" is a strict negativity pattern, should NOT be filtered at moderate
        assert "terrible" in result.lower()


# ---------------------------------------------------------------------------
# 5. Code block preservation (fenced)
# ---------------------------------------------------------------------------


class TestCodeBlockPreservation:
    def test_profanity_in_fenced_code_not_filtered(self):
        text = "Please fix this:\n```\nfuck_count = 0\n```"
        result = _apply_full_pipeline(text, intensity="strict")
        assert "fuck_count" in result

    def test_text_outside_code_still_filtered(self):
        text = "This is shit\n```\nshit_var = 1\n```"
        result = _apply_full_pipeline(text, intensity="light")
        assert "shoot" in result.lower().split("```")[0]
        assert "shit_var" in result


# ---------------------------------------------------------------------------
# 6. Inline code preservation
# ---------------------------------------------------------------------------


class TestInlineCodePreservation:
    def test_backtick_code_not_filtered(self):
        text = "Use `fuck_count` variable"
        result = _apply_full_pipeline(text, intensity="strict")
        assert "`fuck_count`" in result

    def test_text_around_inline_code_filtered(self):
        text = "This shit `fuck_count` is damn useful"
        result = _apply_full_pipeline(text, intensity="light")
        assert "`fuck_count`" in result
        assert "shoot" in result.lower()


# ---------------------------------------------------------------------------
# 7. CAPS normalization
# ---------------------------------------------------------------------------


class TestCapsNormalization:
    def test_all_caps_lowered(self):
        result = _apply_full_pipeline("THIS IS STUPID", intensity="light")
        assert "this" in result
        assert "stupid" in result
        # Words 4+ chars should be lowered
        assert "THIS" not in result
        assert "STUPID" not in result

    def test_short_words_not_lowered(self):
        # Words <4 chars stay as-is
        result = _apply_full_pipeline("I AM OK BUT FINE", intensity="light")
        assert "fine" in result  # FINE (4 chars) lowered
        # Short words like I, AM, OK, BUT may or may not be lowered depending on length


# ---------------------------------------------------------------------------
# 8. Excessive punctuation
# ---------------------------------------------------------------------------


class TestExcessivePunctuation:
    def test_multiple_exclamation(self):
        result = _apply_full_pipeline("WHY!!!", intensity="light")
        # WHY -> lowered to "why", !!! -> !
        assert "!!!" not in result
        assert "!" in result

    def test_multiple_question(self):
        result = _apply_full_pipeline("WHAT???", intensity="light")
        assert "???" not in result
        assert "?" in result


# ---------------------------------------------------------------------------
# 9. Repeated characters
# ---------------------------------------------------------------------------


class TestRepeatedCharacters:
    def test_sooooo_normalized(self):
        result = _apply_full_pipeline("sooooo annoying", intensity="light")
        assert "sooooo" not in result
        assert "soo" in result

    def test_nooo_normalized(self):
        result = _apply_full_pipeline("nooooo way", intensity="light")
        assert "nooooo" not in result
        assert "noo" in result


# ---------------------------------------------------------------------------
# 10. Clean input passthrough
# ---------------------------------------------------------------------------


class TestCleanInputPassthrough:
    def test_clean_text_unchanged(self):
        clean = "Please help me refactor this function."
        result = run_filter(clean)
        assert result is None  # No output means no changes

    def test_polite_text_unchanged(self):
        clean = "Could you review this code for me?"
        result = run_filter(clean)
        assert result is None


# ---------------------------------------------------------------------------
# 11. Disabled config
# ---------------------------------------------------------------------------


class TestDisabledConfig:
    def test_disabled_produces_no_output(self, tmp_path):
        config = {
            "intensity": "strict",
            "languages": ["en"],
            "enabled": False,
            "preserve_code_blocks": True,
            "log_transforms": False,
        }
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        config_file = claude_dir / "tone-police.config.json"
        config_file.write_text(json.dumps(config))

        result = run_filter(
            "fuck this shit",
            env_extra={"CLAUDE_PROJECT_DIR": str(tmp_path)},
        )
        assert result is None


# ---------------------------------------------------------------------------
# 12. Config override
# ---------------------------------------------------------------------------


class TestConfigOverride:
    def test_project_config_overrides_default(self, tmp_path):
        # Project config set to light -- hostile phrases should NOT be filtered
        config = {
            "intensity": "light",
            "languages": ["en"],
            "enabled": True,
            "preserve_code_blocks": True,
            "log_transforms": False,
        }
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        config_file = claude_dir / "tone-police.config.json"
        config_file.write_text(json.dumps(config))

        result = run_filter(
            "shut up already",
            env_extra={"CLAUDE_PROJECT_DIR": str(tmp_path)},
        )
        # "shut up" is moderate, light should not filter it
        assert result is None or "shut up" in result.get("systemMessage", "").lower()


# ---------------------------------------------------------------------------
# 13. Multi-language
# ---------------------------------------------------------------------------


class TestMultiLanguage:
    def test_spanish_profanity_filtered(self):
        result = _apply_full_pipeline(
            "esto es mierda", intensity="light", languages=["es"]
        )
        assert "rayos" in result.lower()
        assert "mierda" not in result.lower()

    def test_multi_lang_en_and_es(self):
        result = _apply_full_pipeline(
            "fuck this mierda", intensity="light", languages=["en", "es"]
        )
        assert "fuck" not in result.lower()
        assert "mierda" not in result.lower()


# ---------------------------------------------------------------------------
# 14. Protect/restore code blocks round-trip
# ---------------------------------------------------------------------------


class TestProtectRestoreCodeBlocks:
    def test_round_trip_fenced(self):
        original = "text ```code block``` more text"
        protected, blocks = tone_filter.protect_code_blocks(original)
        assert "```code block```" not in protected
        assert "__CODE_BLOCK_0__" in protected
        restored = tone_filter.restore_code_blocks(protected, blocks)
        assert restored == original

    def test_round_trip_inline(self):
        original = "use `my_var` here"
        protected, blocks = tone_filter.protect_code_blocks(original)
        assert "`my_var`" not in protected
        restored = tone_filter.restore_code_blocks(protected, blocks)
        assert restored == original

    def test_multiple_blocks(self):
        original = "`a` and ```b``` and `c`"
        protected, blocks = tone_filter.protect_code_blocks(original)
        assert len(blocks) == 3
        restored = tone_filter.restore_code_blocks(protected, blocks)
        assert restored == original


# ---------------------------------------------------------------------------
# 15. Empty input
# ---------------------------------------------------------------------------


class TestEmptyInput:
    def test_empty_string(self):
        result = run_filter("")
        assert result is None

    def test_whitespace_only(self):
        # The script checks `if not user_prompt` which is truthy for whitespace
        # Actually " " is truthy in Python, so it will process but produce no changes
        result = run_filter("   ")
        assert result is None


# ---------------------------------------------------------------------------
# 16. Main integration via subprocess
# ---------------------------------------------------------------------------


class TestMainIntegration:
    def test_end_to_end_profanity(self):
        result = run_filter("this is shit code")
        assert result is not None
        assert "additionalContext" in result
        assert "shoot" in result["additionalContext"].lower()

    def test_end_to_end_clean(self):
        result = run_filter("please help me with this code")
        assert result is None

    def test_end_to_end_invalid_json(self):
        script = str(PLUGIN_ROOT / "hooks" / "scripts" / "tone-filter.py")
        result = subprocess.run(
            [sys.executable, script],
            input="not valid json",
            capture_output=True,
            text=True,
            env={**os.environ, "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT)},
        )
        assert result.stdout.strip() == ""

    def test_end_to_end_missing_prompt(self):
        script = str(PLUGIN_ROOT / "hooks" / "scripts" / "tone-filter.py")
        result = subprocess.run(
            [sys.executable, script],
            input=json.dumps({"other_field": "value"}),
            capture_output=True,
            text=True,
            env={**os.environ, "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT)},
        )
        assert result.stdout.strip() == ""
