# Unbreaker Context

```yaml
version: 1.4.0
data_version: 0.8.0
status: Repo is at v1.4.0 (143 redirects + first vanilla-lua patch), committed and pushed. NOT yet on the Workshop; live build is still v1.3.0. Verified against an installed B42.20 Stable.
created: 2026-04-22
session: 12
last_updated: 2026-08-05
verification_target: B42.20.1
continue_with: Rob pushes v1.4.0 to the Workshop (build script + SteamCMD, both his). Description and mod.info wording are drafted in the session-12 transcript and unapplied.
blockers: HARD RULE, the agent NEVER touches Steam/Workshop. No SteamCMD, no publish, not build_workshop.ps1. All releasing is Rob's manual action.

workshop:
  id: 3721648770
  url: https://steamcommunity.com/sharedfiles/filedetails/?id=3721648770
  visibility: public
```

## To Resume

Session 13. Unbreaker main at v1.4.0 / data v0.8.0, 143 redirects, 0 open issues.
Siblings: `pz-mod-checker` (rules cover 42.0 to 42.20), `pz-shims` (public, 4 shims).

THIS WINDOW:
1. Nothing is blocked. v1.4.0 is ready to publish whenever Rob wants.
2. If Rob asks about the Workshop: evergreen description + `mod.info` fix (see Pending 1 and 2).
3. When the next B42.x lands, FIRST action is the build diff (see Method).

## Method: diff builds, do not read changelogs

```
git clone --depth 1 https://github.com/Project-Zomboid-Community-Modding/ProjectZomboid-Vanilla-Lua
```

Commits are named by version (`29df4fe` = 42.19). Diff `client/server/shared` against
`<PZ install>/media/lua`. Check `projectzomboid.jar` too: some globals are Java-exposed with no
Lua assignment anywhere (`BodyLocations` is the worked example). This caught two removals no
changelog mentions. Do this every patch.

**Limit, learned in s12:** a file diff cannot see Java-side changes. 42.20 narrowed
`getFileWriter` to an extension whitelist, and no tree diff would ever surface that. The 42.20.1
hotfix then reversed it ("Added the ability for mods to write .json files"), which is why
pz-mod-checker rules now carry an optional `fixed_in` upper bound.

**42.20.1 hotfix (2026-08-05) checked, Unbreaker unaffected.** All 143 targets still resolve,
`gamepadBinding` still client-side, `ISFarmingCursor` still gone. Critically the hotfix did NOT
fix the saved-preset bug: `CharacterCreationMain.lua:572` still reads `retVal[s[1]] = s[2]`, so
the v1.4.0 patch is still needed and still correct.

## Two kinds of fix (decided s12)

- **Redirects** (`data/vanilla_globals.json` to `UnbreakerData.lua`): broken `require()` to a
  vanilla global. `rawget` only, so it can never make anything worse. 143 shipped.
- **Vanilla patches** (`mod/42/media/lua/client/UnbreakerPatches.lua`): bugs in the BASE GAME's
  lua. High bar: must be a vanilla bug with no third-party version to track. Applies on
  `OnGameBoot`, prints `[Unbreaker] vanilla patches applied: N/M`.
- **NOT here:** mod-specific patches. They go stale the moment the author ships a fix and
  Unbreaker cannot know when. Those live in `pz-shims`.

## Core Pattern

`require` is overridden; on failure it returns `rawget(_G, entry.global)`. B42 returns nil
silently for missing modules, so check `(ok and result ~= nil)`.

**Triage note:** PZ logs `require(...) failed` even for modules Unbreaker successfully redirects.
A "failed" line is not proof of breakage. Last full 42.20 session: 29 unique failures, 18 covered,
3 correctly unrecoverable, 8 uncovered and all mod-internal. Zero new redirect candidates.

## What It Cannot Fix

Deep API rewrites; mod-internal modules; modules with no vanilla global (`Json`, `recipecode`,
`Items/ItemFactory`, `Maps/ISMapDefinitions`, `ISLootWindowControlHandler`); Brita/Arsenal/True
Actions; multiplayer (untested).

Removed upstream: `CharacterCustomisationPanel`, `CommonTemplates` (both gone by 42.19),
`Farming/BuildingObjects/ISFarmingCursor` (deleted 42.20, undocumented).

**Translations, still excluded.** 40 custom body locations are registered across installed mods
(KATTAJ1 24, SPNCC 9, SpnOpenCloth 3, custombodylocation 2, ALICE 1) and NONE has a
`UI_ClothingType_` entry, so character creation shows raw keys. Verified count, s12. It is a
finite list, not open-ended, but it is display strings for other people's mods. Right fix is
upstream. If ever done, its own small mod.

## Files Worth Knowing

- `mod/42/media/lua/shared/Unbreaker.lua` — require override
- `mod/42/media/lua/client/UnbreakerPatches.lua` — vanilla-bug patches (new s12)
- `data/vanilla_globals.json` — v0.8.0, 143 shipped
- `scripts/generate_lua.py` — JSON to Lua
- `scripts/build_workshop.ps1` — ROB RUNS THIS, never the agent
- `workshop_item.template.txt` — VDF. Has NO `description` field, by design. Changenote is at v1.4.0.
- `PUBLISH.md` — runbook

## GOTCHA: four copies of Unbreaker exist

| Path | Role |
|---|---|
| `c:\xampp\htdocs\unbreaker\mod` | repo source |
| `~/Zomboid/mods/Unbreaker` | local dev copy |
| `~/Zomboid/Workshop/Unbreaker/Contents/mods/Unbreaker` | PZ publisher staging — **PZ loads THIS one** |
| Steam `workshop/content/108600/3721648770` | subscription |

All four synced to v1.4.0 in s12. Always confirm with the console line, never `mod.info` on disk.
Do not touch `workshop.txt` in the staging folder; it holds the tags.

## Pending (all Rob)

1. **Push v1.4.0 to the Workshop.** Changenote is already correct in the template.
2. **Workshop description**: evergreen rewrite drafted in the s12 transcript. Version detail moved
   to the changenote so the description stops going stale. Includes the pz-shims link.
3. **`mod.info` description** still claims "renamed functions" (never true) and omits the new
   vanilla-patch capability. Replacement wording drafted, not applied. Ships inside the mod.
4. **Rob's 4 damaged character presets** (Zane, Theo, Hunter, Billy) must be rebuilt once. The
   v1.4.0 fix stops further loss but cannot recover data already gone from the file.
5. **`Vehicles/VehicleUtils` unproven in practice.** Promoted on static evidence; file is under
   `media/lua/server`. A driving session with Realistic Dashboard and Gauges settles it.
6. **pz-mod-checker has an uncommitted feature** (`README.md`, `gui/server.py`,
   `gui/static/index.html`, untracked `unbreaker.py`). Rob's work from an earlier session, never
   committed. The only thing across the three repos not backed up.

## Recent Sessions

### Session 12 (2026-08-04): found a vanilla bug destroying saved presets, shipped v1.4.0
Chased the s11 translations note and found something worse next to it. Rob reported KATTAJ1 items
vanishing from saved character templates. Root cause is vanilla:
`CharacterCreationMain.readSavedOutfitFile` does `luautils.split(line, ":")` then keeps only
`s[2]`, but the format is `PresetName:key=value;...`, so the payload is truncated at the first
colon inside it. B42's own convention puts a colon in every custom slot name
(`ItemBodyLocation.register("KATTAJ1:BackFanny")`), so any preset with a modded slot loses
everything from that slot on, including trailing vanilla slots, and the truncation is written back
on save. Confirmed on Rob's live file: 4 of 5 presets already destroyed, the intact one loses 346
of 1052 chars under vanilla and 0 under the patch, which round-trips byte-identical.

Added `UnbreakerPatches.lua` for this, establishing vanilla-bug patches as a second category and
drawing the boundary: vanilla bugs here, mod-specific patches in pz-shims. v1.4.0, all four copies
synced. Also fixed the `no_lua_in_media_root` check added in s11, which flagged `media/registries.lua`
(29 mods use it) and `media/maps/*/spawnpoints.lua` (vanilla ships 14). Exemptions derived from the
base game; 20 false positives down to 1 genuine. Counted the translation gap properly: 40 slots, 0
translations.

### Session 11 (2026-07-30): B42.20 Stable, data v0.8.0, shipped
Re-validated everything against an installed 42.20 plus a 42.19 file diff: 133 of 137 redirects
survived. Added 4, resolved the 3 staged candidates, promoted `VehicleUtils`, demoted two dead
ones. 137 to 143. Rob pushed v1.3.0; closed #15; 0 open issues. Off-repo: diagnosed Auto Key Rings
(33,642 exceptions/session, also breaking multi-item inventory drags), shimmed it to zero, and spun
the shims into **https://github.com/robotsmeller/pz-shims**. In pz-mod-checker: 42.19/42.20 rules,
comment-stripping fix, and a Java-reflection rule catching 4 previously invisible mods.

### Session 10 (2026-06-24): Triaged diagnostic-tool reports #12–#15, data v0.7.0
First inbound community reports, all from falkon311. Added 2 verified alternate-path redirects,
staged 3 unverified candidates, closed #12–#14. Not released.

@.claude/rules/code-architecture.md
