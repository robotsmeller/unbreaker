# Unbreaker Context

```yaml
version: 0.1.0
status: Scaffolded — awaiting Phase 1 proof-of-concept
created: 2026-04-22
session: 2
last_updated: 2026-04-22

arch:
  stack: Lua (PZ mod), Python (tooling), GitHub Actions (CI/CD)
  purpose: Polyfill for PZ mods broken by incremental weekly patches
  target: Project Zomboid Build 42.x (actively developed, ~weekly patches)
  coauthor: Claude Sonnet 4.6 <noreply@anthropic.com>

identity:
  product: Unbreaker
  what: Standalone PZ Workshop mod. Works with or without PZ Mod Checker.
  framing: Patch buffer — keeps mods working between patches while authors catch up
  not: A B41->B42 migration tool. Not a mod compatibility database. Not a rewriter.
```

## Core Pattern

```lua
local _require = require
require = function(module)
    local ok, result = pcall(_require, module)
    if ok then return result end
    if STUBS[module] then return STUBS[module]() end
    error("module '" .. module .. "' not found", 2)
end
```

Real module always wins. Stub only fires on failure. No manual cleanup when mods update.

## What It Fixes (see SCOPE.md for full detail)

- require() failures: vanilla globals that moved to auto-loaded scope
- require() failures: filename mismatches within a mod
- Renamed functions: alias old name to new name
- Moved globals: register old location pointing to new one

## What It Cannot Fix

- Deep API rewrites (crafting, animation, vehicles)
- Missing mod dependencies (empty stub silences crash, doesn't restore function)
- Translation gaps (needs filesystem access, not available in Kahlua)
- Brita, Arsenal, True Actions (need full rewrites)
- Multiplayer (unverified — checksum risk)

## Session Notes

### Session 1 (2026-04-22): Research + Scaffold

**Origin:** Spun out of PZ Mod Checker Session 8. PZMC diagnose revealed 50+ mods with
require() failures. Research established the architecture.

**Key research findings:**
- PZ Lua (Kahlua) cannot make HTTP requests — sandbox intentionally blocks java.net
- package.preload status in Kahlua: UNVERIFIED — use require() override instead
- Steam Workshop updates at game launch, before PZ loads — this IS the update mechanism
- No HTTP from Lua needed. GitHub JSON -> SteamCMD -> Workshop -> Steam delivers it.
- require() override with pcall fallback: real module always wins automatically
- Collab audit (Soren/Atlas/Morgan): all CAUTION, not STOP. Core mechanism sound.

**Naming discussion:**
- "Duct Tape" rejected — sounds like an item mod
- "ModBridge" rejected — implies B41/B42 bridging which isn't what this does
- "Unbreaker" retained — tongue-in-cheek, clearly mod-scoped
- Framing clarified: not B41->B42, it's a weekly patch buffer

**Scope clarified:**
- Polyfill model (same as browser JS polyfills)
- Can: require redirects, function aliases, moved globals
- Cannot: rewrites, missing deps, translation, multiplayer (unverified)

**What was created:**
- Full folder structure at c:\xampp\htdocs\unbreaker\
- Public GitHub repo: https://github.com/rob-kingsbury/unbreaker
- SCOPE.md — definitive scope document
- ROADMAP.md — 7-phase plan
- vanilla_globals.json — 15 entries (all verified: false)
- GitHub Actions: auto-generate UnbreakerData.lua on data changes
- Issue templates: mod-request, stub-broken

**Known vanilla global redirects (from PZMC diagnose, 180-mod install):**
| Module | Global | Mods affected |
|--------|--------|---------------|
| ISUI/ISInventoryPaneContextMenu | ISInventoryPaneContextMenu | 5 |
| TimedActions/ISInventoryTransferAction | ISInventoryTransferAction | 3 |
| Vehicles/Vehicles | Vehicles | 3 |
| ISUI/ISContextMenu | ISContextMenu | 1 |
| ISUI/ISHotbar | ISHotbar | 1 |
| ISUI/ISWorldMap | ISWorldMap | 1 |
| ISUI/PlayerData/ISPlayerData | ISPlayerData | 1 |
| ISUI/InventoryWindow/ISLootWindowControlHandler | ISLootWindowControlHandler | 1 |
| BuildingObjects/ISAnimalPickMateCursor | ISAnimalPickMateCursor | 1 |
| BodyLocations | BodyLocations | 1 |
| Vehicles/VehicleUtils | VehicleUtils | 1 |
| Vehicles/Distributions | VehicleDistributions | 1 (name unverified) |
| SimpleSilencersModelTable | SimpleSilencersModelTable | 1 (filename mismatch) |
| SimpleSilencersCraftedSilencerBlacklist | SimpleSilencersCraftedSilencerBlacklist | 1 (filename mismatch) |

**Major library targets (Phase 4+):**
- damnlib: 2.4M subscribers, ~80 KI5 vehicle mods. B42 version exists but breaks each patch.
  Require names: DAMN_MechOverlay (B41) and damnlib (B42) — need both.
- tsarslib: 4.6M subscribers (B41). B42 Tchernobill port at 565k, breaks each patch.
  True Actions (3.3M) has no B42 version at all.

**Critical blocker for Session 2:**
Does the require() global override work in PZ's Kahlua? Write a 20-line test mod.
Everything else depends on this answer.
