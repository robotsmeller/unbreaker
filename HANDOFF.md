# Unbreaker — Handoff

**Last Updated:** 2026-05-11 (end of Session 8)

```yaml
session: 8
continue_with: In-game probe under B42.18 — validate 134 existing redirects + 2 new candidates (Json, recipecode). Ship v0.5.0 only if probe passes.
blockers: none
status: Live on Steam Workshop (id 3721648770). v1.2.0 / data v0.4.0 public — verified safe under B42.18 per patch notes review. Data v0.5.0 staged on disk but NOT pushed.
```

## Session 8 Summary

PZ shipped **B42.18 Unstable** (2026-05-11). Reviewed the full Steam announcement patch notes:
- **MODDING section is purely additive.** New Java methods (`CraftRecipe.getModTags`/`setTags`, `InputScript.getItems`, `Zombie.doCrawlerSpeed`/`doSprinter`/etc.), new `SyncFactionServer` event, new Texture field for Trait scripts. No file moves, no renamed globals, no removed Lua APIs.
- **Conclusion:** the currently-live v1.2.0 / data v0.4.0 should continue to work under 42.18 without any changes shipped. Caveat: patch notes are a summary, not a diff — silent file relocations are possible but unlikely in a bug-fix patch.
- **Decision:** do NOT push v0.5.0 to the Workshop until in-game probe verifies. The live mod already covers 42.18 users.

Workshop communication posted (in-thread comment by Rob, 2026-05-11):
> "Fixes for 42.18 update coming today, but doesn't look like there are any require() changes so the current version should still work. Feel free to let me know here is there are other issues. If it works for you, spread the word, rate the mod — every bit helps. Thanks."

Changes staged on disk (not committed, not released):
- `data/vanilla_globals.json` → v0.5.0, last_updated 2026-05-11, added `verification_target: "B42.18"` field
- 2 candidate entries added (`verified: false`, so not shipped by generate_lua.py): `Json` → `Json`, `recipecode` → `recipecode` (both are Issue #4 unknowns)
- `mod/42/media/lua/shared/UnbreakerData.lua` regenerated (header v0.5.0; shipped redirect count unchanged at 134)
- `HANDOFF.md` + `.claude/context.md` updated

Pending for next session:
1. Run `python scripts/smoke_probe.py` under B42.18 — verify Unbreaker loads with 134 redirects and miss buffer is empty on a clean save
2. Run `python scripts/final_probe.py` — spot-check the v0.2.0 expansion redirects still resolve
3. Probe `_G.Json` and `_G.recipecode`. If non-nil and table-shaped: flip `verified: true`. If nil: reclassify category to `unrecoverable` and note PROBED B42.18.
4. If probe clean: bump `mod.info` modversion 1.2.0 → 1.2.1, run `scripts/build_workshop.ps1`, push to Workshop.
5. Issue #4 leftovers (not addressable today): `AquaConfig` (filename mismatch in AutotsarMotorClub port — needs that mod installed); three `YourDash/Z_PatchVehicleDashboard_*` (mod-internal filename mismatches — can't shim from vanilla, file as mod-request bug for YourDash author).
6. Monitor Workshop comments + diagnostic tool reports for surprise 42.18 regressions.

## Current State

**Unbreaker is live on the Workshop.** Public visibility, content uploaded, in-game test passed (`[Unbreaker] loaded v1.2.0 — 134 redirects`). Diagnostic tool live at robotsmeller.github.io/unbreaker. Issue #4 filed via the diagnostic tool's report flow, end-to-end verified.

Workshop URL: https://steamcommunity.com/sharedfiles/filedetails/?id=3721648770

## Post-Launch Actions

| # | Item | Status |
|---|------|--------|
| 1 | Verify tags actually appear on Workshop page | Pending — SteamCMD VDF tag formats both ignored by PZ. PZ in-game publisher folder is set up at `~/Zomboid/Workshop/Unbreaker/` as fallback. |
| 2 | Draft + post r/projectzomboid announcement | Pending |
| 3 | Indie Stone forums modding-section post | Pending |
| 4 | PZ modding Discord(s) — diagnostic tool announcement | Pending |
| 5 | Reach out to authors of mods Unbreaker covers | Ongoing |
| 6 | Triage Issue #4 (6 unknowns from launch session) | Pending |

## Promotion Strategy (drafted Session 7)

**Lead with the diagnostic tool**, not the mod. It's the unique value — paste console.txt, get a categorized answer. Frame Unbreaker as the engine behind the tool's "fixed" bucket.

**Tone:** Match the Workshop description — dry, direct, honest about Brita/Arsenal/True Actions being out of scope. PZ community rewards self-awareness over hype.

**Don't:** spam comments on broken mods, astroturf with alts, post identical content cross-platform within 24h.

## Workshop Publishing Lessons (Session 7)

These bit us during launch — recorded so they don't bite again:

- **`poster.png` is the Workshop thumbnail, NOT `preview.png`.** The names are reversed from what you'd expect on PZ Workshop. Updating only `preview.png` left a blank thumbnail in browse lists.
- **SteamCMD VDF doesn't escape strings the way you think.** `\n` passes through literally and renders as `\n` text on the page. `\"` truncates the string at the backslash-quote pair. Use real newlines for multi-line strings; replace any literal `"` in source with single quotes or curly quotes.
- **VDF re-pushes everything on every upload.** If the description field has a placeholder and you point SteamCMD at that file, your real description gets clobbered. Hence `workshop_item.template.txt` (placeholder) + `build/workshop_item.txt` (generated, full content spliced in by `scripts/build_workshop.ps1`).
- **Tags via SteamCMD VDF do not work for PZ.** Neither `tags { tag "..." }` nor `tags "comma,separated"` formats took. Use PZ's in-game Workshop publisher (`~/Zomboid/Workshop/<ModName>/workshop.txt`) for tag setting. Folder is already set up.
- **Workshop preview cap is 1 MB hard.** Steam returns "Limit exceeded" for oversized previews — same error name as rate limiting, easy to misdiagnose. Resize previews to 1024x1024 or 512x512 and re-encode.

## Diagnostic Tool

Static page at https://robotsmeller.github.io/unbreaker/

- Paste or drag-drop console.txt; processed entirely in-browser
- Simple/Advanced view toggle, light/dark/system theme toggle (all persist in localStorage)
- Simple view: status banner + plain-language stats + inline report button
- Advanced view: detailed module list with collapsible sections
- Unknown bucket has one-click "Open GitHub issue" button pre-filled with module list, label, title
- Fetches vanilla_globals.json from GitHub raw — always reflects current release
- Backtick + newline sanitization in issue body (no Markdown injection)
- Forbids literal `"` in description (build script throws — would have truncated the VDF push)

## Open Issues

- #2 [Smoke Like It's 93] Stray `require("Items/")` — self-broken, `unrecoverable`-class
- #3 [WaterPipes] Self-broken require `wp_vsquare`
- #4 Uncovered require() failures (6 modules) — filed via diagnostic tool. AquaConfig already in JSON unverified; `Json` and `recipecode` worth probing as vanilla candidates; three `YourDash/Z_PatchVehicleDashboard_*` look like filename mismatches.

## Open Questions

| # | Question | Notes |
|---|---|---|
| 1 | Multiplayer: does override cause checksum rejection? | Single-player verified. Untested MP. |
| 2 | SteamCMD 2FA strategy for CI publish | Phase 7 prerequisite |
| 3 | Phase 2: triage miss buffer | Post-launch, ongoing |

## What Exists

- `mod/42/media/lua/shared/Unbreaker.lua` — require() override with miss ring buffer, v1.2.0
- `mod/42/media/lua/shared/UnbreakerData.lua` — generated, 134 redirects
- `mod/42/mod.info` and top-level `mod/mod.info` — B42 layout, v1.2.0
- `mod/poster.png`, `mod/preview.png` — childish-art thumbnails, 1024x1024, ~360 KB each
- `data/vanilla_globals.json` — v0.4.0, 134 verified redirects
- `docs/index.html` — GitHub Pages diagnostic tool
- `scripts/generate_lua.py` — JSON → Lua generator
- `scripts/build_workshop.ps1` — builds Workshop content folder + generates VDF with description spliced in
- `scripts/final_probe.py` and `scripts/smoke_probe.py` — in-game verification probes
- `assets/workshop-description.txt` — Workshop page copy (BBCode, source of truth)
- `assets/unbreaker-childish.png` — master art for poster + preview
- `assets/preview-original-1024.png` — pre-resize backup of original preview
- `workshop_item.template.txt` — VDF template (description is placeholder, replaced at build time)
- `PUBLISH.md` — runbook
- `~/Zomboid/Workshop/Unbreaker/` — local PZ Workshop folder for in-game publisher (tags fallback)
- `.github/workflows/generate.yml` — CI regen on JSON change

## Session Summaries

### Session 7 (2026-05-07): Workshop launch
Set up SteamCMD pipeline (`scripts/build_workshop.ps1`, `workshop_item.template.txt`, `PUBLISH.md`). Hit and resolved every VDF gotcha: rate limit, 1MB preview cap, content folder layout (no `Contents/` wrapper), description clobbering, `\n` not interpreting, `\"` truncating. Discovered `poster.png` is the Workshop thumbnail, not `preview.png`. Tags don't work via SteamCMD VDF on PZ; PZ in-game publisher folder set up as fallback. Mod is now live and public.

### Session 6 (2026-05-07): Diagnostic tool + security hardening
Built docs/index.html GitHub Pages diagnostic tool (paste console.txt, get categorized results, one-click unknown issue filing). Soren audit found backtick injection (medium) and newline passthrough (low) in GitHub issue URL builder; both fixed. Updated README and workshop description to reference tool.
