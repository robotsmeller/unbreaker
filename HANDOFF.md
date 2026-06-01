# Unbreaker — Handoff

**Last Updated:** 2026-06-01 (end of Session 9)

```yaml
session: 9
continue_with: Restore the Workshop description by hand in the Steam app (the v1.2.1 push reverted it to the launch copy). Then promotion — r/projectzomboid post leading with the diagnostic tool.
blockers: none
status: Live on Steam Workshop (id 3721648770). v1.2.1 / data v0.6.0 public, verified live under B42.19. 135 redirects.
```

## Current State

**Unbreaker v1.2.1 is live and public** on the Workshop (id 3721648770), confirmed server-side after the Session 9 push (visibility public, time_updated current). Data v0.6.0, 135 redirects, all probed live under B42.19. Diagnostic tool live at robotsmeller.github.io/unbreaker. **GitHub issue tracker is empty — #2 through #6 all closed.**

Workshop URL: https://steamcommunity.com/sharedfiles/filedetails/?id=3721648770

## Immediate Follow-ups

| # | Item | Status |
|---|------|--------|
| 1 | Restore Workshop description in the Steam app | **Needed** — the v1.2.1 push clobbered manual edits; prior text is unrecoverable. Pipeline now never pushes the description. B42.19 line drafted (Session 9 summary). |
| 2 | r/projectzomboid announcement (lead with the diagnostic tool) | Pending |
| 3 | Indie Stone forums + PZ modding Discord posts | Pending |
| 4 | Outreach to authors of mods Unbreaker covers | Ongoing |
| 5 | Verify tags appear on Workshop page (PZ in-game publisher if VDF didn't take) | Pending |
| 6 | Monitor Workshop comments + diagnostic reports for new B42.x patch regressions | Ongoing |

## What Exists (current)

- `mod/42/media/lua/shared/Unbreaker.lua` — require() override + miss ring buffer, v1.2.1
- `mod/42/media/lua/shared/UnbreakerData.lua` — generated, 135 redirects
- `mod/mod.info` + `mod/42/mod.info` — B42 layout, modversion 1.2.1
- `data/vanilla_globals.json` — v0.6.0; `vanilla_global` + `unrecoverable` categories
- `scripts/generate_lua.py` — JSON → Lua generator (skips unrecoverable + unverified)
- `scripts/build_workshop.ps1` — builds Workshop folder + VDF. NO description field (never pushed)
- `scripts/smoke_probe.py`, `scripts/final_probe.py` — in-game verification probes
- `scripts/issue_probe.py`, `scripts/issue_probe_followup.py` — issue-triage probes (Class A discovery via `rawget(_G, basename)`)
- `docs/index.html` — GitHub Pages diagnostic tool
- `assets/workshop-description.txt` — reference copy of the launch description (NOT the live source of truth; description is hand-managed in Steam)
- `workshop_item.template.txt` — VDF template, no description line
- `PUBLISH.md` — runbook
- `.claude/hooks/session-issues.sh` — SessionStart hook listing open issues by status (activates next session)
- `~/Zomboid/Workshop/Unbreaker/` — local PZ Workshop folder (tags fallback)

## Probe Mechanism (for next data change)

Probes ship Lua into a running PZ via the PZ Test Pilot harness (`C:/xampp/htdocs/pz-test-pilot`, `run_lua` IPC). PZ must be in a loaded world, window focused and unpaused. For a new vanilla candidate: probe `pcall(require, name)` + `rawget(_G, basename)` — if the global exists, redirect to it (`verified: true`). Shared Lua loads at game boot, so a **full restart** is required to pick up regenerated data, and the loaded mod must be the dev build. Watch the id collision: three Unbreaker copies can exist on disk (Steam sub, `~/Zomboid/mods`, `~/Zomboid/Workshop` staging) — enable only one, or update all of them.

## Workshop Publishing Lessons

- **`poster.png` is the Workshop thumbnail, NOT `preview.png`** (names inverted on PZ).
- **NEVER push the description** — it overwrites manual Steam-app edits. The VDF now omits the field; the build script throws if it is reintroduced. (Memory: workshop-description-never-push)
- **SteamCMD VDF:** `\n` passes through literally (use real newlines); `\"` truncates (no literal `"`).
- **Tags don't work via VDF on PZ** — use the in-game publisher (`~/Zomboid/Workshop/<ModName>/workshop.txt`).
- **Preview cap 1 MB** (Steam returns the same error name as a rate limit).
- **Cached SteamCMD credentials** logged in unattended this session — no 2FA prompt on `+login robotsmeller`.

## Open Questions

| # | Question | Notes |
|---|---|---|
| 1 | Multiplayer: does the override cause checksum rejection? | Single-player verified; MP untested. |
| 2 | SteamCMD 2FA for CI publish | Credentials cached locally for now; CI strategy still open. |

## Session Summaries

### Session 9 (2026-06-01): B42.19 verification + CFarmingSystem fix, shipped v1.2.1
Reviewed B42.19 Unstable (no modding breakage). Live-probed Issue #5/#6 modules: added `Farming/CFarmingSystem` (verified in-game), reclassified `Json`/`recipecode`/`Items/ItemFactory`/`Maps/ISMapDefinitions` as unrecoverable. Bumped to v1.2.1 / data v0.6.0 (135 redirects), pushed to Workshop (live, public). Closed all issues #2–#6. Removed the description from the publish pipeline after a push clobbered Rob's manual Steam edits. Added a SessionStart issue hook; repaired the fetch MCP server.

### Session 8 (2026-05-11): B42.18 update prep
Reviewed B42.18 patch notes (MODDING purely additive, no breakage). Staged data v0.5.0 + 2 candidates (Json, recipecode), held release pending in-game probe. Live v1.2.0 / data v0.4.0 confirmed safe for 42.18 users.
