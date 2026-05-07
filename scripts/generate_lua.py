"""
Unbreaker — Lua data generator.

Reads data/vanilla_globals.json (and future data/library_stubs/) and emits
mod/media/lua/shared/UnbreakerData.lua, a Kahlua-compatible Lua 5.1 module
returned as a single table the runtime indexes by module path.

Run:
    python scripts/generate_lua.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SRC_VANILLA = ROOT / "data" / "vanilla_globals.json"
OUT = ROOT / "mod" / "42" / "media" / "lua" / "shared" / "UnbreakerData.lua"


def lua_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def render_entry(module: str, entry: dict[str, Any]) -> str:
    parts = [f"module={lua_string(module)}"]
    if entry.get("global"):
        parts.append(f"global={lua_string(entry['global'])}")
    if entry.get("alias"):
        parts.append(f"alias={lua_string(entry['alias'])}")
    if entry.get("category"):
        parts.append(f"category={lua_string(entry['category'])}")
    return "{ " + ", ".join(parts) + " }"


def load_redirects() -> tuple[str, list[tuple[str, dict[str, Any]]]]:
    raw = json.loads(SRC_VANILLA.read_text(encoding="utf-8"))
    version = raw.get("version", "0.0.0")
    out: list[tuple[str, dict[str, Any]]] = []
    for entry in raw.get("redirects", []):
        if entry.get("category") == "unrecoverable":
            continue
        module = entry.get("module")
        if not module:
            continue
        out.append((module, entry))
    return version, out


def render_lua(version: str, entries: list[tuple[str, dict[str, Any]]]) -> str:
    lines = [
        "-- UnbreakerData.lua — GENERATED FILE. Do not edit by hand.",
        "-- Source: data/vanilla_globals.json",
        "-- Regenerate with: python scripts/generate_lua.py",
        "",
        "local M = {}",
        f"M.version = {lua_string(version)}",
        "M.redirects = {",
    ]
    for module, entry in entries:
        lines.append(f"  [{lua_string(module)}] = {render_entry(module, entry)},")
    lines.append("}")
    lines.append("")
    lines.append("return M")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    version, entries = load_redirects()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render_lua(version, entries), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} — {len(entries)} redirects (data v{version})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
