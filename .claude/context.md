# Unbreaker Context

```yaml
version: 1.2.0
status: Ship-ready. Diagnostic tool live on GitHub Pages. Pending SteamCMD Workshop upload.
created: 2026-04-22
session: 6
last_updated: 2026-05-07

arch:
  stack: Lua (PZ mod), Python (tooling), GitHub Actions (CI/CD), GitHub Pages (diagnostic)
  purpose: Polyfill for PZ mods broken by incremental weekly patches
  target: Project Zomboid Build 42.x (actively developed, ~weekly patches)
  layout: B42 versioned (mod/42/media/...)

identity:
  product: Unbreaker
  what: Standalone PZ Workshop mod. Works with or without PZ Mod Checker.
  framing: Patch buffer — keeps mods working between patches while authors catch up
  not: A B41->B42 migration tool. Not a mod compatibility database. Not a rewriter.
```

## Core Pattern (v1.2.0)

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
        unknown = unknown + 1
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

- `mod/42/media/lua/shared/Unbreaker.lua` — override + miss ring buffer, v1.2.0
- `data/vanilla_globals.json` — v0.4.0, 134 verified entries
- `docs/index.html` — GitHub Pages diagnostic tool (paste console.txt, get categorized results)
- `assets/workshop-description.txt` — Workshop page copy (BBCode, humanizer-audited)
- `scripts/final_probe.py` — re-run after every data change to verify
- `scripts/smoke_probe.py` — quick architecture sanity check

## Diagnostic Tool (docs/index.html)

Static GitHub Pages tool at https://robotsmeller.github.io/unbreaker/

- Fetches vanilla_globals.json from GitHub raw on load (always current)
- User pastes or drags console.txt; text is processed entirely in-browser, never uploaded
- Categorizes require() failures: fixed / not fixable / library stub needed / unknown
- Unknown section has "Open GitHub issue" button that pre-fills an issue with all uncovered modules
- Security: all user-derived content through escHtml() before innerHTML; backticks and newlines sanitized before GitHub issue URL construction

## Session Notes

### Session 6 (2026-05-07): Diagnostic tool + security hardening
Built docs/index.html GitHub Pages diagnostic tool. Soren audit found two issues: backtick injection into Markdown issue body (medium) and newline/null passthrough (low) — both fixed. Updated README and workshop-description.txt to reference tool. GitHub Pages must be enabled in repo settings (main branch, /docs folder) to go live.

### Session 5 (2026-05-07): Collab audit fixes + Phase 2/3 redirect expansion
Soren+Atlas audit: fixed verified filter in generator (H1), added CI validation gate (H2), capped missSeen (L5), removed dead alias branch (L3/L4). In-game probes expanded redirects 27 -> 96 -> 134 (all verified live B42.17). Version bumped to 1.2.0.

## Critical for Next Session

1. Enable GitHub Pages in repo settings (Settings > Pages > main branch, /docs folder)
2. SteamCMD Workshop upload
3. Update Workshop footer link in docs/index.html once Workshop ID is known
4. Pin scoped comment on Workshop page day one
5. Phase 2: triage miss buffer (issues #1-3 are first candidates)
