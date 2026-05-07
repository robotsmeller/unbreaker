# Unbreaker — Handoff

**Last Updated:** 2026-05-07 (end of Session 2)

```yaml
session: 3
continue_with: Phase 2 — expand redirect data from Session 2's captured miss list (303 entries)
blockers: none
status: Phase 1 complete and live-verified
```

## Current State

**Phase 1 is done.** Architecture is empirically proven in PZ Build 42.17.

In a real 180-mod install during Session 2:
- 141 broken require() calls intercepted
- 139 served correctly via redirects (98.6% hit rate)
- 2 unserved — both already documented unrecoverable (ISLootWindowControlHandler, AquaConfig)

## What Exists

- `mod/42/media/lua/shared/Unbreaker.lua` — require() override with miss ring buffer
- `mod/42/media/lua/shared/UnbreakerData.lua` — generated, 27 redirects
- `mod/42/mod.info` and top-level `mod/mod.info` — B42 layout (`versionMin=42.0.0`)
- `data/vanilla_globals.json` — v0.2.0, 27 redirects (25 verified live, 2 documented unrecoverable)
- `scripts/generate_lua.py` — JSON → Lua generator (stdlib only)
- `scripts/smoke_probe.py` — bundled Phase 1 architecture probe via PZ Test Pilot
- `scripts/probe_misses.py` — candidate-list checker for redirect expansion
- `scripts/final_probe.py` — full live verification including miss-buffer dump
- Repo on GitHub, GitHub Actions auto-generates UnbreakerData.lua on JSON change

## Session 2 Findings

### Architecture works
- **require() override pattern works in Kahlua.** Confirmed via live probes.
- **B42 require() returns nil silently** for missing modules (does NOT throw). Our override now treats `(ok and result == nil)` as a redirect trigger if a redirect entry exists, else passes through unchanged.
- **B42 vanilla globals are real.** Most `ISUI/Foo`-style modules set `_G.Foo` as a side-effect at load time but don't `return` the table. Our redirect serves `_G.Foo` when require returns nil.

### B42 Bugs in PZ
- `fileExists()` returns false even for files that exist. Bypassed in pz-test-pilot's `FileIO.atomicRead()` by using `readFile()` empty/nil checks instead.
- The Lua `Json` module (`require("Json")` → table with .Encode/.Decode) is gone in B42. pz-test-pilot's `Json.lua` was rewritten as a self-contained pure-Lua encoder/decoder.

### Loadstring works
- `loadstring()` is available in Kahlua B42.17 — pz-test-pilot's `run_lua` route works without falling back to the `snippet` registry.

### Verified redirects (25 entries)
All probed live. ISInventoryPaneContextMenu, ISVehicleMenu (both paths), ISContextMenu (both paths), ISHotbar, ISWorldMap, ISPlayerData, ISInventoryPage, ISToolTipInv, ISChat, ISDebugMenu, ISBuildMenu, ISAnimalPickMateCursor, ISBuildingObject, ISInventoryTransferAction, ISBaseTimedAction, ISTakeFuel, Vehicles, VehicleDistributions, forageSystem, ISSearchManager, luautils, BodyLocations, SimpleSilencersModelTable, SimpleSilencersCraftedSilencerBlacklist.

### Unrecoverable (2 entries — kept for documentation)
- `ISLootWindowControlHandler` — global doesn't exist in B42. Module removed/renamed.
- `Vehicles/VehicleUtils` — file removed entirely. Required by Realistic Dashboard and Gauges.

### Captured for Phase 2 (303 unique misses)
Every require() in the user's install that returned nil and has no current redirect. Many are no-ops (mods requiring for side effects, discarding the result), but the list contains high-value candidates:
- `ISBaseObject`, `defines`, `Hotbar/ISHotbar` (alt path), `ISWorldObjectContextMenu`
- Many `ISUI/*` (ISPanel, ISButton, ISCollapsableWindow, ISTabPanel, ISScrollingListBox, ISTickBox, ISModalDialog, ISTextEntryBox, ISToolTip, ISLabel, ISImage, ...)
- `Map/CGlobalObject`, `Map/CGlobalObjectSystem`, `Map/SGlobalObject`, `Map/SGlobalObjectSystem`
- `TimedActions/*` family (ISTimedActionQueue, ISEatFoodAction, ISInventoryTransferUtil, ISTransferAction, ISWearClothing, ...)
- `Camping/CCampfireSystem`
- `Farming/SFarmingSystem`, `Farming/farming_vegetableconf`
- `Traps/TrapDefinition`, `Traps/STrapSystem`
- Full `WorldGen/features/*` tree (~50 entries)
- `PZAPI/ui/atoms/*`, `PZAPI/ui/molecules/*`, `PZAPI/ui/organisms/*`, `PZAPI/ModOptions`

## Phase 2 Tasks (next session)

1. Triage the 303-entry miss buffer
2. For each candidate: probe whether `_G.<leaf>` exists; if yes → add redirect with verified=true
3. For high-frequency families (WorldGen/features, ISUI) decide whether to add per-entry or pattern-based
4. Re-run final_probe and verify served-rate climbs further
5. Update Workshop description, prep for first publish (Phase 7 prerequisites)

## Phase 1 Decisions (Session 2)

| Decision | Rationale |
|---|---|
| Treat `(ok, nil)` as needing redirect | B42 require() returns nil for missing modules instead of throwing |
| Pass-through when no redirect entry | Avoid breaking mods that legitimately call require() for side effects |
| Ring buffer for miss diagnostics | Enables data-driven Phase 2 expansion without instrumenting individual mods |
| `42/media/` mod layout | Matches B42 convention; both Unbreaker and PZTestPilot use it |
| pz-test-pilot fixed in place | Two B42 regressions found; fixes belong in pz-test-pilot's repo |
| Verified=true gating | Every shipped redirect must round-trip live before being marked verified |

## Repo Layout

```
data/vanilla_globals.json        # source of truth (27 redirects)
scripts/
  generate_lua.py                # JSON -> Lua codegen
  smoke_probe.py                 # Phase 1 architecture probe
  probe_misses.py                # candidate redirect checker
  final_probe.py                 # full live verification + miss dump
mod/
  mod.info                       # outer (B42 layout marker)
  42/
    mod.info
    media/lua/shared/
      Unbreaker.lua              # the override
      UnbreakerData.lua          # GENERATED — never edit by hand
.github/workflows/generate.yml   # CI regen on JSON change
```

## Open Questions Carried Over

| # | Question | Notes |
|---|---|---|
| 1 | Multiplayer: does override cause checksum rejection? | Untested. Single-player verified. |
| 2 | damnlib API surface KI5 mods actually call | Phase 4 prerequisite |
| 3 | tsarslib B42 Tchernobill API surface | Phase 5 prerequisite |
| 4 | SteamCMD GitHub Actions 2FA setup | Phase 7 prerequisite |
| 5 | How to triage the 303-entry miss list efficiently | Phase 2 starts here |

## Workshop Description Draft (still applicable)

> Keeps your mods working between PZ patches. Fixes broken require() calls,
> renamed functions, and moved globals — the minor API shuffles that come with
> almost every weekly update. Does NOT fix mods needing deep rewrites. When a
> mod's author publishes a proper fix, Unbreaker automatically steps aside.
> Stopgap, not a replacement.
