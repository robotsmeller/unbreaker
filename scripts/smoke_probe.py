"""
Smoke-test probe: ship a bundled Lua payload to PZ Test Pilot's run_lua,
collect a single JSON result with all the answers we need.

Usage:
    python scripts/smoke_probe.py

PZ window must be FOCUSED (not paused) for the duration. ~10-30 seconds.
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

PROBE_LUA = r"""
local results = {}

results.harness_alive = true
results.loadstring_works = (loadstring ~= nil)
results.unbreaker_loaded = (_G.Unbreaker ~= nil)
if _G.Unbreaker then
    results.unbreaker_version = _G.Unbreaker.version
    results.unbreaker_data_version = _G.Unbreaker.data_version
    results.unbreaker_redirect_count = _G.Unbreaker.redirect_count
    results.unbreaker_stats_pre = _G.Unbreaker.stats()
end

local ok1, mod1 = pcall(require, "TestPilot/Json")
results.real_module_loads = ok1
results.real_module_type = type(mod1)

local ok2, mod2 = pcall(require, "ISUI/ISContextMenu")
results.broken_module_intercepted = ok2
results.broken_module_type = type(mod2)
results.broken_module_is_global = (mod2 == _G.ISContextMenu)

local ok3, err3 = pcall(require, "Unbreaker/DefinitelyDoesNotExist_xyz123")
results.unknown_module_fails = (not ok3)
results.unknown_module_error = tostring(err3)

local probes = {
    "ISUI/ISInventoryPaneContextMenu","ISUI/ISVehicleMenu","ISUI/ISContextMenu",
    "ISUI/ISHotbar","ISUI/ISWorldMap","ISUI/PlayerData/ISPlayerData",
    "ISUI/InventoryWindow/ISLootWindowControlHandler",
    "BuildingObjects/ISAnimalPickMateCursor",
    "TimedActions/ISInventoryTransferAction",
    "Vehicles/Vehicles","Vehicles/Distributions","BodyLocations",
    "SimpleSilencersModelTable","SimpleSilencersCraftedSilencerBlacklist","AquaConfig"
}
local probeResults = {}
for i, name in ipairs(probes) do
    local ok, m = pcall(require, name)
    local g = nil
    if _G.Unbreaker and _G.Unbreaker.has_redirect(name) then
        g = "(redirect entry exists)"
    end
    probeResults[name] = {
        ok = ok,
        type = type(m),
        is_table = (type(m) == "table"),
        nil_value = (m == nil),
        has_redirect = _G.Unbreaker and _G.Unbreaker.has_redirect(name) or false,
    }
end
results.vanilla_global_probes = probeResults

if _G.Unbreaker then
    results.unbreaker_stats_post = _G.Unbreaker.stats()
end

return results
"""


def main() -> int:
    cfg = load_config()
    cfg["command_timeout_s"] = 90  # generous; user might re-focus mid-flight

    print("Sending bundled probe to PZ Test Pilot. Keep PZ window focused.")
    try:
        result = send_command(cfg, "run_lua", {"code": PROBE_LUA})
    except CommandTimeout as e:
        print(json.dumps({"status": "timeout", "error": str(e)}, indent=2))
        return 1
    except HarnessDead as e:
        print(json.dumps({"status": "harness_dead", "error": str(e)}, indent=2))
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
