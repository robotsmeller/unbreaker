# Unbreaker Context

```yaml
version: 1.3.0
data_version: 0.8.0
status: PZ went B42.20 Stable on 2026-07-29. Repo has v1.3.0 / data v0.8.0 (143 redirects), re-validated against an installed 42.20 rather than against changelogs. Live Workshop build is still v1.2.1 / data v0.6.0 (135 redirects), now two data versions behind.
created: 2026-04-22
session: 11
last_updated: 2026-07-30
verification_target: B42.20
continue_with: Ship v1.3.0 to the Workshop (Rob runs it, see HARD RULE), then the pz-mod-checker work Rob queued: a 42.20.0 rules file for that project, whose rules top out at 42.18.0.
blockers: HARD RULE, the agent NEVER touches Steam/Workshop. No SteamCMD, no publish step, and not build_workshop.ps1 either; the permission classifier blocks that script, which is correct. All releasing is Rob's manual action. Workshop description still needs a manual restore in Steam (Rob).

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
- Truly removed B42 modules: ISLootWindowControlHandler, CharacterCustomisationPanel, CommonTemplates (the last two confirmed gone in 42.20; they were live in 42.17)
- NOT in this list any more: VehicleUtils. Promoted to a working redirect in v0.8.0. The old entry conflated a missing FILE with a missing GLOBAL. Watch for that confusion, the redirect only needs the global.

## Files Worth Knowing

- `mod/42/media/lua/shared/Unbreaker.lua` — override + miss ring buffer, v1.2.1
- `data/vanilla_globals.json` — v0.8.0, 143 shipped redirects (+ `unrecoverable` and `verified:false` entries, not shipped)
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

### Session 11 (2026-07-30): B42.20 Stable deep dive, data v0.8.0 / mod v1.3.0
PZ shipped B42.20 to Stable on 2026-07-29. Verified against an INSTALLED 42.20 instead of against changelogs, which is the method worth repeating: 1,395 vanilla lua files under `media/lua`, plus `projectzomboid.jar` (23,735 classes) as a fallback index for Java-exposed globals. Rob's own 42.20 launch log supplied 29 live require failures to triage.

Result: 133 of the 137 shipped redirects survived 42.20 untouched. Added 4 (`gamepadBinding`, the only breakage 42.20 actually introduced, per its changelog moving the file from /shared to /client; plus `TimedActions/ISWalkToTimedAction`, `ISUI/ISItemDropBox`, `Items/ProceduralDistributions/ProceduralDistributions`, all three observed failing live but NOT attributable to 42.20 specifically, since there is no 42.19 install to diff against). Resolved all 3 candidates staged in v0.7.0 and shipped them. Promoted `Vehicles/VehicleUtils` out of unrecoverable. Demoted `CharacterCustomisationPanel` and `CommonTemplates` to unrecoverable, both confirmed absent from media/ and the jar. 137 -> 143 shipped.

Also synced Rob's local test copy at `~/Zomboid/mods/Unbreaker`, which was v1.2.0 and silently shadowing the v1.2.1 Workshop copy, so his testing was two versions behind.

**BIGGEST METHOD CHANGE: we now diff builds instead of reading changelogs.** Rob pointed at the community mirror `Project-Zomboid-Community-Modding/ProjectZomboid-Vanilla-Lua`, whose commits are named by version (`29df4fe` = 42.19, and it has no 42.20 yet). `git clone --depth 1` gives a full 42.19 `client/server/shared` tree that diffs directly against the installed 42.20. Do this every patch from now on. It is strictly better than the changelog, and it is cheap.

What the 42.19 -> 42.20 diff produced that no changelog reading would have:
- `gamepadBinding` shared -> client is the ONLY root move in the entire build. Confirms the redirect and confirms nothing else moved.
- `Farming/BuildingObjects/ISFarmingCursor` was DELETED and the changelog never mentions it. Logged unrecoverable, not redirected: the surviving `ISFarmingCursorMouse` shares only 6 of 10 methods (missing `getObjectList`, `isValid`, `onJoypadPressButton`, `rotateKey`), so redirecting would hand mods a half-broken object.
- The `LastStand/Challenge2` family (6 modules, 6 globals) went with the Challenge Mode revamp, replaced by `28MinutesLater` and `TopOfTheWorld`. Not logged, zero reports, add on demand.
- `CharacterCustomisationPanel` and `CommonTemplates` were ALREADY GONE in 42.19. Sessions 8 and 9 reviewed those builds from changelogs and called them clean, and both times these were already dead. That is the case for diffing.
- The other 22 "lost globals" are accidental globals someone finally made `local` (`counta`, `startX`, `doRect`, `itemList`). Ignore that class.

**Method note worth keeping.** Three traps hit in one session. (1) "The module file exists, so the redirect is a no-op" is WRONG: B42 files exist but return nil, which is the exact case Unbreaker covers. Check for a top-level `return`, not for the file. (2) A regex anchored at column 0 misses `  Distributions = ...` with leading whitespace and manufactures false positives. (3) `BodyLocations` has no lua assignment anywhere yet is a live global, because it comes from Java (`zombie/characters/WornItems/BodyLocations`). Any "this global is gone" claim must check the jar before it is written down.

### Session 10 (2026-06-24): Triaged diagnostic-tool reports #12–#15, data v0.7.0
First inbound community reports, all from falkon311 via the diagnostic tool (17 unique modules across 4 issues). Pulled the console.txt attachments and triaged against the artifact. Added 2 verified alternate-path redirects (`ISUI/ISUI3DScene`, `TimedActions/ISPathFindAction`) whose target globals are already verified live via their `Vehicles/`-prefixed siblings, so they ship with confidence without a fresh probe. Bumped data v0.6.0 → v0.7.0 (137 shipped). Staged 3 unverified probe candidates (`Animals/MigrationGroupDefinitions`, `Animals/RanchZoneDefinitions` from Animals Everywhere; `Definitions/ContainerButtonsIcons`, a plural-vs-singular typo vs vanilla `ContainerButtonIcons`) as verified:false — need an in-game `rawget(_G, basename)` probe before shipping. Everything else was mod-internal (VRO, VorpallySauced, Inventory Tetris, CSR, GydeTraitMags, NVAPI, Error Magnifier) or a missing dependency — out of scope by design. Replied on #15 with the full triage, closed #12–#14 as consolidated. NOT yet released to Workshop.

### Session 9 (2026-06-01): B42.19 verification + CFarmingSystem fix, shipped v1.2.1
Reviewed B42.19 Unstable (no modding breakage). Live-probed Issue #5/#6 modules: added `Farming/CFarmingSystem` (verified in-game via full-restart re-probe), reclassified Json/recipecode/Items/ItemFactory/Maps/ISMapDefinitions as unrecoverable. Shipped v1.2.1 / data v0.6.0 (135 redirects) to Workshop, live and public. Closed all issues #2–#6. Removed description from the publish pipeline after a push clobbered Rob's manual Steam edits. Added SessionStart issue hook; repaired fetch MCP server.

### Session 8 (2026-05-11): B42.18 update prep
Reviewed B42.18 patch notes (MODDING purely additive, no breakage). Bumped data v0.4.0 → v0.5.0, added `verification_target`. Staged 2 candidates (Json, recipecode, verified:false). Held release pending in-game probe.

## Critical for Next Session

1. **Ship v1.3.0 / data v0.8.0 to the Workshop — ROB ONLY.** Repo has 143 redirects; the live build is still 135 (v1.2.1 / data v0.6.0). HARD RULE: the agent NEVER touches Steam/Workshop. The permission classifier also blocks `build_workshop.ps1` outright, which is correct and should be left alone. Rob runs both steps himself:
   `powershell -File scripts\build_workshop.ps1`
   `& C:\steamcmd\steamcmd.exe +login robotsmeller +workshop_build_item "build\workshop_item.txt" +quit`
   #15 stays open as the tracker until this ships. See memory `never-touch-steam`.
2. **Update the Workshop description BY HAND in the Steam app** when v1.3.0 goes up. It currently reads "Verified on Build 42.19 Unstable" and "135 verified redirects/fixes". Should say B42.20 Stable and 143. NEVER push it through the pipeline (memory `workshop-description-never-push`).
3. **pz-mod-checker, the queued follow-up.** It already pulls Unbreaker coverage live from GitHub raw `main` (`pz_mod_checker/unbreaker.py`, 24h cache), so redirects sync themselves once this is merged. What is stale there is `data/rules/`, which tops out at `42.18.0.json`. A `42.20.0.json` is the real work. Seed material already gathered from Rob's 42.20 log: `LuaManager.validateReflectionAccess` refusing reflection outside debug mode, and Java signature changes such as `hasTag` on `HandWeapon`. Neither is a require failure, so neither is Unbreaker's problem.
4. **Optional probes, low priority.** Everything shipped in v0.8.0 was verified statically against the install (top-level assignment in an auto-loaded file, or a jar class). An in-game `rawget` pass would upgrade confidence on `Vehicles/VehicleUtils` specifically, since its defining file is under `media/lua/server` and so may not resolve for an MP client.
5. Promotion: r/projectzomboid post (lead with the diagnostic tool), Indie Stone forums, PZ modding Discord. Outreach to authors of mods Unbreaker covers.
6. Next B42.x patch: clone the 42.20 commit from the vanilla lua mirror once it lands and diff it against the new install. That is now the standard first move for any patch.
