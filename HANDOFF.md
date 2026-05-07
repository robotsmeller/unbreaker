# Unbreaker — Handoff

**Last Updated:** 2026-05-07 (end of Session 3)

```yaml
session: 4
continue_with: Pre-ship blockers — CI path fix, load order / mod ID decision, then publish
blockers: none
status: In-game validated. Pre-ship items identified. Ready to ship after ~5 code changes + mod ID decision.
```

## Current State

**Phase 1 is done and re-validated in Session 3.**

In-game probe against a live new-game session confirmed:
- 141 broken require() calls intercepted
- 139 served correctly (98.6%)
- 2 unserved — both already documented unrecoverable (ISLootWindowControlHandler, VehicleUtils)
- All 13 spot-checked redirects return valid tables

**Collab audit (plan-review.md) completed Session 3.** Overall verdict: CAUTION — ship-ready after ~8 concrete pre-ship items. Architecture is sound, gaps are operational.

## Critical Pre-Ship Items (from collab audit + Session 3 findings)

### Blockers (must fix before publish)

| # | Item | File | Detail |
|---|------|------|--------|
| 1 | CI workflow path wrong | `.github/workflows/generate.yml:28` | `mod/media/...` → `mod/42/media/...` — workflow never successfully regenerated since B42 layout migration |
| 2 | Mod ID / load order decision | `mod/42/mod.info`, `mod/mod.info` | "Unbreaker" sorts late alphabetically. Some mods' load-time require() calls fire before Unbreaker's hook installs. Must decide on mod ID before first Workshop publish — permanent once listed. |

### Non-blocking but do before publish

| # | Item | File | Detail |
|---|------|------|--------|
| 3 | Remove alias dead code | `mod/42/media/lua/shared/Unbreaker.lua:64-75` | Zero JSON entries use `alias`. Has latent bug: resolveGlobal(entry.alias) treats module paths as global names. Remove until there's data. |
| 4 | Bump version | Both `mod.info` files + `Unbreaker.lua` | `0.1.0-dev` → `1.0.0` |
| 5 | Fix generator docstring | `scripts/generate_lua.py:5` | States old output path |
| 6 | AquaConfig comment | `data/vanilla_globals.json` | Document why verified:false is intentional (can't verify without mod installed) |
| 7 | Workshop description | — | Must name Brita/Arsenal/True Actions explicitly in paragraph one. See draft below. |
| 8 | Thumbnail | `mod/preview.png`, `mod/poster.png` | Unwatermark the Gemini image at `C:\Users\roban\Downloads\unbreaker.png` |
| 9 | Push to GitHub remote | — | Never pushed. Repo exists locally and on GitHub but not synced. |

## Load Order Finding (Session 3)

**The WARN messages in PZ logs (`require("X") failed`) are Java-level PZ logging, NOT Lua-level failures.** They fire when the native `_require()` fails, which happens before Unbreaker's redirect kicks in. The WARNs appear even when Unbreaker successfully serves the redirect. Do NOT use WARNs as a failure metric.

**Real load order issue:** "Unbreaker" alphabetically sorts after mods like "kattaj1_42_17_shim", "SimpleSilencers", "SkullysDufflesAndRigs". Their top-level Lua runs before Unbreaker's hook installs. Those load-time calls are genuinely missed.

**Mitigation:** For Workshop-installed mods, the mod folder is a numeric Steam Workshop ID (e.g. `3000000000`). Digits sort before letters in ASCII, so Workshop Unbreaker likely loads before alphabetically-named local mods. Load order may only be a problem for local installs. **Needs empirical test.**

**Options:**
- Change mod ID to something that sorts early (e.g. `!Unbreaker`, `000Unbreaker`) — ugly but effective for local installs
- Keep "Unbreaker", document the limitation, rely on Workshop numeric ID sort order
- **Decision needed before publish** — mod ID is permanent on Workshop

## Collab Audit Key Findings (plan-review.md)

Full plan at `c:\xampp\htdocs\unbreaker\plan-review.md`.

- **Ship strategy:** Option C "Tiered Ship" — ship with 27 redirects now. Phase 2 (303-entry triage) is post-ship work. Don't block publish on batch probe.
- **Don't build:** GitHub Pages form, community feedback pipeline, CONTRIBUTING.md — premature. No contributors yet.
- **Workshop description:** Name Brita, Arsenal, True Actions explicitly in paragraph 1. Pin a scoped comment on day one.
- **Silent success problem:** When Unbreaker works, players see nothing. Review-to-subscriber ratio will skew negative. Accept this.
- **MP:** Untested. Single-player disclaimer required.
- **Kill-switch:** Define criteria before publish (e.g. "archive if TIS does a major API overhaul that invalidates >50% of redirects").

## Workshop Description Draft

```
⚠️ Does NOT fix Brita's Weapon Pack, Arsenal[26], or True Actions. Those need deep
rewrites only the mod authors can do.

Keeps your mods working between PZ patches. Fixes broken require() calls, renamed
functions, and moved globals — the minor API shuffles that come with almost every
weekly update. When a mod's author publishes a proper fix, Unbreaker automatically
steps aside. Stopgap, not a replacement.

Verified: B42.17, 180-mod install, 98.6% of broken require() calls served.
Single-player only — multiplayer untested.
```

## What Exists

- `mod/42/media/lua/shared/Unbreaker.lua` — require() override with miss ring buffer
- `mod/42/media/lua/shared/UnbreakerData.lua` — generated, 27 redirects
- `mod/42/mod.info` and top-level `mod/mod.info` — B42 layout
- `data/vanilla_globals.json` — v0.2.0, 27 redirects
- `scripts/generate_lua.py` — JSON → Lua generator
- `scripts/smoke_probe.py` — quick architecture sanity check
- `scripts/probe_misses.py` — candidate redirect checker
- `scripts/final_probe.py` — full live verification + miss dump
- `plan-review.md` — collab audit pre-flight brief (Session 3)
- `.github/workflows/generate.yml` — CI regen (PATH IS WRONG — see blocker #1)

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
.github/workflows/generate.yml   # CI regen on JSON change (PATH BUG — fix first)
plan-review.md                   # collab audit output
```

## Open Questions

| # | Question | Notes |
|---|---|---|
| 1 | Load order: does Workshop numeric ID sort before alphabetic local mods? | Test empirically — affects whether mod ID change is needed |
| 2 | Mod ID decision: keep "Unbreaker" or rename for early sort? | Must decide before Workshop publish |
| 3 | Multiplayer: does override cause checksum rejection? | Single-player verified. Untested MP. |
| 4 | SteamCMD 2FA strategy for CI publish | Phase 7 prerequisite |
| 5 | Phase 2: triage 303-entry miss buffer | Post-ship work |
