# Unbreaker Context

```yaml
version: 1.2.1
data_version: 0.7.0
status: Live Workshop build is v1.2.1 / data v0.6.0 (135 redirects), public, verified B42.19. Repo HEAD has data v0.7.0 (137 redirects) staged but NOT yet shipped to Workshop.
created: 2026-04-22
session: 10
last_updated: 2026-06-24
verification_target: B42.19
continue_with: Cut a v1.2.2 release to ship data v0.7.0 (137 redirects) to the Workshop, OR batch it with the 3 staged probe candidates after an in-game probe.
blockers: 2 new redirects + 3 probe candidates sit in the repo unshipped. Workshop release is manual (no publish.yml). Workshop description still needs a manual restore in Steam.

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

## Core Pattern (v1.2.1)

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

**B42 require() quirk:** returns nil silently for missing modules (does NOT throw). Must check `(ok and result ~= nil)` to detect "loaded but unusable" — the common case because most vanilla files set a global as a side-effect and never return anything. Discovery for a new candidate: `rawget(_G, basename)` — if the file's side-effect global exists, redirect the module path to it.

**Note for triage:** PZ's own require logs `require(...) failed` (WARN) whenever a require returns nil, and that line still prints even for modules Unbreaker successfully redirects (the original require runs first, logs, then Unbreaker's fallback resolves it). A "failed" warning in console.txt is not proof of breakage. The diagnostic tool correctly reports only modules absent from the shipped redirect list.

## What It Fixes

- require() failures: vanilla globals that moved to side-effect-only auto-loaded scope
- require() failures: filename mismatches within a mod
- require() failures: alternate paths to an already-redirected global (e.g. `TimedActions/ISPathFindAction` vs `Vehicles/TimedActions/ISPathFindAction`)
- Moved globals: register old location pointing to new one

## What It Cannot Fix

- Deep API rewrites (crafting, animation, vehicles)
- Missing mod dependencies / self-broken mods (empty stub silences crash, doesn't restore function) — e.g. WaterPipes `wp_vsquare`, Smoke Like It's 93 `require 'Items/'`
- Mod-internal modules (a mod requiring its own files: VRO/*, VorpallySauced/*, InventoryTetris/*, etc.) — no vanilla global to point at
- Modules with no vanilla global to point at (unrecoverable) — Json, recipecode, Items/ItemFactory, Maps/ISMapDefinitions
- Translation gaps (needs filesystem access, not available in Kahlua)
- Brita, Arsenal, True Actions (need full rewrites)
- Multiplayer (untested — checksum risk)
- Truly removed B42 modules: ISLootWindowControlHandler, VehicleUtils

## Files Worth Knowing

- `mod/42/media/lua/shared/Unbreaker.lua` — override + miss ring buffer, v1.2.1
- `data/vanilla_globals.json` — v0.7.0, 137 shipped redirects (+ `unrecoverable` and `verified:false` entries, not shipped)
- `scripts/generate_lua.py` — JSON → Lua (skips unrecoverable + unverified)
- `scripts/build_workshop.ps1` — Workshop pipeline (folder + VDF). VDF omits description — NEVER pushed. No publish.yml; releasing is a manual run of this script.
- `workshop_item.template.txt` — VDF template, no description line
- `scripts/final_probe.py`, `scripts/smoke_probe.py` — verification probes
- `scripts/issue_probe.py`, `scripts/issue_probe_followup.py` — issue-triage probes (rawget(_G, basename) discovery)
- `.claude/hooks/session-issues.sh` — SessionStart hook: open issues grouped by status (in-progress / new)
- `docs/index.html` — GitHub Pages diagnostic tool with Simple/Advanced views
- `assets/workshop-description.txt` — reference copy of launch description (NOT live source of truth; hand-managed in Steam)
- `PUBLISH.md` — runbook

## Workshop Publishing (lessons)

- **`poster.png` is the Workshop cover thumbnail, NOT `preview.png`.** PZ inverts these. (Memory: project_pz_workshop_images.md)
- **NEVER push the description** — it overwrites Rob's manual Steam-app edits. The VDF omits the field; build script throws if reintroduced. (Memory: workshop-description-never-push)
- **VDF gotchas:** `\n` doesn't interpret (use real newlines); `\"` truncates the string (forbid literal `"`).
- **Tags don't work via SteamCMD VDF on PZ.** Use PZ's in-game Workshop publisher (`~/Zomboid/Workshop/<ModName>/workshop.txt`).
- **Preview image cap: 1 MB.** Steam returns "Limit exceeded" (same error name as rate limit). Resize to 1024x1024 or 512x512.
- **SteamCMD credentials cache locally** — Session 9 push logged in via `+login robotsmeller` with no 2FA prompt.

## Diagnostic Tool (docs/index.html)

Static GitHub Pages tool at https://robotsmeller.github.io/unbreaker/

- Fetches vanilla_globals.json from GitHub raw on load (always current)
- User pastes or drags console.txt; processed entirely in-browser, never uploaded
- Categorizes require() failures: fixed / not fixable (includes `unrecoverable`) / library stub needed / unknown
- Simple/Advanced view tabs, light/dark/system theme toggle
- Unknown bucket has one-click "Open GitHub issue" button pre-filled with module list
- Security: all user-derived content through escHtml() before innerHTML; backticks and newlines sanitized before GitHub issue URL construction

## Recent Sessions

### Session 10 (2026-06-24): Triaged diagnostic-tool reports #12–#15, data v0.7.0
First inbound community reports, all from falkon311 via the diagnostic tool (17 unique modules across 4 issues). Pulled the console.txt attachments and triaged against the artifact. Added 2 verified alternate-path redirects (`ISUI/ISUI3DScene`, `TimedActions/ISPathFindAction`) whose target globals are already verified live via their `Vehicles/`-prefixed siblings, so they ship with confidence without a fresh probe. Bumped data v0.6.0 → v0.7.0 (137 shipped). Staged 3 unverified probe candidates (`Animals/MigrationGroupDefinitions`, `Animals/RanchZoneDefinitions` from Animals Everywhere; `Definitions/ContainerButtonsIcons`, a plural-vs-singular typo vs vanilla `ContainerButtonIcons`) as verified:false — need an in-game `rawget(_G, basename)` probe before shipping. Everything else was mod-internal (VRO, VorpallySauced, Inventory Tetris, CSR, GydeTraitMags, NVAPI, Error Magnifier) or a missing dependency — out of scope by design. Replied on #15 with the full triage, closed #12–#14 as consolidated. NOT yet released to Workshop.

### Session 9 (2026-06-01): B42.19 verification + CFarmingSystem fix, shipped v1.2.1
Reviewed B42.19 Unstable (no modding breakage). Live-probed Issue #5/#6 modules: added `Farming/CFarmingSystem` (verified in-game via full-restart re-probe), reclassified Json/recipecode/Items/ItemFactory/Maps/ISMapDefinitions as unrecoverable. Shipped v1.2.1 / data v0.6.0 (135 redirects) to Workshop, live and public. Closed all issues #2–#6. Removed description from the publish pipeline after a push clobbered Rob's manual Steam edits. Added SessionStart issue hook; repaired fetch MCP server.

### Session 8 (2026-05-11): B42.18 update prep
Reviewed B42.18 patch notes (MODDING purely additive, no breakage). Bumped data v0.4.0 → v0.5.0, added `verification_target`. Staged 2 candidates (Json, recipecode, verified:false). Held release pending in-game probe.

## Critical for Next Session

1. **Ship data v0.7.0 to the Workshop.** Repo HEAD has 137 redirects (the 2 new alternate paths); the live build is still 135. Bump mod to v1.2.2 and run `build_workshop.ps1` (manual; no publish.yml). #15 stays open as the tracker until this ships.
2. **In-game probe the 3 staged candidates** (verified:false in vanilla_globals.json): `rawget(_G,'MigrationGroupDefinitions')`, `rawget(_G,'RanchZoneDefinitions')`, and both spellings of ContainerButton(s)Icons. Flip to verified:true and ship any that resolve; reclassify the rest.
3. **Restore the Workshop description** in the Steam app — the v1.2.1 push reverted it to the launch copy. The pipeline no longer pushes it.
4. Promotion: r/projectzomboid post (lead with the diagnostic tool), Indie Stone forums, PZ modding Discord. Outreach to authors of mods Unbreaker covers.
5. Monitor for the next B42.x patch; re-run probes if any redirect breaks (B42.20+). Verify Workshop tags via the PZ in-game publisher.
