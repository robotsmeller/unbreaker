# Unbreaker Context

```yaml
version: 1.0.0
status: Ship-ready. All pre-ship items complete. Pending repo move + Workshop upload.
created: 2026-04-22
session: 5
last_updated: 2026-05-07

arch:
  stack: Lua (PZ mod), Python (tooling), GitHub Actions (CI/CD)
  purpose: Polyfill for PZ mods broken by incremental weekly patches
  target: Project Zomboid Build 42.x (actively developed, ~weekly patches)
  layout: B42 versioned (mod/42/media/...)

identity:
  product: Unbreaker
  what: Standalone PZ Workshop mod. Works with or without PZ Mod Checker.
  framing: Patch buffer — keeps mods working between patches while authors catch up
  not: A B41->B42 migration tool. Not a mod compatibility database. Not a rewriter.
```

## Core Pattern (v1.0.0 — alias branch removed)

```lua
local _require = require
require = function(module)
    local ok, result = pcall(_require, module)
    if ok and result ~= nil then return result end

    local entry = REDIRECTS[module]
    if entry then
        if entry.global then
            local g = rawget(_G, entry.global)
            if g ~= nil then return g end
        end
        missed = missed + 1
        recordMiss(module)
    else
        recordMiss(module)
    end

    if not ok then error(result, 2) end
    return result
end
```

**Key insight from Session 2:** B42's require() returns nil silently for missing
modules (does NOT throw). Must check `(ok and result ~= nil)` to detect "loaded
but unusable" — the common case because most vanilla files set a global as a
side-effect and never return anything.

**Session 4:** Alias branch removed from override. No JSON entries use `alias` and
the branch had a latent bug (resolveGlobal called with module paths). Remove until
there's data that needs it.

## What It Fixes

- require() failures: vanilla globals that moved to side-effect-only auto-loaded scope
- require() failures: filename mismatches within a mod
- Moved globals: register old location pointing to new one

## What It Cannot Fix

- Deep API rewrites (crafting, animation, vehicles)
- Missing mod dependencies (empty stub silences crash, doesn't restore function)
- Translation gaps (needs filesystem access, not available in Kahlua)
- Brita, Arsenal, True Actions (need full rewrites)
- Multiplayer (untested — checksum risk)
- Truly removed B42 modules: ISLootWindowControlHandler, VehicleUtils

## Files Worth Knowing

- `mod/42/media/lua/shared/Unbreaker.lua` — override + miss ring buffer, v1.0.0
- `data/vanilla_globals.json` — v0.2.0, 27 entries
- `assets/workshop-description.txt` — Workshop page copy (BBCode, humanizer-audited)
- `scripts/final_probe.py` — re-run after every data change to verify
- `scripts/smoke_probe.py` — quick architecture sanity check

## Session Notes

### Session 4 (2026-05-07): Pre-ship hardening + publish prep
Completed all 9 pre-ship items. CI path fixed, alias dead code removed, version bumped to 1.0.0, Workshop description written and audited, thumbnails verified. Mod ID decision: keep Unbreaker (Workshop numeric ID handles load order). Repo move to neutral GitHub account noted — must do before publish to avoid personal name in URL.

### Session 3 (2026-05-07): In-game validation + pre-ship planning
Re-validated in live B42.17. 141 intercepted, 139 served (98.6%). WARN messages confirmed as Java-level noise, not Lua failures. Load order issue for local installs documented. Collab audit completed, ship strategy decided: Option C — 27 redirects now, Phase 2 post-ship.

### Session 2 (2026-05-06): Phase 1 proof + expansion
Verified architecture live in B42.17 via pz-test-pilot. 141 intercepted, 139 served (98.6%), 303 unique misses captured for Phase 2. require() nil-return quirk handled. Layout migrated to B42 versioned. Data expanded 15 → 27 entries.

## Critical for Next Session

1. ~~Move repo to neutral GitHub account~~ Done — github.com/robotsmeller/unbreaker
2. ~~Update URLs in mod.info and workshop-description.txt~~ Done
3. SteamCMD Workshop upload
4. Pin scoped comment on Workshop page day one
5. Phase 2: triage 303-entry miss buffer (issues #1-3 are first candidates)
