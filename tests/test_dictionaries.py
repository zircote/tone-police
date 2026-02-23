"""Tests for dictionary file integrity and structure."""

import json
import re
from pathlib import Path

import pytest

DICTIONARIES_DIR = Path(__file__).parent.parent / "dictionaries"


def _load_all_json_files():
    """Return list of (path, data) for all JSON files in dictionaries/."""
    results = []
    for p in sorted(DICTIONARIES_DIR.glob("*.json")):
        with open(p) as f:
            results.append((p, json.load(f)))
    return results


def _language_dicts():
    """Return only language dictionary files (excluding common-patterns)."""
    return [
        (p, d) for p, d in _load_all_json_files() if p.name != "common-patterns.json"
    ]


# ---------------------------------------------------------------------------
# 1. All JSON files parse
# ---------------------------------------------------------------------------


class TestJsonParsing:
    def test_all_json_files_parse(self):
        for path in sorted(DICTIONARIES_DIR.glob("*.json")):
            with open(path) as f:
                data = json.load(f)
            assert isinstance(data, dict), f"{path.name} did not parse as a dict"


# ---------------------------------------------------------------------------
# 2. All regex patterns compile
# ---------------------------------------------------------------------------


class TestRegexCompilation:
    def test_all_regex_patterns_compile(self):
        for path, data in _load_all_json_files():
            patterns_section = data.get("patterns", {})

            if path.name == "common-patterns.json":
                # Check caps_normalization
                caps = patterns_section.get("caps_normalization", {})
                if "pattern" in caps:
                    re.compile(caps["pattern"])

                # Check excessive_punctuation
                punct = patterns_section.get("excessive_punctuation", {})
                for entry in punct.get("patterns", []):
                    re.compile(entry["pattern"])

                # Check repeated_characters
                repeat = patterns_section.get("repeated_characters", {})
                if "pattern" in repeat:
                    re.compile(repeat["pattern"])
            else:
                # Language dictionaries
                for level_name, categories in patterns_section.items():
                    for category_name, pattern_list in categories.items():
                        for entry in pattern_list:
                            try:
                                re.compile(entry["pattern"])
                            except re.error as e:
                                pytest.fail(
                                    f"{path.name} [{level_name}][{category_name}]: "
                                    f"invalid regex '{entry['pattern']}': {e}"
                                )


# ---------------------------------------------------------------------------
# 3. Required fields present in language dicts
# ---------------------------------------------------------------------------


class TestRequiredFields:
    @pytest.mark.parametrize(
        "path,data",
        _language_dicts(),
        ids=lambda x: x.name if isinstance(x, Path) else "",
    )
    def test_required_fields_present(self, path, data):
        assert "language" in data, f"{path.name} missing 'language' field"
        assert "patterns" in data, f"{path.name} missing 'patterns' field"


# ---------------------------------------------------------------------------
# 4. Intensity levels present
# ---------------------------------------------------------------------------


class TestIntensityLevels:
    @pytest.mark.parametrize(
        "path,data",
        _language_dicts(),
        ids=lambda x: x.name if isinstance(x, Path) else "",
    )
    def test_intensity_levels_present(self, path, data):
        patterns = data.get("patterns", {})
        for level in ("light", "moderate", "strict"):
            assert level in patterns, f"{path.name} missing intensity level '{level}'"


# ---------------------------------------------------------------------------
# 5. No duplicate patterns within same category/level
# ---------------------------------------------------------------------------


class TestNoDuplicatePatterns:
    def test_no_duplicate_patterns(self):
        for path, data in _language_dicts():
            patterns_section = data.get("patterns", {})
            for level_name, categories in patterns_section.items():
                for category_name, pattern_list in categories.items():
                    seen = []
                    for entry in pattern_list:
                        p = entry["pattern"]
                        assert p not in seen, (
                            f"{path.name} [{level_name}][{category_name}]: "
                            f"duplicate pattern '{p}'"
                        )
                        seen.append(p)


# ---------------------------------------------------------------------------
# 6. Common patterns structure
# ---------------------------------------------------------------------------


class TestCommonPatternsStructure:
    def test_common_patterns_structure(self):
        path = DICTIONARIES_DIR / "common-patterns.json"
        with open(path) as f:
            data = json.load(f)

        assert "description" in data
        assert "patterns" in data
        patterns = data["patterns"]

        assert "caps_normalization" in patterns
        assert "excessive_punctuation" in patterns
        assert "repeated_characters" in patterns

        # caps_normalization has pattern
        assert "pattern" in patterns["caps_normalization"]

        # excessive_punctuation has patterns list
        assert "patterns" in patterns["excessive_punctuation"]
        assert len(patterns["excessive_punctuation"]["patterns"]) > 0

        # repeated_characters has pattern and replacement
        assert "pattern" in patterns["repeated_characters"]
        assert "replacement" in patterns["repeated_characters"]


# ---------------------------------------------------------------------------
# 7. Replacement fields present
# ---------------------------------------------------------------------------


class TestReplacementFields:
    def test_replacement_fields_present(self):
        for path, data in _language_dicts():
            patterns_section = data.get("patterns", {})
            for level_name, categories in patterns_section.items():
                for category_name, pattern_list in categories.items():
                    for i, entry in enumerate(pattern_list):
                        assert "pattern" in entry, (
                            f"{path.name} [{level_name}][{category_name}][{i}]: "
                            f"missing 'pattern' field"
                        )
                        assert "replacement" in entry, (
                            f"{path.name} [{level_name}][{category_name}][{i}]: "
                            f"missing 'replacement' field"
                        )
