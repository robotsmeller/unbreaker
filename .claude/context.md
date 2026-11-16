# Unbreaker Context

```yaml
version: 1.4.1
data_version: 0.8.0
status: v1.4.1 LIVE on the Workshop. 143 redirects + 1 vanilla-lua patch. Verified in game on 42.22.2 stable 2026-11-15 (patch applied, fixed preset reader used, 141/143 redirects resolve, the 2 misses are SimpleSilencers with the mod absent). No release needed for 42.22.
created: 2026-04-22
session: 17
last_updated: 2026-11-15
verification_target: B42.22.2 stable (verified in game). Rob's install is on the public branch. TIS renamed Unstable to Pre-Release with 42.22.
continue_with: Nothing queued. When the next pre-release lands, save its media/lua as a baseline first, then diff against C:\pz-baselines\42.22.2\. Sibling work lives in pz-mod-checker (#23, #2).
blockers: Standing HARD RULE, the agent NEVER touches Steam/Workshop. No SteamCMD, no publish, not build_workshop.ps1. Rob runs those. main is PR-only on GitHub (unbreaker and pz-mod-checker); the agent may push a branch and open a PR, Rob merges.

workshop:
  id: 3721648770
  url: https://steamcommunity.com/sharedfiles/filedetails/?id=3721648770
  visibility: public
```

## To Resume

Session 18. Unbreaker main at v1.4.1 / data v0.8.0 (c83c3da), 143 redirects, 0 open issues, 0 open PRs, live on Workshop.
Siblings: `pz-mod-checker` (84 rules through 42.22), `pz-shims` (public, 4 shims), `pz-test-pilot`, `pz-head-for-the-hills`.

THIS WINDOW:
1. When TIS ships the next pre-release or stable: copy the installed `media/lua` to
   `C:\pz-baselines\<version>\` FIRST, before Steam updates, then diff against 42.22.2, read
   changed return types from `projectzomboid.jar` if needed, then `python scripts/smoke_probe.py`
   in a loaded world.
2. Otherwise Unbreaker has no queued work. pz-mod-checker's next is #23 or #2 (its own context.md).

## Supporting both branches (decided s16)

Players run stable and pre-release at once. Never key behaviour on branch or version number; test
whether the thing exists. Redirects already do (`rawget`). The preset patch runs vanilla's reader
and ours on every read and only uses ours when vanilla's output matches the known truncation, else
steps aside (`tests/lua/test_outfit_guard.lua`, run with `lua`). Version ranges belong only in
pz-mod-checker, which has no live game to probe (`since` + `fixed_in`).

## Method: diff builds, do not read changelogs

Baselines live in `C:\pz-baselines\<version>\lua` (42.20.4 and 42.22.2; no 42.21, Steam updated
first). Diff lists: `diff-42.20.4-42.21.txt`, `diff-42.20.4-42.22.2.txt`. Use
`diff -rq --strip-trailing-cr`, and check `Only in` lines separately: a DELETED file breaks a
redirect (`ISFarmingCursor`, 42.20). A file diff cannot see Java-side changes; read method
descriptors out of `projectzomboid.jar` instead (s17 did it with a small Python class reader, the
bundled JRE has no `javap`). The install is the source of truth.

## Two kinds of fix

- **Redirects** (`data/vanilla_globals.json` to `UnbreakerData.lua`): broken `require()` to a
  vanilla global. 143 shipped, 152 rows (9 unverified/unrecoverable staged).
- **Vanilla patches** (`mod/42/media/lua/client/UnbreakerPatches.lua`): bugs in BASE GAME lua.
  Boot line: `[Unbreaker] vanilla patches applied: N/M (game <build>)`, then
  `[Unbreaker] saved-outfit reader: <verdict>` on first use. MUST be tested in game before
  publishing (s13 blanked the preset dropdown on a file-local it could not see).
- **NOT here:** mod-specific patches go to `pz-shims`.

## Core Pattern

`require` is overridden; on failure returns `rawget(_G, entry.global)`. B42 returns nil silently for
missing modules, so check `(ok and result ~= nil)`. PZ logs `require(...) failed` even for modules
Unbreaker redirects; a "failed" line is not proof of breakage.

## What It Cannot Fix

Deep API rewrites; mod-internal modules; modules with no vanilla global (`Json`, `recipecode`,
`Items/ItemFactory`, `Maps/ISMapDefinitions`, `ISLootWindowControlHandler`); Brita/Arsenal/True
Actions; multiplayer (untested); `loadstring` (host-level). Removed upstream:
`CharacterCustomisationPanel`, `CommonTemplates`, `ISFarmingCursor` (42.20), Last Stand (42.22).

## Files Worth Knowing

- `mod/42/media/lua/shared/Unbreaker.lua` (require override), `.../client/UnbreakerPatches.lua`
- `scripts/smoke_probe.py`: needs Test Pilot enabled AND a loaded world (heartbeat is `OnTick`),
  and `loadstring` (42.21+, still present in 42.22.2). Sweeps all redirects (`full_sweep`);
  SimpleSilencers misses are expected without that mod.
- `scripts/watch.py` + `notify.ps1`: comment watcher. Test with `--simulate N`, never edit state.
- `scripts/build_workshop.ps1` + SteamCMD: ROB RUNS THESE. See `PUBLISH.md`.
- `workshop_item.template.txt`: VDF, NO `description` field by design.

## GOTCHA: four copies of Unbreaker

repo `mod/`; `~/Zomboid/mods/Unbreaker` (dev); `~/Zomboid/Workshop/Unbreaker/Contents/mods/Unbreaker`
(**PZ loads this**); Steam `workshop/content/108600/3721648770`. First three at v1.4.1. Confirm
with the console line, never `mod.info`. Do not touch `workshop.txt` in staging.

## Pending

1. **Rob's 3 damaged presets** (Zane, Hunter, Billy; checked 2026-09-25, each still ends mid-entry at
   `;KATTAJ1` or `;ALICE`; Theo is whole) need rebuilding once. Backup at
   `~/Zomboid/Lua/saved_outfits.txt.bak.pre-v140`.
2. **`Vehicles/VehicleUtils` unproven in practice.** Promoted on static evidence.
3. **Test Pilot's boot Spike self-test fails** on `require("Json")` (seen 2026-09-25, 11-03, 11-15).
   Harness itself works; the spike is stale. Belongs in pz-test-pilot.

## Recent Sessions

### Session 17 (2026-11-15): 42.22.2 stable, nothing to ship
Steam updated before a 42.21 baseline was saved, so the diff ran 42.20.4 to 42.22.2: 760 files
changed, Last Stand deleted (replaced by Challenges), no redirect source file or global lost, preset
reader and writer byte-identical. `getGameMode()` now returns a `zombie.core.GameMode` object (read
from projectzomboid.jar), so string compares in mods silently go false; pz-mod-checker got rules for
both (PR #24). In game on 42.22.2: Unbreaker 141/143, Test Pilot harness up with loadstring true,
Head for the Hills cabin spawn clean. First launch sat about 110 s at "Loading Mods" with 209
Workshop mods. main is now PR-only on GitHub; this session landed via unbreaker PR #20.

### Session 16 (2026-09-25): 42.21 unstable, v1.4.1 shipped for both branches
42.21 re-enabled `loadstring`/`loadstream`. Decided Unbreaker must work on stable and unstable at
once without version checks; added the compare-both-readers guard to the preset patch, the build
number in the boot line, v1.4.1. Verified in game on 42.21.0, 141/143. Rob published via SteamCMD.
pz-mod-checker gained the loadstring and getText arity rules.

### Session 15 (2026-08-26): 42.20.4 removes loadstring, both live mods unaffected
Security hotfix removed `loadstring`/`loadstream`. Unbreaker and Head for the Hills never used
either. Steam's news API (`ISteamNews/GetNewsForApp/v2/?appid=108600&maxlength=0`) gives full
patch notes; the forum's `og:description` truncates.
