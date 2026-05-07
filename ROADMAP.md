# Unbreaker — Roadmap

A standalone Project Zomboid Workshop mod that silently fixes broken `require()` calls
for popular mods that haven't been updated for Build 42.

---

## Coverage Model

The redirect list targets vanilla module paths that moved in B42. Those are a finite set. Each entry covers every mod that uses that path, so coverage compounds as the list grows. The goal is comprehensive coverage of vanilla-path breakage, not a general compatibility layer.

Three failure modes are outside scope and won't be addressed by expanding the redirect list:

| Failure mode | Example | Fixable? |
|---|---|---|
| Vanilla path moved | `require("ISUI/ISInventoryPaneContextMenu")` | Yes, add redirect entry |
| Self-broken mod | mod requires a file that never existed | No |
| Missing dependency | mod A requires mod B not installed | No |
| Major library not stubbed | damnlib, tsarslib | Phase 4/5 |

When a mod is still broken after installing Unbreaker, one of the last three rows is almost certainly why.

---

## Phase 0: Infrastructure (current)

- [x] Project scaffolded
- [x] GitHub repo created (public)
- [x] vanilla_globals.json seeded with 12 known redirects
- [x] Issue templates created
- [ ] GitHub Actions: auto-generate UnbreakerData.lua when data/*.json changes
- [ ] GitHub Actions: publish to Steam Workshop on release tag (SteamCMD)
- [ ] Steam Workshop item created (placeholder listing)

---

## Phase 1: Proof of Concept

**Blocker: verify core mechanism works before writing anything else.**

- [ ] Write 20-line test mod that overrides global `require`
- [ ] Verify: `require("SomeModule")` is intercepted by the override
- [ ] Verify: real module (file exists) wins over stub via pcall fallback
- [ ] Verify: load order — does alphabetical naming guarantee loading before other mods?
- [ ] Verify: PZ registers all mod Lua paths before any mod code executes
- [ ] Verify: multiplayer — does require() override cause checksum mismatch?
- [ ] Document findings in `.claude/context.md`

**Exit criteria:** A test mod in PZ that intercepts a require() call and returns a stub value. Confirmed working in singleplayer. Multiplayer status documented.

---

## Phase 2: Vanilla Globals (safe redirects)

**Zero API replication required. High confidence fixes.**

### Data tasks
- [ ] Verify each redirect in vanilla_globals.json against actual PZ B42 Lua source
- [ ] Document `since_pz` version for each (when did the global move?)
- [ ] Add missing redirects as GitHub Issues are filed

### Known redirects to verify and ship

| Module path | Global name | Affected mods | Verified |
|-------------|-------------|---------------|---------|
| ISUI/ISInventoryPaneContextMenu | ISInventoryPaneContextMenu | KATTAJ1 packs, Context Menu Building, US Military Pack, Simple Silencers | No |
| TimedActions/ISInventoryTransferAction | ISInventoryTransferAction | More Traits, Bandits Week One, Nepenthe's More On The Floor | No |
| Vehicles/Vehicles | Vehicles | Bandits Week One, RotatorsLib, Nepenthe's High Beams | No |
| Vehicles/VehicleUtils | VehicleUtils | Realistic Dashboard and Gauges | No |
| Vehicles/Distributions | VehicleDistributions | (unknown) | No |
| ISUI/ISContextMenu | ISContextMenu | Realistic Dashboard and Gauges | No |
| ISUI/ISHotbar | ISHotbar | Reorder The Hotbar | No |
| ISUI/ISWorldMap | ISWorldMap | (unknown) | No |
| ISUI/PlayerData/ISPlayerData | ISPlayerData | RotatorsLib | No |
| ISUI/InventoryWindow/ISLootWindowControlHandler | ISLootWindowControlHandler | (unknown) | No |
| BuildingObjects/ISAnimalPickMateCursor | ISAnimalPickMateCursor | (unknown) | No |
| BodyLocations | BodyLocations | Skully's Duffelbags | No |

### Code tasks
- [ ] Write `scripts/generate_lua.py` (JSON -> UnbreakerData.lua)
- [ ] Write `mod/media/lua/shared/Unbreaker.lua` (require() override)
- [ ] Write `mod/mod.info`
- [ ] Test each vanilla global redirect in PZ
- [ ] Submit to Steam Workshop

**Exit criteria:** Unbreaker is on the Workshop. Installs, loads, and demonstrably reduces require() failures in PZ Mod Checker diagnose output.

---

## Phase 3: Filename Mismatch Fixes

**Mods that require() their own files under the wrong name.**

- [ ] Simple Silencers: `SimpleSilencersModelTable` -> global `SimpleSilencersModelTable` (file is `SimpleSilencers_ModelTable.lua`)
- [ ] Simple Silencers: `SimpleSilencersCraftedSilencerBlacklist` -> global
- [ ] Identify other filename-mismatch cases from community issues
- [ ] Add `filename_mismatch` category handling to generate_lua.py

**Note:** These are different from vanilla globals. The global exists because PZ auto-loads all .lua files, but the require() name doesn't match the filename. The stub returns the global that the auto-loaded file already set up.

---

## Phase 4: damnlib Stub (KI5 Vehicles — 2.4M+ subscribers)

**Highest impact. Requires API research.**

### Research tasks
- [ ] Read damnlib source (B41 and B42 versions) — what does the API actually expose?
- [ ] Enumerate all functions/tables KI5 vehicle mods call on the damnlib module
- [ ] Determine minimum API surface needed for vehicles to load and function
- [ ] Check: does damnlib B42 version work if installed alongside Unbreaker? (avoid shadowing a working lib)

### Implementation tasks
- [ ] Write `data/library_stubs/damnlib.json` — full API surface definition
- [ ] Implement `damnlib` stub in Lua (functional, not empty `{}`)
- [ ] Handle both require names: `DAMN_MechOverlay` (B41) and `damnlib` (B42)
- [ ] Test with 3-5 KI5 vehicle mods
- [ ] Test: when real damnlib is installed, Unbreaker defers to it (pcall fallback)

**Exit criteria:** At least one KI5 vehicle loads and functions in-game with Unbreaker but without damnlib installed.

---

## Phase 5: tsarslib Stub (Tsar/iBrRus family — 4.6M subscribers)

**Complex. True Actions and Autotsar depend on this.**

- [ ] Read tsarslib B41 and Tchernobill B42 port source
- [ ] Enumerate API surface used by True Actions and Autotsar
- [ ] Assess feasibility: is the API surface small enough to stub meaningfully?
- [ ] Write `data/library_stubs/tsarslib.json`
- [ ] Implement stub
- [ ] Test with True Actions

**Note:** tsarslib does more than damnlib — crafting integration, UI, vehicle systems. This may be too large to stub meaningfully. Reassess after damnlib.

---

## Phase 6: Multiplayer Support

**Currently untested. Single-player only until this phase is complete.**

### What needs to be true for MP to work

PZ validates Workshop mod files via checksum when a client connects to a server. The core questions are:

1. **Does the checksum check cover `Unbreaker.lua`?** If the server has Unbreaker and the client doesn't (or vice versa), PZ may reject the connection. Both sides need the same mod files.
2. **Does the `require()` override change execution state the server tracks?** The override replaces the global `require` function. If PZ's netcode checksums any Lua state beyond file contents (e.g. loaded module results), differing redirect outcomes on client vs. server could cause desync.
3. **Are redirect results consistent across client and server?** A vanilla global redirect returns a value that's already in memory on both sides — low desync risk. A library stub that returns a fake table is higher risk if the server runs different mod logic against it.

### Research tasks

- [ ] Determine how PZ validates mods in MP: file checksums, Lua state, or both
- [ ] Confirm: does PZ require all players on a server to have identical mod lists?
- [ ] Identify which redirect categories are MP-safe (vanilla globals: likely fine; library stubs: needs testing)

### Test tasks

- [ ] Install Unbreaker on both a local server and client, connect, confirm no rejection
- [ ] Test: client has Unbreaker, server does not — document what happens
- [ ] Test: at least one redirect fires during a multiplayer session, confirm no desync
- [ ] Test: dedicated server (not local host) — same results?

### Documentation tasks

- [ ] Document server-side install requirement (if applicable)
- [ ] Update Workshop description to remove single-player disclaimer once verified
- [ ] Note any redirect categories that remain MP-unsafe

**Exit criteria:** Unbreaker installs on a server, clients connect without rejection, a redirect fires in a multiplayer session without causing a desync or crash.

---

## Phase 8: PZ Mod Checker Integration

**PZMC can detect what Unbreaker would fix and link to it.**

- [ ] PZMC diagnose page: "X of these failures would be fixed by Unbreaker" note
- [ ] Link to Workshop page from diagnose output
- [ ] PZMC optionally fetches vanilla_globals.json for display (shows which failures are fixable vs. not)

---

## Phase 9: Community Infrastructure

- [ ] CONTRIBUTING.md — how to submit a new redirect or report a broken stub
- [ ] Issue template: mod request (mod name, Workshop ID, what fails, subscriber count)
- [ ] Issue template: stub broken (mod updated, Unbreaker now shadowing real module)
- [ ] Label conventions documented
- [ ] Process for verifying community-submitted redirects before merging

---

## Ongoing Maintenance

**After each PZ patch:**
- Run PZ Mod Checker diagnose on a large mod install
- Check if any vanilla_globals.json entries are now invalid (mod moved again)
- Check if any library stubs are now shadowing real updates (mod authors fixed their mods)
- File issues for new require() failures not yet covered

**After a popular mod gets a B42 update:**
- If the mod was in vanilla_globals.json: the pcall fallback handles it automatically (real module wins)
- If the mod was a library stub: verify the stub isn't interfering, then mark as resolved in JSON
- Close the relevant GitHub Issue

---

## Out of Scope

- **Brita's Weapon Pack / Arsenal**: Needs full rewrite, not a require() fix
- **ModOptions B41**: B42 has native replacement; mods should port to vanilla API
- **Filibuster Used Cars**: Animation system breakage, not a require() issue
- **Any fix that requires rewriting significant game logic**: Unbreaker fixes calling conventions, not gameplay

---

## Decision Log

| Date | Decision | Reason |
|------|----------|--------|
| 2026-04-22 | Public repo | JSON needs public raw URL; community issues = update mechanism |
| 2026-04-22 | require() override over package.preload | Kahlua preload support unverified; override pattern is testable |
| 2026-04-22 | pcall fallback pattern | Real module always wins; no manual JSON cleanup when mods update |
| 2026-04-22 | Steam Workshop = distribution | No HTTP from Lua needed; updates at game launch, before PZ loads |
| 2026-04-22 | Phase 1 before Phase 4 | Core mechanism unverified; no point building API stubs if require() override doesn't work |
