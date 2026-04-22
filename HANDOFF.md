# Unbreaker — Handoff

**Last Updated:** 2026-04-22 (end of Session 1)

```yaml
session: 2
continue_with: Phase 1 proof-of-concept — write test mod, verify require() override works in PZ Kahlua
blockers: none
```

## Current State

Fully scaffolded, documented, repo live. No functional Lua code yet.
Everything blocks on one empirical test: does the require() override work in PZ's Kahlua?

**Repo:** https://github.com/rob-kingsbury/unbreaker

## What Exists

- Full folder structure and context files
- SCOPE.md — definitive document on what Unbreaker can/can't fix
- ROADMAP.md — 7-phase plan with decision log
- vanilla_globals.json — 15 entries seeded from live PZMC diagnose data (all unverified)
- GitHub Actions workflow for auto-generating UnbreakerData.lua
- Issue templates for mod requests and stub interference reports

## Session 1 Decisions

| Decision | Rationale |
|----------|-----------|
| Public repo | JSON needs public raw URL; community issues = update mechanism |
| require() override over package.preload | Kahlua preload support unverified |
| pcall fallback pattern | Real module always wins automatically when mods update |
| Steam Workshop = distribution, not HTTP | Updates at game launch, no Lua networking needed |
| "Unbreaker" name retained | Tongue-in-cheek, clearly mod-scoped, not confused with in-game items |
| Scope: polyfill, not bridge | Not B41->B42 compatibility; patch buffer for active weekly PZ development |
| Translation shim excluded | Requires filesystem access unavailable in Kahlua |
| Multiplayer: unverified | Must test before recommending for MP servers |
| Brita/Arsenal/True Actions: out of scope | Need full rewrites, not shimming |

## Phase 1 Tasks (next session)

1. Write 20-line test mod in `mod/` — one require() override, one stub, verify interception
2. Test in PZ singleplayer — does it intercept? Does real module win via pcall?
3. Test load order — does alphabetical naming guarantee loading before other mods?
4. Document results in `.claude/context.md`
5. If test passes: write `scripts/generate_lua.py`
6. If test passes: write `mod/media/lua/shared/Unbreaker.lua` (full implementation)
7. Write `mod/mod.info`

## Open Questions

| # | Question | Urgency |
|---|----------|---------|
| 1 | Does require() global override work in PZ Kahlua? | BLOCKER — test first |
| 2 | Does PZ register all mod Lua paths before any mod code runs? | High |
| 3 | Does alphabetical mod naming guarantee load-before-others? | High |
| 4 | Multiplayer: does override cause checksum rejection? | Medium |
| 5 | What is the damnlib API surface KI5 mods actually call? | Medium (Phase 4) |
| 6 | Does tsarslib B42 Tchernobill port expose same API as B41? | Low (Phase 5) |
| 7 | SteamCMD GitHub Actions — 2FA bypass setup needed? | Low (Phase 7) |

## What Unbreaker Actually Fixes (summary — see SCOPE.md for full detail)

**Can fix:**
- require() failures where the module is a vanilla global (moved to auto-loaded scope)
- require() failures where a mod requires its own file under the wrong name
- Renamed functions / method aliases
- Moved globals

**Cannot fix:**
- Deep API rewrites (crafting, animation, vehicle physics)
- Missing mod dependencies (empty stub silences crash but doesn't restore function)
- Translation file gaps (no filesystem access in Kahlua)
- Multiplayer (unverified)
- Mods needing full rewrites (Brita, Arsenal, True Actions)

## Relationship to PZ Mod Checker

Unbreaker is standalone — no PZMC required.
PZMC integration is Phase 6: diagnose page notes which failures Unbreaker would fix,
links to Workshop page. Optional, additive.

## Workshop Description Draft

> Keeps your mods working between PZ patches. Fixes broken require() calls, renamed
> functions, and moved globals — the minor API shuffles that come with almost every
> weekly update. Does NOT fix mods needing deep rewrites. When a mod's author publishes
> a proper fix, Unbreaker automatically steps aside. Stopgap, not a replacement.
