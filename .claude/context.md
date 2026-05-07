# Unbreaker Context

```yaml
version: 0.2.0
status: Phase 1 re-validated Session 3. Pre-ship items identified. Ready to ship after ~5 code changes + mod ID decision.
created: 2026-04-22
session: 4
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

## Core Pattern (refined from Session 2 findings)

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
        -- ... alias fallback ...
    end

    if not ok then error(result, 2) end
    return result  -- pass through nil for unknown modules
end
```

**Key insight from Session 2:** B42's require() returns nil silently for missing
modules (does NOT throw). Naive `pcall` fallback never triggers. Must check
`(ok and result ~= nil)` to detect "loaded but unusable" — the actual common case
because most vanilla files set `_G.Name = SomeClass:derive(...)` then `return`
nothing.

## What It Fixes

- require() failures: vanilla globals that moved to side-effect-only auto-loaded scope
- require() failures: filename mismatches within a mod
- Renamed functions: alias old name to new name (data shape supports it)
- Moved globals: register old location pointing to new one

## What It Cannot Fix

- Deep API rewrites (crafting, animation, vehicles)
- Missing mod dependencies (empty stub silences crash, doesn't restore function)
- Translation gaps (needs filesystem access, not available in Kahlua)
- Brita, Arsenal, True Actions (need full rewrites)
- Multiplayer (untested — checksum risk)
- Truly removed B42 modules: ISLootWindowControlHandler, VehicleUtils

## Session Notes

### Session 1 (2026-04-22): Research + Scaffold
Spun out of PZ Mod Checker. Established architecture, repo, JSON seed, GH Actions.
Critical Phase 1 blocker identified: does require() override work in Kahlua?

### Session 2 (2026-05-06 → 2026-05-07): Phase 1 proof + expansion

**Verified the entire architecture in live B42.17.** Used pz-test-pilot harness
(itself pre-development) to drive Lua probes from outside the running game.

**Stats from a real 180-mod install at end of session:**
- 141 require() calls intercepted
- 139 served correctly (98.6%)
- 2 unserved (both pre-documented unrecoverable)
- 303 unique misses captured for Phase 2 triage

**Two B42 bugs in PZ itself, fixed in pz-test-pilot:**
1. `fileExists()` returns false for files that exist — bypassed via reader-trial
2. The Lua `Json` module is gone — replaced with pure-Lua encoder/decoder

**One B42 require() quirk handled in Unbreaker.lua:**
- `require()` returns nil silently for missing modules. The override now treats
  `(ok and result == nil)` as a redirect trigger rather than only `(not ok)`.

**Mod layout migrated to B42 versioned (mod/42/media/...).** Generator updated.

**Data expanded from 15 → 27 entries.** All non-unrecoverable entries verified
live via the bundled probe.

## Files Worth Knowing

- `mod/42/media/lua/shared/Unbreaker.lua` — override + miss ring buffer
- `data/vanilla_globals.json` — v0.2.0, 27 entries
- `scripts/final_probe.py` — re-run after every data change to verify
- `scripts/smoke_probe.py` — quick architecture sanity check

## Session Notes (continued)

### Session 3 (2026-05-07): In-game validation + pre-ship planning

**Re-validated in live B42.17 new game session.** Probe confirmed 141 intercepted, 139 served (98.6%). All 13 spot-checked redirects return valid tables. Architecture holds.

**Key finding: WARN messages in PZ log are NOT Lua failures.** PZ logs `require("X") failed` at the Java level when native _require() fails. This fires before Unbreaker's redirect kicks in. WARNs appear even when Unbreaker successfully serves. Do not use WARNs as failure metric.

**Load order issue confirmed.** "Unbreaker" sorts late alphabetically. Mods like kattaj1_42_17_shim run their Lua before Unbreaker's hook installs. Those load-time calls are genuinely missed. For Workshop installs (numeric mod ID), digits sort before letters — may not be an issue. Needs empirical test. Mod ID decision required before first publish (permanent).

**Collab audit completed.** Ship strategy: Option C — ship with 27 redirects now, Phase 2 post-ship. Two hard blockers: CI workflow path (`mod/media/...` → `mod/42/media/...`), mod ID decision. Full plan in `plan-review.md`.

## Critical for Future Sessions

Next session starts with pre-ship blockers:
1. Fix CI workflow path (`.github/workflows/generate.yml:28`)
2. Decide mod ID (affects Workshop publish — permanent)
3. Remove alias dead code, bump version, fix docstring
4. Push to GitHub remote
5. Workshop description + thumbnail (user to unwatermark)
6. Publish

Phase 2 (303-entry miss buffer triage) is post-ship work.
