"""
Tests for scripts/generate_lua.py.

Run: python -m pytest tests/test_generate.py
"""

from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from generate_lua import load_redirects, lua_string, render_entry, render_lua


# ---------------------------------------------------------------------------
# lua_string
# ---------------------------------------------------------------------------

def test_lua_string_plain():
    assert lua_string("hello") == '"hello"'


def test_lua_string_escapes_backslash():
    assert lua_string("a\\b") == '"a\\\\b"'


def test_lua_string_escapes_double_quote():
    assert lua_string('a"b') == '"a\\"b"'


def test_lua_string_escapes_newline():
    assert lua_string("a\nb") == '"a\\nb"'


def test_lua_string_escapes_carriage_return():
    assert lua_string("a\rb") == '"a\\rb"'


def test_lua_string_strips_null_bytes():
    assert lua_string("a\x00b") == '"ab"'


def test_lua_string_path_with_slash():
    assert lua_string("ISUI/ISContextMenu") == '"ISUI/ISContextMenu"'


# ---------------------------------------------------------------------------
# render_entry
# ---------------------------------------------------------------------------

def test_render_entry_with_global():
    entry = {"global": "ISContextMenu", "category": "vanilla_global", "verified": True}
    result = render_entry(entry)
    assert result == '{ global="ISContextMenu" }'
    assert "category" not in result
    assert "module" not in result


def test_render_entry_no_global():
    result = render_entry({})
    assert result == "{  }"


# ---------------------------------------------------------------------------
# render_lua
# ---------------------------------------------------------------------------

def test_render_lua_structure():
    entries = [("ISUI/ISContextMenu", {"global": "ISContextMenu"})]
    lua = render_lua("1.0.0", entries)
    assert 'M.version = "1.0.0"' in lua
    assert 'M.redirects = {' in lua
    assert '["ISUI/ISContextMenu"] = { global="ISContextMenu" },' in lua
    assert lua.strip().endswith("return M")


def test_render_lua_empty_entries():
    lua = render_lua("0.0.0", [])
    assert "M.redirects = {" in lua
    assert "return M" in lua
    # No entry lines between redirects = { and }
    lines = lua.splitlines()
    open_idx = next(i for i, l in enumerate(lines) if "M.redirects = {" in l)
    close_idx = next(i for i, l in enumerate(lines) if l.strip() == "}")
    assert close_idx == open_idx + 1


def test_render_lua_no_dead_fields():
    entries = [("SomeMod/SomeFile", {"global": "SomeGlobal", "category": "vanilla_global"})]
    lua = render_lua("1.0.0", entries)
    assert "category" not in lua
    assert 'module=' not in lua


# ---------------------------------------------------------------------------
# load_redirects (uses a temporary JSON fixture, not the real data file)
# ---------------------------------------------------------------------------

def _make_json(redirects: list[dict]) -> str:
    return json.dumps({"version": "1.0.0", "redirects": redirects})


def test_load_redirects_filters_unverified(tmp_path, monkeypatch):
    data = _make_json([
        {"module": "A/B", "global": "G", "category": "vanilla_global", "verified": True},
        {"module": "C/D", "global": "H", "category": "vanilla_global", "verified": False},
    ])
    src = tmp_path / "vanilla_globals.json"
    src.write_text(data, encoding="utf-8")

    import generate_lua
    monkeypatch.setattr(generate_lua, "SRC_VANILLA", src)

    version, entries = load_redirects()
    modules = [m for m, _ in entries]
    assert "A/B" in modules
    assert "C/D" not in modules


def test_load_redirects_filters_unrecoverable(tmp_path, monkeypatch):
    data = _make_json([
        {"module": "A/B", "global": "G", "category": "vanilla_global", "verified": True},
        {"module": "C/D", "global": "H", "category": "unrecoverable", "verified": True},
    ])
    src = tmp_path / "vanilla_globals.json"
    src.write_text(data, encoding="utf-8")

    import generate_lua
    monkeypatch.setattr(generate_lua, "SRC_VANILLA", src)

    version, entries = load_redirects()
    modules = [m for m, _ in entries]
    assert "A/B" in modules
    assert "C/D" not in modules


def test_load_redirects_skips_missing_module(tmp_path, monkeypatch):
    data = _make_json([
        {"global": "G", "category": "vanilla_global", "verified": True},
    ])
    src = tmp_path / "vanilla_globals.json"
    src.write_text(data, encoding="utf-8")

    import generate_lua
    monkeypatch.setattr(generate_lua, "SRC_VANILLA", src)

    version, entries = load_redirects()
    assert entries == []


def test_load_redirects_empty_json(tmp_path, monkeypatch):
    src = tmp_path / "vanilla_globals.json"
    src.write_text(json.dumps({}), encoding="utf-8")

    import generate_lua
    monkeypatch.setattr(generate_lua, "SRC_VANILLA", src)

    version, entries = load_redirects()
    assert version == "0.0.0"
    assert entries == []


def test_load_redirects_version_passthrough(tmp_path, monkeypatch):
    data = _make_json([])
    src = tmp_path / "vanilla_globals.json"
    src.write_text(data, encoding="utf-8")

    import generate_lua
    monkeypatch.setattr(generate_lua, "SRC_VANILLA", src)

    version, _ = load_redirects()
    assert version == "1.0.0"


# ---------------------------------------------------------------------------
# Integration: known-good JSON produces expected entry count
# ---------------------------------------------------------------------------

def test_real_data_entry_count():
    """Verified entry count in JSON matches what load_redirects returns."""
    root = Path(__file__).resolve().parent.parent
    raw = json.loads((root / "data" / "vanilla_globals.json").read_text(encoding="utf-8"))
    expected = sum(
        1 for e in raw.get("redirects", [])
        if e.get("verified") and e.get("category") != "unrecoverable" and e.get("module")
    )
    _, entries = load_redirects()
    assert len(entries) == expected
