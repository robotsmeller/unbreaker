"""Class A issue-triage probe.

Probes the vanilla-candidate modules reported in GitHub issues (#4, #6) against a
running PZ via the Test Pilot harness. For each module it answers three things:

  1. Does require() succeed, and what does it return? (ok / type / nil)
  2. Does a side-effect global with the module's basename exist in _G?
     e.g. "Maps/ISMapDefinitions" -> rawget(_G, "ISMapDefinitions")
  3. Is it already in the Unbreaker redirect table?

Interpretation:
  require ok, non-nil ............ already works in B42, nothing to do
  require ok+nil OR fails, global exists ... vanilla global -> ADD REDIRECT to that global
  fails, no global (clean install) ......... truly removed/rewritten -> unfixable
The "global_basename" field is the redirect target to drop into vanilla_globals.json.

Run on a CLEAN vanilla B42.19 install (no mods needed for Class A). PZ window must be
FOCUSED and unpaused. ~10-30 seconds.

Usage:
    python scripts/issue_probe.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

TEST_PILOT_ROOT = Path(os.environ.get("PZ_TEST_PILOT_PATH", "C:/xampp/htdocs/pz-test-pilot"))
sys.path.insert(0, str(TEST_PILOT_ROOT / "scripts"))

from config import load as load_config
from _ipc import send_command, CommandTimeout, HarnessDead

# Class A: vanilla candidates from issues #4 and #6 (no mods required to probe).
# Json + recipecode were staged verified:false in Session 8; the rest are new.
LUA = r"""
if not _G.Unbreaker then return { error = "Unbreaker not loaded" } end

local function basename(s) return s:match("([^/]+)$") or s end

local modules = {
    "Maps/ISMapDefinitions",
    "Items/ItemFactory",
    "Farming/CFarmingSystem",
    "Json",
    "recipecode",
}

local results = {}
for _, name in ipairs(modules) do
    local ok, m = pcall(require, name)
    local base = basename(name)
    local g = rawget(_G, base)
    results[name] = {
        require_ok = ok,
        return_type = type(m),
        returned_nil = (m == nil),
        global_basename = base,
        global_exists = (g ~= nil),
        global_type = type(g),
        has_redirect = _G.Unbreaker.has_redirect(name),
    }
end

return {
    unbreaker_loaded = true,
    data_version = _G.Unbreaker.data_version,
    redirect_count = _G.Unbreaker.redirect_count,
    probes = results,
}
"""


def main() -> int:
    cfg = load_config()
    cfg["command_timeout_s"] = 90
    print("Sending Class A issue probe. Keep PZ window focused.")
    try:
        result = send_command(cfg, "run_lua", {"code": LUA})
    except (CommandTimeout, HarnessDead) as e:
        print(json.dumps({"error": str(e)}, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
