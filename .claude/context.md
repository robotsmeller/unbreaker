# Unbreaker Context

```yaml
version: 0.0.1
status: Scaffolding — not yet functional
created: 2026-04-22
session: 1
last_updated: 2026-04-22

arch:
  stack: Lua (PZ mod), Python (tooling), GitHub Actions (CI/CD)
  purpose: Fix broken require() calls in popular B42-incompatible PZ mods
  target: Project Zomboid Build 42.x
  coauthor: Claude Sonnet 4.6 <noreply@anthropic.com>

identity:
  product: Unbreaker
  what: Standalone PZ Workshop mod, works with or without PZ Mod Checker
  approach: require() override with pcall fallback, data-driven JSON redirects
```

## Background

Spun out of PZ Mod Checker (Session 8, 2026-04-22). Research findings:

- B42 broke require() calls for dozens of popular mods by moving vanilla globals out of requireable files into auto-loaded global scope
- Two major library mods (damnlib, tsarslib) gate access to ~15-20M combined mod subscriptions
- Steam Workshop update mechanism = reliable silent distribution (checked at game launch)
- require() override with pcall fallback is the correct Lua pattern (real module always wins over stub)
- package.preload priority order is unverified in PZ's Kahlua — use global require() override instead

## Key Research (Session 1)

### Known vanilla global redirects (from PZ Mod Checker diagnose on 180-mod install)
- ISUI/ISInventoryPaneContextMenu -> ISInventoryPaneContextMenu (5 mods affected)
- TimedActions/ISInventoryTransferAction -> ISInventoryTransferAction (3 mods)
- Vehicles/Vehicles -> Vehicles (3 mods)
- Vehicles/VehicleUtils -> VehicleUtils (1 mod)
- ISUI/ISContextMenu -> ISContextMenu (1 mod)
- ISUI/ISHotbar -> ISHotbar (1 mod)
- ISUI/ISWorldMap -> ISWorldMap (1 mod)
- ISUI/PlayerData/ISPlayerData -> ISPlayerData (1 mod)
- ISUI/InventoryWindow/ISLootWindowControlHandler -> ISLootWindowControlHandler (1 mod)
- BuildingObjects/ISAnimalPickMateCursor -> ISAnimalPickMateCursor (1 mod)
- BodyLocations -> BodyLocations (1 mod)
- Vehicles/Distributions -> VehicleDistributions (needs verification)

### Major library targets
- damnlib: 2.4M subscribers, gates ~80 KI5 vehicle mods. B42 version exists but breaks each patch. Require names: DAMN_MechOverlay (B41) and damnlib (B42)
- tsarslib: 4.6M subscribers (B41), B42 port by Tchernobill at 565k but unstable. True Actions (3.3M) has no B42 version.

### Critical unknown
- Does require() override work in PZ Kahlua? Needs empirical test mod before building anything else.

## Session Notes

### Session 1 (2026-04-22): Project scaffolding
Folder structure created. GitHub repo initialized. ROADMAP.md populated.
All research from PZ Mod Checker Session 8 carried over.
First code task: test mod to verify require() override works in PZ.
