# Unbreaker — Handoff

**Last Updated:** 2026-04-22 (end of Session 1)

```yaml
session: 2
continue_with: Proof-of-concept test mod — verify require() override works in PZ Kahlua
blockers: none
```

## Current State

Project scaffolded. No functional Lua code yet. Research complete.
The single most important unknown before writing any real code:
**Does overriding the global `require` function work in PZ's Kahlua environment?**

## What Exists

- Folder structure and all context/config files
- GitHub repo (public): TBD
- ROADMAP.md with full task breakdown
- vanilla_globals.json seeded with 12 known redirects from PZ Mod Checker diagnose data
- Issue templates for mod requests and bug reports

## What Needs Doing (see ROADMAP.md for detail)

1. **Test mod** — 20-line Lua mod that overrides require() and verifies interception works
2. **generate_lua.py** — converts vanilla_globals.json to UnbreakerData.lua
3. **Unbreaker.lua** — main mod file, the actual require() override
4. **Load order solution** — test whether alphabetical naming is sufficient
5. **damnlib API research** — read source to understand what API surface is needed
6. **GitHub Actions** — auto-generate UnbreakerData.lua on data changes
7. **Workshop publish** — SteamCMD workflow, requires Steam credentials as repo secrets
8. **PZ Mod Checker integration** — PZMC diagnose page gets "Generate Shim" button

## Open Questions

| # | Question | Urgency |
|---|----------|---------|
| 1 | Does require() global override work in PZ Kahlua? | BLOCKER |
| 2 | Does PZ register all mod Lua paths before any mod code runs? | High |
| 3 | Does alphabetical mod naming guarantee load-before-others? | High |
| 4 | What is the damnlib API surface KI5 mods actually use? | Medium |
| 5 | Does tsarslib B42 Tchernobill port expose same API as B41? | Medium |
| 6 | SteamCMD in GitHub Actions — does it require 2FA bypass setup? | Medium |

## Session 1 Summary

Spun out of PZ Mod Checker. Research established:
- Steam Workshop is the distribution mechanism (updates at game launch, no HTTP from Lua needed)
- require() override with pcall fallback is the right pattern (real module always wins)
- Two library mods (damnlib, tsarslib) gate ~15-20M combined mod subscriptions
- 12 vanilla global redirects identified from live diagnose data
- Public repo is correct (JSON needs public raw URL, community issues = update mechanism)
