"""Follow-up discovery probe for the inconclusive Class A modules.

For ISMapDefinitions and ItemFactory the first probe found no same-name global.
This enumerates _G for the real global names (case-insensitive substring) and
retries corrected require paths, so we can decide redirect vs unfixable without
making the player reload.

Run in the same live world as issue_probe.py.

Usage:
    python scripts/issue_probe_followup.py
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

LUA = r"""
local function find(sub)
    sub = string.lower(sub)
    local hits = {}
    for k, v in pairs(_G) do
        if type(k) == "string" and string.find(string.lower(k), sub, 1, true) then
            hits[#hits + 1] = k .. " (" .. type(v) .. ")"
        end
    end
    return hits
end

local function tryreq(name)
    local ok, m = pcall(require, name)
    return { ok = ok, type = type(m), nil_value = (m == nil) }
end

return {
    -- enumerate real global names
    globals_mapdefinit = find("mapdefinit"),
    globals_factory    = find("factory"),
    globals_farming    = find("farming"),
    globals_recipe     = find("recipe"),
    globals_json       = find("json"),
    -- retry corrected / alternate paths for ISMapDefinitions
    req_ISUI_Maps_ISMapDefinitions = tryreq("ISUI/Maps/ISMapDefinitions"),
    req_client_Maps_ISMapDefinitions = tryreq("client/ISUI/Maps/ISMapDefinitions"),
    -- retry ItemFactory alternates
    req_ItemFactory_bare = tryreq("ItemFactory"),
}
"""


def main() -> int:
    cfg = load_config()
    cfg["command_timeout_s"] = 90
    print("Sending follow-up discovery probe. Keep PZ window focused.")
    try:
        result = send_command(cfg, "run_lua", {"code": LUA})
    except (CommandTimeout, HarnessDead) as e:
        print(json.dumps({"error": str(e)}, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
