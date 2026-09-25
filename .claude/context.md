# Unbreaker Context

```yaml
version: 1.4.1
data_version: 0.8.0
status: v1.4.1 LIVE on the Workshop (updated 2026-09-25 10:36). 143 redirects + 1 vanilla-lua patch. Verified in game on 42.21.0 unstable; 42.20.4 stable cleared statically (preset reader byte-identical between the two).
created: 2026-04-22
session: 16
last_updated: 2026-09-25
verification_target: B42.21.0 unstable (verified in game) and B42.20.4 stable (static). Rob's install is now on the unstable branch.
continue_with: Nothing is blocked. Next real work is pz-mod-checker's getText arity rule and committing its old uncommitted feature. Re-diff when 42.21 reaches stable or 42.22 lands.
blockers: Standing HARD RULE, the agent NEVER touches Steam/Workshop. No SteamCMD, no publish, not build_workshop.ps1. Rob runs those.

workshop:
  id: 3721648770
  url: https://steamcommunity.com/sharedfiles/filedetails/?id=3721648770
  visibility: public
```

## To Resume

Session 17. Unbreaker main at v1.4.1 / data v0.8.0, 143 redirects, 0 open issues, live on Workshop.
Siblings: `pz-mod-checker`, `pz-shims` (public, 4 shims), `pz-test-pilot`, `pz-head-for-the-hills`.

THIS WINDOW:
1. **pz-mod-checker**: commit or discard the long-uncommitted feature (`gui/server.py`,
   `gui/static/index.html`, `README.md`, untracked `unbreaker.py`), then refresh its stale
   `context.md` (session 10).
2. **pz-mod-checker getText arity rule** (see Two Kinds of Fix below).
3. When TIS moves 42.21 to stable or ships 42.22: diff against `C:\pz-baselines\` (copy the old
   `media/lua` there FIRST, before Steam updates), then `python scripts/smoke_probe.py` in a world.

## Supporting both branches (decided s16)

Players run stable and unstable at once. Never key behaviour on branch or version number; test
whether the thing exists. Redirects already do (`rawget`). The preset patch runs vanilla's reader
and ours on every read and only uses ours when vanilla's output matches the known truncation, else
steps aside (`tests/lua/test_outfit_guard.lua`, run with `lua`). Version ranges belong only in
pz-mod-checker, which has no live game to probe (`since` + `fixed_in`).

## Method: diff builds, do not read changelogs

Baselines live in `C:\pz-baselines\<version>\` (42.20.4 saved s16; diff list to 42.21 in
`C:\pz-baselines\diff-42.20.4-42.21.txt`). Use `diff -rq --strip-trailing-cr`, and check `Only in`
lines separately: a DELETED file breaks a redirect (`ISFarmingCursor`, 42.20). A file diff cannot
see Java-side changes. The community vanilla-lua repo lags; the install is the source of truth.
For logic that only moved or was reformatted, a token-level diff (comments and whitespace stripped)
separates real changes from noise; s16 used it on `ISMoveableSpriteProps.lua`.

## Two kinds of fix

- **Redirects** (`data/vanilla_globals.json` to `UnbreakerData.lua`): broken `require()` to a
  vanilla global. 143 shipped, 152 rows (9 unverified/unrecoverable staged).
- **Vanilla patches** (`mod/42/media/lua/client/UnbreakerPatches.lua`): bugs in BASE GAME lua.
  Boot line: `[Unbreaker] vanilla patches applied: N/M (game <build>)`, then
  `[Unbreaker] saved-outfit reader: <verdict>` on first use. MUST be tested in game before
  publishing (s13 blanked the preset dropdown on a file-local it could not see).
- **NOT here:** mod-specific patches go to `pz-shims`.

**getText arity (42.20.2)**: 76 vanilla call sites swept from `getText("KEY")` to
`getText("KEY", "")`. The engine wants one argument per format specifier. Tractable
pz-mod-checker rule: call arity vs specifier count, both inside the mod.

## Core Pattern

`require` is overridden; on failure returns `rawget(_G, entry.global)`. B42 returns nil silently for
missing modules, so check `(ok and result ~= nil)`. PZ logs `require(...) failed` even for modules
Unbreaker redirects; a "failed" line is not proof of breakage.

## What It Cannot Fix

Deep API rewrites; mod-internal modules; modules with no vanilla global (`Json`, `recipecode`,
`Items/ItemFactory`, `Maps/ISMapDefinitions`, `ISLootWindowControlHandler`); Brita/Arsenal/True
Actions; multiplayer (untested); `loadstring` (host-level, and restoring it restores the hole).
Removed upstream: `CharacterCustomisationPanel`, `CommonTemplates`, `ISFarmingCursor` (42.20).

## Files Worth Knowing

- `mod/42/media/lua/shared/Unbreaker.lua` (require override), `.../client/UnbreakerPatches.lua`
- `scripts/smoke_probe.py`: needs Test Pilot enabled AND a loaded world (heartbeat is `OnTick`),
  and `loadstring` (42.21+). Now sweeps all redirects (`full_sweep`); SimpleSilencers misses are
  expected without that mod.
- `scripts/watch.py` + `notify.ps1`: comment watcher. Test with `--simulate N`, never edit state.
- `scripts/build_workshop.ps1` + SteamCMD: ROB RUNS THESE. PZ's in-game uploader refuses the
  1024px `preview.png` (wants 256x256), so SteamCMD is the publish path. See `PUBLISH.md`.
- `workshop_item.template.txt`: VDF, NO `description` field by design.

## GOTCHA: four copies of Unbreaker

repo `mod/`; `~/Zomboid/mods/Unbreaker` (dev); `~/Zomboid/Workshop/Unbreaker/Contents/mods/Unbreaker`
(**PZ loads this**); Steam `workshop/content/108600/3721648770`. First three at v1.4.1. Confirm
with the console line, never `mod.info`. Do not touch `workshop.txt` in staging.

## Pending

1. **pz-mod-checker uncommitted feature + stale context** (To Resume 1).
2. **Rob's 4 damaged presets** (Zane, Theo, Hunter, Billy) need rebuilding once. Backup at
   `~/Zomboid/Lua/saved_outfits.txt.bak.pre-v140`.
3. **`Vehicles/VehicleUtils` unproven in practice.** Promoted on static evidence.

## Recent Sessions

### Session 16 (2026-09-25): 42.21 unstable, v1.4.1 shipped for both branches
42.21 went to unstable 2026-09-23 and re-enabled `loadstring`/`loadstream`. Decided Unbreaker must
work on stable and unstable at once without version checks, which exposed that the preset patch
replaced vanilla's reader wholesale. Added the compare-both-readers guard, the build number in the
boot line, and a corrected `mod.info` description; v1.4.1. Verified in game on 42.21.0: patch
applied, fixed reader used, five presets listed, `saved_outfits.txt` unchanged, 141/143 redirects
resolve live (2 SimpleSilencers misses, mod absent). 42.21 diff: 641 files changed, one moved
(`ISRadioAction` client to shared, global intact), none deleted. Rob published via SteamCMD.
Siblings: Test Pilot already feature-detects `loadstring`, only its CLAUDE.md note changed;
pz-mod-checker gained `b42-20-4-loadstring-removed` (fixed_in 42.21.0); Head for the Hills clean
(its mirrored door/stairs logic did not change, it calls Java directly).

### Session 15 (2026-08-26): 42.20.4 removes loadstring, both live mods unaffected
Security hotfix removed `loadstring`/`loadstream`. Unbreaker and Head for the Hills never used
either. Test Pilot's inline `run_lua` went dark on stable. Fetching note: the Indie Stone forum's
`og:description` is truncated for long posts; Steam's news API
(`ISteamNews/GetNewsForApp/v2/?appid=108600&maxlength=0`) gives full notes.

### Session 14 (2026-08-05): comment watcher built, 42.20.2 cleared statically
Built `scripts/watch.py` + `notify.ps1` (Steam + GitHub comments to Telegram every 20 min; the
scheduled task and `%LOCALAPPDATA%\pz-watch\` are machine state, not in git). Self-authored items
tagged `OWN` and suppressed. Found 42.20.2's real change is `getText` arity.
