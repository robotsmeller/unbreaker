# Unbreaker

A standalone Project Zomboid mod that keeps your mods working between patches.

Every PZ update moves something. A file gets renamed, a global shifts scope, a `require()` path changes. Mods that haven't caught up start crashing silently. Unbreaker intercepts those broken `require()` calls and returns the correct value instead.

**Real modules always win.** Unbreaker only fires when the original load fails. When a mod's author ships a proper fix, Unbreaker steps aside automatically — no config needed.

Tested in B42.17 against a 180-mod install: 141 broken `require()` calls intercepted, 139 served correctly (98.6%).

---

## Install

Subscribe on the [Steam Workshop](#) *(link pending — will update after first publish)*.

No config. No setup. Load order is handled automatically.

---

## What it fixes

- `require()` calls targeting vanilla files that moved to auto-loaded global scope in B42
- `require()` calls with filename mismatches (mod requires the wrong filename for its own file)
- Moved globals: old location redirected to new one

## What it does NOT fix

- **Brita's Weapon Pack, Arsenal, True Actions** — these need their authors to rewrite large parts of the mod. A polyfill can't do that.
- Deep B42 API rewrites (crafting, animation, vehicles)
- Missing mod dependencies
- Multiplayer (untested — single-player only for now)

---

## Architecture

```
data/vanilla_globals.json          # Source of truth — all redirects live here
scripts/generate_lua.py            # JSON → UnbreakerData.lua (run manually or via CI)
mod/42/media/lua/shared/
  Unbreaker.lua                    # require() override + miss ring buffer
  UnbreakerData.lua                # Generated — never edit by hand
```

The core pattern:

```lua
local _require = require
require = function(module)
    local ok, result = pcall(_require, module)
    if ok and result ~= nil then return result end  -- real module wins

    local entry = REDIRECTS[module]
    if entry and entry.global then
        local g = rawget(_G, entry.global)
        if g ~= nil then return g end
    end

    if not ok then error(result, 2) end
    return result
end
```

B42's `require()` returns `nil` silently for missing modules rather than throwing. The `ok and result ~= nil` check catches both failure modes: actual errors and silent nil returns.

---

## Adding a redirect

1. Edit `data/vanilla_globals.json` — add an entry with `"verified": false`
2. Test it in a live PZ session
3. Set `"verified": true` and open a PR

The CI workflow regenerates `UnbreakerData.lua` automatically when the JSON changes.

```json
{
  "module": "ISUI/ISInventoryPaneContextMenu",
  "global": "ISInventoryPaneContextMenu",
  "category": "vanilla_global",
  "since_pz": "42.0.0",
  "verified": true,
  "notes": "Moved to auto-loaded global scope in B42."
}
```

Only entries with `"verified": true` are included in production builds.

---

## Reporting issues

Leave a comment on the Workshop page, or open a GitHub issue with:
- The mod name and Workshop ID
- What fails (crash log snippet if you have one)
- Whether the mod works without Unbreaker installed

---

## License

MIT — see [LICENSE](LICENSE).
