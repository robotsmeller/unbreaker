# Unbreaker Context

```yaml
version: 1.3.0
data_version: 0.8.0
status: v1.3.0 / data v0.8.0 (143 redirects) is LIVE on the Workshop and confirmed loading in game. Verified against an installed B42.20 Stable plus a 42.19-to-42.20 file diff.
created: 2026-04-22
session: 11
last_updated: 2026-07-30
verification_target: B42.20
continue_with: Workshop page text only. The description still advertises 42.19 and 135 redirects; wording is ready in the session-11 transcript. Also add the pz-shims link and drop the false "renamed functions" claim from mod.info.
blockers: HARD RULE, the agent NEVER touches Steam/Workshop. No SteamCMD, no publish, and not build_workshop.ps1 (the permission classifier blocks it, correctly). All releasing is Rob's manual action.

workshop:
  id: 3721648770
  url: https://steamcommunity.com/sharedfiles/filedetails/?id=3721648770
  visibility: public
```

## To Resume

Session 12. Unbreaker main at v1.3.0 / data v0.8.0, 143 redirects, 0 open issues.
Sibling repos: `pz-mod-checker` (rules now cover 42.0 to 42.20), `pz-shims` (new, public).

THIS WINDOW:
1. Nothing is blocked. Unbreaker is done for 42.20.
2. If Rob asks about the Workshop page: description wording + shims link + mod.info fix (see `pending`).
3. When the next B42.x lands, FIRST action is the build diff (see Method).

## Method: diff builds, do not read changelogs

Clone the community mirror and diff it against the installed game:

```
git clone --depth 1 https://github.com/Project-Zomboid-Community-Modding/ProjectZomboid-Vanilla-Lua
```

Commits are named by version (`29df4fe` = 42.19). Diff its `client/server/shared` against
`<PZ install>/media/lua`. Check `projectzomboid.jar` too: some globals are Java-exposed with no
Lua assignment anywhere (`BodyLocations` is the worked example).

This caught two removals no changelog mentions, including two globals dead since 42.18/42.19 that
changelog-only reviews in sessions 8 and 9 called clean. Do this every patch.

## Core Pattern (v1.3.0)

`require` is overridden; on failure it looks up `REDIRECTS[module]` and returns `rawget(_G, entry.global)`.

**B42 quirk:** require returns nil silently for missing modules, so check `(ok and result ~= nil)`.
Discovery for a candidate: does a top-level `NAME =` assignment exist in an auto-loaded vanilla file,
or a matching class in the jar?

**Triage note:** PZ logs `require(...) failed` even for modules Unbreaker successfully redirects.
A "failed" line is not proof of breakage. Latest 42.20 session: 29 unique failures, 18 covered,
3 correctly unrecoverable, 8 uncovered and all mod-internal. Zero new redirect candidates.

## What It Cannot Fix

Deep API rewrites; mod-internal modules; modules with no vanilla global (`Json`, `recipecode`,
`Items/ItemFactory`, `Maps/ISMapDefinitions`, `ISLootWindowControlHandler`); translations;
Brita/Arsenal/True Actions; multiplayer (untested).

Removed upstream: `CharacterCustomisationPanel` and `CommonTemplates` (gone by 42.19),
`Farming/BuildingObjects/ISFarmingCursor` (deleted in 42.20, undocumented).

**NOT this list any more: `VehicleUtils`.** The old entry confused a missing FILE with a missing
GLOBAL. Watch for that confusion; a redirect only needs the global.

### Worked example of the "translations" exclusion (noted 2026-08-04)

Seen on Rob's live install while working on pz-head-for-the-hills. Character creation lists dozens
of clothing slots labelled with their raw key rather than a name: `UI_ClothingType_KATTAJ1:BackFanny`,
`UI_ClothingType_SPNCC:Face`, `UI_ClothingType_SpnOpenCloth:JACKET_OPEN`,
`UI_ClothingType_custombodylocation:LowerBack`, `UI_ClothingType_ALICE:Sheath`.

Five mods register the slots and ship no translation entry for them: KATTAJ1 Clothes Core (and its
Military Pack), Spongie's Character Customisation, Spongie's Open Jackets, Skully's Duffels and Rigs,
and Better Vanilla ALICE Backpacks. PZ falls back to printing the key when
`UI_ClothingType_<name>` has no entry, so nothing is broken; the labels are just ugly and the
dropdowns all read None.

Recorded because it looks fixable and is not Unbreaker's shape. A redirect fixes a `require()` that
resolves to nothing. This needs display strings for five other mods' body locations, growing every
time one of them adds a slot, which is a maintenance commitment rather than a finite list. If it is
ever worth doing it belongs in its own small mod, not here.

The right fix is upstream: one line on each mod's Workshop page.

## Files Worth Knowing

- `mod/42/media/lua/shared/Unbreaker.lua` — override + miss ring buffer
- `data/vanilla_globals.json` — v0.8.0, 143 shipped (+ unrecoverable / verified:false, not shipped)
- `scripts/generate_lua.py` — JSON to Lua (skips unrecoverable + unverified)
- `scripts/build_workshop.ps1` — folder + VDF. ROB RUNS THIS, never the agent.
- `docs/index.html` — GitHub Pages diagnostic tool
- `PUBLISH.md` — runbook (fixed in s11: it referenced a `workshop_item.txt` that does not exist;
  it is `workshop_item.template.txt`, copied to `build/workshop_item.txt` at build time)

## GOTCHA: four copies of Unbreaker exist

PZ loads whichever it likes and it bit us for most of session 11.

| Path | Role |
|---|---|
| `c:\xampp\htdocs\unbreaker\mod` | repo source |
| `~/Zomboid/mods/Unbreaker` | local dev copy |
| `~/Zomboid/Workshop/Unbreaker/Contents/mods/Unbreaker` | PZ publisher staging — **PZ loaded THIS one** |
| Steam `workshop/content/108600/3721648770` | subscription |

Always confirm with the console line: `[Unbreaker] loaded v1.3.0 — 143 redirects (data v0.8.0)`.
Never trust `mod.info` on disk. Do not touch `workshop.txt` in the staging folder; it holds the tags.

## Pending (all Rob, none blocking)

1. **Workshop description** still says 42.19 / 135 redirects. Wording ready in the s11 transcript.
2. **Add the pz-shims link** to the description, `docs/index.html` (highest value: near the
   "unknown" bucket) and the README. Not to `mod.info` `url=`, which should stay on the repo.
3. **`mod.info` description overclaims** "renamed functions". Unbreaker does not do that. Needs a
   repo edit and a re-push, not a Steam-side edit.
4. **Changenote published stale** (v1.2.1 text). Template is corrected for the next release.
5. **`Vehicles/VehicleUtils` unproven in practice.** Promoted on static evidence; its file is under
   `media/lua/server`. A driving session with Realistic Dashboard and Gauges settles it.

## Recent Sessions

### Session 11 (2026-07-30): B42.20 Stable, data v0.8.0, shipped + two sibling repos advanced
PZ went B42.20 Stable 2026-07-29. Re-validated everything against an installed 42.20 plus a
42.19 file diff: 133 of 137 redirects survived untouched. Added 4 (`gamepadBinding`, the only
root move in the build; `TimedActions/ISWalkToTimedAction`; `ISUI/ISItemDropBox`;
`Items/ProceduralDistributions/ProceduralDistributions`), resolved the 3 candidates staged in
v0.7.0, promoted `VehicleUtils`, demoted two dead ones. 137 to 143. Rob pushed v1.3.0 to the
Workshop; closed #15 with a reply to falkon311; 0 open issues.

Off-repo but same session: live-diagnosed Auto Key Rings B42.20 (33,642 exceptions/session, and
it was breaking multi-item inventory drags via the timed action queue), wrote a shim, took it to
**zero** and the log from 7.6 MB to 955 KB. Spun the shims into a new public repo,
**https://github.com/robotsmeller/pz-shims**. In pz-mod-checker: added 42.19/42.20 rule files,
implemented `no_lua_in_media_root` (declared in session 8, never implemented, so that rule had
never once fired), fixed pattern rules matching inside Lua comments, and added a rule for Java
reflection gated since the 42.14 security patch, which catches 4 mods that were previously
invisible including StarlitLibrary.

### Session 10 (2026-06-24): Triaged diagnostic-tool reports #12–#15, data v0.7.0
First inbound community reports, all from falkon311 (17 modules across 4 issues). Added 2 verified
alternate-path redirects, staged 3 unverified candidates, closed #12–#14. Not released.

### Session 9 (2026-06-01): B42.19 verification + CFarmingSystem fix, shipped v1.2.1
Added `Farming/CFarmingSystem`, reclassified 4 modules as unrecoverable, shipped v1.2.1 / data
v0.6.0 (135 redirects). Removed the description from the publish pipeline after a push clobbered
Rob's manual Steam edits.

@.claude/rules/code-architecture.md
