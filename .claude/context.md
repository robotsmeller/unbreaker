# Unbreaker Context

```yaml
version: 1.2.0
status: Live on Steam Workshop. Public visibility. Promotion phase.
created: 2026-04-22
session: 7
last_updated: 2026-05-07

arch:
  stack: Lua (PZ mod), Python (tooling), GitHub Actions (CI/CD), GitHub Pages (diagnostic), PowerShell (Workshop build)
  purpose: Polyfill for PZ mods broken by incremental weekly patches
  target: Project Zomboid Build 42.x (actively developed, ~weekly patches)
  layout: B42 versioned (mod/42/media/...)

identity:
  product: Unbreaker
  what: Standalone PZ Workshop mod. Works with or without PZ Mod Checker.
  framing: Patch buffer — keeps mods working between patches while authors catch up
  not: A B41->B42 migration tool. Not a mod compatibility database. Not a rewriter.

workshop:
  id: 3721648770
  url: https://steamcommunity.com/sharedfiles/filedetails/?id=3721648770
  visibility: public
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

**B42 require() quirk:** returns nil silently for missing modules (does NOT throw). Must check `(ok and result ~= nil)` to detect "loaded but unusable" — the common case because most vanilla files set a global as a side-effect and never return anything.

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
- `docs/index.html` — GitHub Pages diagnostic tool with Simple/Advanced views
- `assets/workshop-description.txt` — Workshop page copy (BBCode, source of truth)
- `assets/unbreaker-childish.png` — master art (1280x1280) used for poster + preview
- `scripts/build_workshop.ps1` — Workshop publish pipeline (folder + VDF gen)
- `workshop_item.template.txt` — VDF template (description is placeholder, replaced at build)
- `PUBLISH.md` — runbook
- `scripts/final_probe.py` — re-run after every data change to verify
- `scripts/smoke_probe.py` — quick architecture sanity check

## Workshop Publishing (lessons from Session 7)

- **`poster.png` is the Workshop cover thumbnail, NOT `preview.png`.** PZ uses these inverted from what the names suggest. (Memory: project_pz_workshop_images.md)
- **VDF gotchas:** `\n` doesn't interpret (use real newlines); `\"` truncates the string (forbid literal `"` in descriptions); placeholder description in VDF will clobber the live one on next push.
- **Tags don't work via SteamCMD VDF on PZ.** Both `tags { tag "..." }` and `tags "a,b,c"` formats are ignored. Use PZ's in-game Workshop publisher (`~/Zomboid/Workshop/<ModName>/workshop.txt`).
- **Preview image cap: 1 MB.** Steam returns "Limit exceeded" for oversized previews — same error name as rate limit. Resize to 1024x1024 or 512x512 and re-encode.

## Diagnostic Tool (docs/index.html)

Static GitHub Pages tool at https://robotsmeller.github.io/unbreaker/

- Fetches vanilla_globals.json from GitHub raw on load (always current)
- User pastes or drags console.txt; text is processed entirely in-browser, never uploaded
- Categorizes require() failures: fixed / not fixable / library stub needed / unknown
- Simple/Advanced view tabs (Simple default), light/dark/system theme toggle
- Simple view: status banner sized to worst category, plain-language stats, inline report button
- Unknown bucket has one-click "Open GitHub issue" button pre-filled with module list
- Security: all user-derived content through escHtml() before innerHTML; backticks and newlines sanitized before GitHub issue URL construction

## Recent Sessions

### Session 7 (2026-05-07): Workshop launch
Built SteamCMD pipeline; resolved every VDF gotcha (rate limit, 1MB preview cap, layout, description clobbering, `\n` not interpreting, `\"` truncating). Discovered `poster.png` is the Workshop thumbnail. Mod live and public at id 3721648770.

### Session 6 (2026-05-07): Diagnostic tool + security hardening
Built docs/index.html GitHub Pages diagnostic tool. Soren audit found backtick injection and newline passthrough; both fixed. Updated README and workshop description to reference tool.

### Session 5 (2026-05-07): Collab audit fixes + Phase 2/3 redirect expansion
Fixed verified filter, added CI validation gate, capped missSeen, removed dead alias branch. Two in-game probes expanded redirects 27 -> 96 -> 134 (verified live B42.17). Version bumped to 1.2.0.

## Critical for Next Session

1. Verify tags appear on Workshop page (use PZ in-game publisher if VDF didn't take)
2. Draft and post r/projectzomboid announcement (lead with diagnostic tool, not the mod)
3. Indie Stone forums + PZ modding Discord posts
4. Triage Issue #4 (6 unknowns from launch session)
5. Outreach to authors of mods Unbreaker covers
