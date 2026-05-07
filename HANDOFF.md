# Unbreaker — Handoff

**Last Updated:** 2026-05-07 (end of Session 6)

```yaml
session: 6
continue_with: Enable GitHub Pages in repo settings, then SteamCMD Workshop upload
blockers: none
status: Ship-ready. Diagnostic tool built and pushed.
```

## Current State

**Mod is at v1.2.0 with 134 verified redirects. Diagnostic tool is live on GitHub.**

One manual step to activate the diagnostic tool: enable GitHub Pages in repo settings
(Settings > Pages > Deploy from branch: main, folder: /docs).

## Publish Checklist

| # | Item | Status |
|---|------|--------|
| 1 | Move repo to neutral GitHub account | Done — github.com/robotsmeller/unbreaker |
| 2 | Update GitHub URL in `assets/workshop-description.txt` | Done |
| 3 | Update `url=` in `mod/42/mod.info` | Done |
| 4 | Enable GitHub Pages (Settings > Pages > main, /docs) | Pending |
| 5 | SteamCMD Workshop upload | Pending |
| 6 | Update Workshop footer link in `docs/index.html` with real Workshop ID | After #5 |
| 7 | Pin scoped comment on Workshop page day one | After #5 |

## Diagnostic Tool

Static page at https://robotsmeller.github.io/unbreaker/ (live once GitHub Pages enabled).

- Paste or drag-drop console.txt; processed entirely in-browser
- Categorizes require() failures: fixed / not fixable / library stub needed / unknown
- Unknown bucket has one-click "Open GitHub issue" button pre-filled with module list
- Fetches vanilla_globals.json from GitHub raw — always reflects current release

## Load Order (resolved)

Workshop installs use a numeric Steam folder ID which sorts before any alphabetically-named local mod. No mod ID rename needed. Local install load order is a documented limitation.

WARN messages in PZ logs (`require("X") failed`) are Java-level logging, not Lua failures. They fire before Unbreaker's redirect kicks in and appear even when Unbreaker successfully serves. Do not use WARNs as a failure metric.

## Post-Ship Work

- **Phase 2:** Triage miss buffer. Issues #1-3 are early Phase 2 candidates.
- **Multiplayer:** Untested. Single-player disclaimer is in Workshop description.
- **Kill-switch criteria:** Archive if TIS does a major API overhaul that invalidates >50% of redirects.

## What Exists

- `mod/42/media/lua/shared/Unbreaker.lua` — require() override with miss ring buffer, v1.2.0
- `mod/42/media/lua/shared/UnbreakerData.lua` — generated, 134 redirects
- `mod/42/mod.info` and top-level `mod/mod.info` — B42 layout, v1.2.0
- `data/vanilla_globals.json` — v0.4.0, 134 verified redirects
- `docs/index.html` — GitHub Pages diagnostic tool
- `scripts/generate_lua.py` — JSON -> Lua generator
- `scripts/final_probe.py` — full live verification + miss dump
- `scripts/smoke_probe.py` — quick architecture sanity check
- `assets/workshop-description.txt` — Workshop page copy (BBCode formatted)
- `mod/poster.png`, `mod/preview.png` — clean thumbnails for Workshop
- `.github/workflows/generate.yml` — CI regen on JSON change

## Repo Layout

```
data/vanilla_globals.json        # source of truth (134 redirects)
docs/
  index.html                     # GitHub Pages diagnostic tool
scripts/
  generate_lua.py                # JSON -> Lua codegen
  smoke_probe.py                 # architecture probe
  final_probe.py                 # full live verification + miss dump
mod/
  mod.info                       # outer (B42 layout marker)
  poster.png / preview.png       # Workshop thumbnails
  42/
    mod.info
    media/lua/shared/
      Unbreaker.lua              # the override
      UnbreakerData.lua          # GENERATED — never edit by hand
assets/
  workshop-description.txt      # Workshop page copy
.github/workflows/generate.yml   # CI regen on JSON change
```

## Open Questions

| # | Question | Notes |
|---|---|---|
| 1 | Multiplayer: does override cause checksum rejection? | Single-player verified. Untested MP. |
| 2 | SteamCMD 2FA strategy for CI publish | Phase 7 prerequisite |
| 3 | Phase 2: triage miss buffer | Post-ship work |

## Session Summaries

### Session 6 (2026-05-07): Diagnostic tool + security hardening
Built docs/index.html GitHub Pages diagnostic tool (paste console.txt, get categorized results, one-click unknown issue filing). Soren audit found backtick injection (medium) and newline passthrough (low) in GitHub issue URL builder — both fixed. Updated README and workshop description to reference tool.

### Session 5 (2026-05-07): Collab audit fixes + Phase 2/3 redirect expansion
Soren+Atlas audit fixed verified filter, added CI validation gate, capped missSeen, removed dead alias branch. Two in-game probes expanded redirects 27 -> 96 -> 134 (all verified live B42.17). Version bumped to 1.2.0.
