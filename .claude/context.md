# Unbreaker Context

```yaml
version: 1.4.0
data_version: 0.8.0
status: v1.4.0 is LIVE on the Workshop (pushed 2026-08-05 15:14 UTC). 143 redirects + the first vanilla-lua patch. Verified in game on B42.20.1.
created: 2026-04-22
session: 13
last_updated: 2026-08-05
verification_target: B42.20.1
continue_with: Nothing blocking. The Workshop DESCRIPTION is still the old text (advertises 42.19 and 135 redirects); Rob deliberately deferred it, wording is in the s13 transcript. Next code work is pz-mod-checker, whose own context.md is stale at session 10.
blockers: HARD RULE, the agent NEVER touches Steam/Workshop. No SteamCMD, no publish, not build_workshop.ps1 (the classifier blocks it, correctly). Rob confirmed the s13 push himself.

workshop:
  id: 3721648770
  url: https://steamcommunity.com/sharedfiles/filedetails/?id=3721648770
  visibility: public
```

## To Resume

Session 14. Unbreaker main at v1.4.0 / data v0.8.0, 143 redirects, 0 open issues, live on Workshop.
Siblings: `pz-mod-checker` (rules cover 42.0 to 42.20, schema now supports `fixed_in`), `pz-shims` (public, 4 shims).

THIS WINDOW:
1. Nothing is blocked and nothing is half-finished in this repo.
2. Highest-value loose end is in **pz-mod-checker**: its `.claude/context.md` still says session 10 and
   records none of the s11 to s13 work. Its own uncommitted feature is still uncommitted.
3. When the next B42.x lands, FIRST action is the build diff (see Method).

## Method: diff builds, do not read changelogs

```
git clone --depth 1 https://github.com/Project-Zomboid-Community-Modding/ProjectZomboid-Vanilla-Lua
```

Commits are named by version (`29df4fe` = 42.19). Diff `client/server/shared` against
`<PZ install>/media/lua`. Check `projectzomboid.jar` too: some globals are Java-exposed with no
Lua assignment (`BodyLocations` is the worked example).

**Two limits, learned the hard way.** A file diff cannot see Java-side changes: 42.20 narrowed
`getFileWriter` to an extension whitelist, and 42.20.1 reversed it, neither visible in a tree diff.
And a hotfix can undo a finding, which is why pz-mod-checker rules now carry an optional `fixed_in`
upper bound.

## Two kinds of fix

- **Redirects** (`data/vanilla_globals.json` to `UnbreakerData.lua`): broken `require()` to a
  vanilla global. `rawget` only, so it can never make anything worse. 143 shipped.
- **Vanilla patches** (`mod/42/media/lua/client/UnbreakerPatches.lua`): bugs in the BASE GAME's
  lua. Applies on `OnGameBoot`, prints `[Unbreaker] vanilla patches applied: N/M`. High bar: must
  be a vanilla bug with no third-party version to track.
- **NOT here:** mod-specific patches. They go stale the moment the author ships a fix. Those live
  in `pz-shims`.

**A vanilla patch MUST be tested in game before publishing.** This is not optional and s13 proves
why: the first version of the outfit patch compared against `OUTFITS_VERSION`, which is a
FILE-LOCAL in `CharacterCreationMain.lua:453` and therefore nil from any other file. The check was
false for every line, the reader returned an empty table, and the character preset dropdown was
blank. No amount of static review found it; one launch did. Redirects are safe to ship on static
evidence. Function replacements are not.

## Core Pattern

`require` is overridden; on failure it returns `rawget(_G, entry.global)`. B42 returns nil silently
for missing modules, so check `(ok and result ~= nil)`.

**Triage note:** PZ logs `require(...) failed` even for modules Unbreaker successfully redirects.
A "failed" line is not proof of breakage. Last full sweep: 29 unique failures, 18 covered, 3
correctly unrecoverable, 8 uncovered and all mod-internal. Zero new redirect candidates.

## What It Cannot Fix

Deep API rewrites; mod-internal modules; modules with no vanilla global (`Json`, `recipecode`,
`Items/ItemFactory`, `Maps/ISMapDefinitions`, `ISLootWindowControlHandler`); Brita/Arsenal/True
Actions; multiplayer (untested).

Removed upstream: `CharacterCustomisationPanel`, `CommonTemplates` (gone by 42.19),
`Farming/BuildingObjects/ISFarmingCursor` (deleted 42.20, undocumented).

**Translations, still excluded.** 40 custom body locations registered across installed mods
(KATTAJ1 24, SPNCC 9, SpnOpenCloth 3, custombodylocation 2, ALICE 1), none with a
`UI_ClothingType_` entry, so character creation shows raw keys. Finite list, but it is display
strings for other people's mods. Right fix is upstream.

## Files Worth Knowing

- `mod/42/media/lua/shared/Unbreaker.lua` — require override
- `mod/42/media/lua/client/UnbreakerPatches.lua` — vanilla-bug patches
- `data/vanilla_globals.json` — v0.8.0, 143 shipped
- `scripts/build_workshop.ps1` — ROB RUNS THIS, never the agent
- `workshop_item.template.txt` — VDF. NO `description` field, by design; the build script throws
  if one reappears. That is what keeps a push from clobbering the Steam-app text.
- `PUBLISH.md` — runbook

## GOTCHA: four copies of Unbreaker exist

| Path | Role |
|---|---|
| `c:\xampp\htdocs\unbreaker\mod` | repo source |
| `~/Zomboid/mods/Unbreaker` | local dev copy |
| `~/Zomboid/Workshop/Unbreaker/Contents/mods/Unbreaker` | PZ publisher staging — **PZ loads THIS one** |
| Steam `workshop/content/108600/3721648770` | subscription |

All four at v1.4.0. Confirm with the console line, never `mod.info` on disk. Do not touch
`workshop.txt` in the staging folder; it holds the tags.

## Pending

1. **Workshop description is stale** (says 42.19, 135 redirects; live is 42.20.1, 143 + a vanilla
   patch). Rob chose to ship v1.4.0 without touching it. Wording drafted in the s13 transcript.
2. **`mod.info` description overclaims** "renamed functions", never true. Deferred with the above.
3. **pz-mod-checker `.claude/context.md` is stale** at session 10 and records none of s11 to s13.
4. **pz-mod-checker has an uncommitted feature** (`README.md`, `gui/server.py`,
   `gui/static/index.html`, untracked `unbreaker.py`). Still the only work across the three repos
   not backed up.
5. **Rob's 4 damaged presets** (Zane, Theo, Hunter, Billy) need rebuilding once. v1.4.0 stops
   further loss but cannot recover data already gone. Ben survived intact.
   Backup at `~/Zomboid/Lua/saved_outfits.txt.bak.pre-v140`.
6. **`Vehicles/VehicleUtils` unproven in practice.** Promoted on static evidence; file is under
   `media/lua/server`.
7. **`%%` translation rule declined, not forgotten.** 42.20.1 says mod translations need `%%` for a
   literal percent. A naive regex found 4,257 hits across 24 mods, but sampling showed most are
   UTF-16 files misread as UTF-8, or legitimate `%s`/`%d`/`%1` specifiers. A usable rule needs
   encoding detection and specifier exclusion first.

## Recent Sessions

### Session 13 (2026-08-05): 42.20.1 checked, outfit patch fixed in game, v1.4.0 shipped
42.20.1 hotfix landed. Verified against it: Unbreaker unaffected, all 143 targets resolve, and
critically the hotfix did NOT fix the saved-preset bug, so v1.4.0 was still worth shipping. The
hotfix did reverse the 42.20 `getFileWriter` .json block, so pz-mod-checker rules gained an
optional `fixed_in` upper bound (`since <= target < fixed_in`), verified active only at 42.20.0.
Declined the `%%` translation rule on measurement rather than instinct.

Then the outfit patch failed its first in-game test: preset dropdown blank, because
`OUTFITS_VERSION` is a vanilla file-local and read as nil from the patch file. Fixed to mirror the
constant and delegate to the original reader on an unknown format. Retested in game: patches 1/1,
five presets listed, Ben McLaughlin loaded with all six modded slots and spawned into a world with
`saved_outfits.txt` byte-identical. Rob pushed v1.4.0 to the Workshop, confirmed live 15:14 UTC.

### Session 12 (2026-08-04): found a vanilla bug destroying saved presets
`CharacterCreationMain.readSavedOutfitFile` splits on `:` and keeps only field 2, but the format is
`PresetName:key=value;...` and B42's own convention puts a colon in every custom slot name
(`ItemBodyLocation.register("KATTAJ1:BackFanny")`). Any preset with a modded slot lost everything
from that slot on, and the truncation was written back on save. Four of Rob's five presets were
already destroyed. Added `UnbreakerPatches.lua`, establishing vanilla-bug patches as a second
category. Also corrected the s11 `no_lua_in_media_root` check, which flagged `media/registries.lua`
(29 mods) and `media/maps/*/spawnpoints.lua` (vanilla ships 14); exemptions derived from the base
game, 20 false positives down to 1 genuine.

### Session 11 (2026-07-30): B42.20 Stable, data v0.8.0
133 of 137 redirects survived 42.20. Added 4, resolved 3 staged candidates, promoted
`VehicleUtils`, demoted two dead ones. 137 to 143. Closed #15. Off-repo: diagnosed Auto Key Rings
(33,642 exceptions/session, also breaking multi-item inventory drags), shimmed it to zero, and spun
the shims into **https://github.com/robotsmeller/pz-shims**.

@.claude/rules/code-architecture.md
