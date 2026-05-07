"""Final Phase 1 verification probe.

Sends a single bundled Lua payload that:
  1. Confirms Unbreaker is loaded with the expanded data set
  2. Reads runtime stats (intercepts/served/missed)
  3. Dumps the miss ring buffer (every module name we couldn't redirect)
  4. Spot-checks the new redirects added in v0.2.0

Usage:
    python scripts/final_probe.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

TEST_PILOT_ROOT = Path("C:/xampp/htdocs/pz-test-pilot")
sys.path.insert(0, str(TEST_PILOT_ROOT / "scripts"))

from config import load as load_config
from _ipc import send_command, CommandTimeout, HarnessDead

LUA = r"""
if not _G.Unbreaker then return { error = "Unbreaker not loaded" } end

local newRedirects = {
    "ISUI/ISInventoryPage", "ISUI/ISToolTipInv", "ISUI/ISChat", "ISUI/ISDebugMenu",
    "TimedActions/ISBaseTimedAction", "TimedActions/ISTakeFuel",
    "Vehicles/ISUI/ISVehicleMenu", "Foraging/forageSystem", "Foraging/ISSearchManager",
    "BuildingObjects/ISBuildingObject", "ISContextMenu", "ISBuildMenu", "luautils",
}

local checks = {}
for _, name in ipairs(newRedirects) do
    local ok, m = pcall(require, name)
    checks[name] = {
        ok = ok,
        type = type(m),
        is_table = (type(m) == "table"),
        has_redirect = _G.Unbreaker.has_redirect(name),
    }
end

return {
    version = _G.Unbreaker.version,
    data_version = _G.Unbreaker.data_version,
    redirect_count = _G.Unbreaker.redirect_count,
    stats = _G.Unbreaker.stats(),
    misses = _G.Unbreaker.misses(),
    new_redirect_checks = checks,
}
"""


def main() -> int:
    cfg = load_config()
    cfg["command_timeout_s"] = 90
    print("Sending final verification probe.")
    try:
        result = send_command(cfg, "run_lua", {"code": LUA})
    except (CommandTimeout, HarnessDead) as e:
        print(json.dumps({"error": str(e)}, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
