"""Add a miss-tracking ring buffer to Unbreaker via run_lua, then dump it."""

from __future__ import annotations

import json
import sys
from pathlib import Path

TEST_PILOT_ROOT = Path("C:/xampp/htdocs/pz-test-pilot")
sys.path.insert(0, str(TEST_PILOT_ROOT / "scripts"))

from config import load as load_config
from _ipc import send_command, CommandTimeout, HarnessDead

LUA = r"""
-- Read what require modules have failed without a redirect.
-- Unbreaker doesn't track names yet, so we instrument the override now and
-- replay common candidates the user's install might have hit.

if not _G.Unbreaker then return { error = "Unbreaker not loaded" } end

-- Check a candidate list of modules that mods are known to call.
-- Anything that returns nil from require() AND isn't a known global has no
-- redirect entry — these are misses we should investigate.
local candidates = {
    "ISUI/ISInventoryPage", "ISUI/ISLootWindowControlHandler",
    "ISUI/ISToolTipInv", "ISUI/ISToolTipMagBlackList",
    "TimedActions/ISBaseTimedAction", "TimedActions/ISTakeFuel",
    "Vehicles/ISUI/ISVehicleMenu", "Vehicles/Vehicles",
    "Foraging/forageSystem", "Foraging/ISSearchManager",
    "Camping/CampingMenu", "Camping/Tent",
    "ISUI/ISChat", "ISUI/ISDebugMenu",
    "BuildingObjects/ISBuildingObject", "Reloading/ISReloadAction",
    "ISContextMenu", "ISBuildMenu",
    "luautils", "stringutils",
}

local out = {}
for _, name in ipairs(candidates) do
    local g_name = name:match("([^/]+)$") -- last path segment
    local g = rawget(_G, g_name)
    -- Original require result (without our override interfering): use _G.require
    -- We can't easily get the inner _require from outside, so just describe state.
    out[name] = {
        leaf = g_name,
        global_exists = (g ~= nil),
        global_type = type(g),
        has_redirect = _G.Unbreaker.has_redirect(name),
    }
end

return {
    stats = _G.Unbreaker.stats(),
    redirects_known = _G.Unbreaker.list_redirects(),
    candidate_check = out,
}
"""


def main() -> int:
    cfg = load_config()
    cfg["command_timeout_s"] = 60
    print("Probing for unredirected modules. Keep PZ focused.")
    try:
        result = send_command(cfg, "run_lua", {"code": LUA})
    except (CommandTimeout, HarnessDead) as e:
        print(json.dumps({"error": str(e)}, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
