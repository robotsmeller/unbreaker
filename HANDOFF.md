# Unbreaker — Handoff

**Last Updated:** 2026-05-07 (end of Session 4)

```yaml
session: 5
continue_with: Move repo to neutral GitHub account, update URLs, then SteamCMD Workshop publish
blockers: none
status: Ship-ready. All pre-ship items complete.
```

## Current State

**All pre-ship items are done. Ready to publish.**

Session 4 completed every item from the Session 3 collab audit:
- CI workflow path fixed (`mod/media/...` → `mod/42/media/...`)
- Mod ID decision: keep `Unbreaker`. Workshop numeric ID sorts before alphabetic local mods.
- Alias dead code removed from `Unbreaker.lua`
- Version bumped to `1.0.0` in Lua + both mod.info files
- Generator docstring corrected
- Workshop description written and humanizer-audited (`assets/workshop-description.txt`)
- Thumbnails verified clean (`mod/poster.png`, `mod/preview.png`)
- Pushed to GitHub remote

## Publish Checklist

| # | Item | Status |
|---|------|--------|
| 1 | Move repo to neutral GitHub account (not rob-kingsbury) | Done — github.com/robotsmeller/unbreaker |
| 2 | Update GitHub URL in `assets/workshop-description.txt` | Done |
| 3 | Update `url=` in `mod/42/mod.info` | Done |
| 4 | SteamCMD Workshop upload | After #2-3 |
| 5 | Pin scoped comment on Workshop page day one | After publish |

## Load Order (resolved)

Workshop installs use a numeric Steam folder ID which sorts before any alphabetically-named local mod. No mod ID rename needed. Local install load order is a documented limitation.

WARN messages in PZ logs (`require("X") failed`) are Java-level logging, not Lua failures. They fire before Unbreaker's redirect kicks in and appear even when Unbreaker successfully serves. Do not use WARNs as a failure metric.

## Post-Ship Work

- **Phase 2:** Triage 303-entry miss buffer from Session 2 probe. Issues #1-3 are early Phase 2 candidates.
- **Multiplayer:** Untested. Single-player disclaimer is in Workshop description.
- **Kill-switch criteria:** Archive if TIS does a major API overhaul that invalidates >50% of redirects.

## What Exists

- `mod/42/media/lua/shared/Unbreaker.lua` — require() override with miss ring buffer, v1.0.0
- `mod/42/media/lua/shared/UnbreakerData.lua` — generated, 27 redirects
- `mod/42/mod.info` and top-level `mod/mod.info` — B42 layout, v1.0.0
- `data/vanilla_globals.json` — v0.2.0, 27 redirects
- `scripts/generate_lua.py` — JSON → Lua generator
- `scripts/final_probe.py` — full live verification + miss dump
- `scripts/smoke_probe.py` — quick architecture sanity check
- `assets/workshop-description.txt` — Workshop page copy (BBCode formatted)
- `assets/unbreaker-thumbnail-master.png` — master thumbnail
- `mod/poster.png`, `mod/preview.png` — clean thumbnails for Workshop
- `plan-review.md` — collab audit output (Session 3)
- `.github/workflows/generate.yml` — CI regen on JSON change (path fixed)

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
  poster.png                     # Workshop thumbnail
  preview.png                    # Workshop thumbnail
  42/
    mod.info
    media/lua/shared/
      Unbreaker.lua              # the override
      UnbreakerData.lua          # GENERATED — never edit by hand
assets/
  workshop-description.txt      # Workshop page copy
  unbreaker-thumbnail-master.png
.github/workflows/generate.yml   # CI regen on JSON change
plan-review.md                   # collab audit output
```

## Open Questions

| # | Question | Notes |
|---|---|---|
| 1 | Multiplayer: does override cause checksum rejection? | Single-player verified. Untested MP. |
| 2 | SteamCMD 2FA strategy for CI publish | Phase 7 prerequisite |
| 3 | Phase 2: triage 303-entry miss buffer | Post-ship work |

## Session Summaries

### Session 4 (2026-05-07): Pre-ship hardening + publish prep
Completed all 9 pre-ship items from collab audit. Fixed CI path, removed alias dead code, bumped to v1.0.0, wrote and humanizer-audited Workshop description, verified thumbnails clean, pushed to GitHub. Decided mod ID: keep Unbreaker. Noted repo move to neutral account needed before publish.

### Session 3 (2026-05-07): In-game validation + pre-ship planning
Re-validated in live B42.17. 141 intercepted, 139 served (98.6%). Confirmed WARN messages are Java-level noise, not Lua failures. Identified load order issue for local installs. Collab audit completed — ship strategy: Option C (27 redirects now, Phase 2 post-ship).
