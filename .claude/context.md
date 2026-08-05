# Unbreaker Context

```yaml
version: 1.4.0
data_version: 0.8.0
status: v1.4.0 LIVE on the Workshop. 143 redirects + 1 vanilla-lua patch. Verified in game on 42.20.1; 42.20.2 checked statically only, no action needed.
created: 2026-04-22
session: 14
last_updated: 2026-08-05
verification_target: B42.20.2 (static). Last in-game verification was 42.20.1.
continue_with: Issue #19 — one game launch on 42.20.2 to confirm the 143 redirects resolve and to capture the new translation error-log format.
blockers: HARD RULE, the agent NEVER touches Steam/Workshop. No SteamCMD, no publish, not build_workshop.ps1 (the classifier blocks it, correctly).

workshop:
  id: 3721648770
  url: https://steamcommunity.com/sharedfiles/filedetails/?id=3721648770
  visibility: public
```

## To Resume

Session 15. Unbreaker main at v1.4.0 / data v0.8.0, 143 redirects, 1 open issue (#19), live on Workshop.
Siblings: `pz-mod-checker`, `pz-shims` (public, 4 shims).

THIS WINDOW:
1. **#19 needs the game, not the agent.** Launch once on 42.20.2, probe the 143 redirects,
   and grab the new translation error-log lines. Nothing else here is blocked.
2. The error-log format feeds a **pz-mod-checker getText rule** (see Two Kinds of Fix below).
3. pz-mod-checker still has a stale `context.md` (session 10) and an uncommitted feature.

## Method: diff builds, do not read changelogs

```
git clone --filter=blob:none https://github.com/Project-Zomboid-Community-Modding/ProjectZomboid-Vanilla-Lua
```

Commits are named by version (`15300b1` = 42.20). Diff `client/server/shared` against
`<PZ install>/media/lua`.

**Use `diff -rq --strip-trailing-cr`.** Without it, s14 got 291 changed files; with it, 9.
The other 282 were line endings. Check `Only in` lines separately: a DELETED file breaks a
redirect, which is how `ISFarmingCursor` bit us in 42.20.

**Three limits, learned the hard way.** The repo lags: it had no 42.20.1 or 42.20.2 commit,
so the install itself became the source of truth. A file diff cannot see Java-side changes
(42.20 narrowed `getFileWriter`, 42.20.1 reversed it, neither visible in a tree diff). And a
hotfix can undo a finding, which is why pz-mod-checker rules carry an optional `fixed_in`.

## Two kinds of fix

- **Redirects** (`data/vanilla_globals.json` to `UnbreakerData.lua`): broken `require()` to a
  vanilla global. `rawget` only, so it can never make anything worse. 143 shipped, 152 rows
  total (9 unverified/unrecoverable are staged, not generated).
- **Vanilla patches** (`mod/42/media/lua/client/UnbreakerPatches.lua`): bugs in the BASE GAME's
  lua. Applies on `OnGameBoot`, prints `[Unbreaker] vanilla patches applied: N/M`. High bar.
- **NOT here:** mod-specific patches go to `pz-shims`.

**A vanilla patch MUST be tested in game before publishing.** s13 proved it: the outfit patch
compared against `OUTFITS_VERSION`, a FILE-LOCAL in `CharacterCreationMain.lua:453`, so it read
nil from another file and blanked the preset dropdown. Static review missed it; one launch found
it. Redirects are safe on static evidence. Function replacements are not.

**42.20.2's real change is `getText` arity, not `%%`.** The notes say mods should use `%%`; the
diff shows 76 call sites swept from `getText("KEY")` to `getText("KEY", "")` / `("KEY","","")`.
The engine now wants one argument per format specifier. That is a tractable pz-mod-checker rule
(call arity vs specifier count, both inside the mod, no encoding guesswork) and it supersedes the
`%%` file-scan declined in s13. The both-forms workaround is explicitly temporary.

## Core Pattern

`require` is overridden; on failure it returns `rawget(_G, entry.global)`. B42 returns nil
silently for missing modules, so check `(ok and result ~= nil)`.

**Triage note:** PZ logs `require(...) failed` even for modules Unbreaker successfully redirects.
A "failed" line is not proof of breakage. Last full sweep: 29 unique failures, 18 covered, 3
correctly unrecoverable, 8 uncovered and all mod-internal.

## What It Cannot Fix

Deep API rewrites; mod-internal modules; modules with no vanilla global (`Json`, `recipecode`,
`Items/ItemFactory`, `Maps/ISMapDefinitions`, `ISLootWindowControlHandler`); Brita/Arsenal/True
Actions; multiplayer (untested).

Removed upstream: `CharacterCustomisationPanel`, `CommonTemplates` (gone by 42.19),
`Farming/BuildingObjects/ISFarmingCursor` (deleted 42.20, undocumented).

**Translations, still excluded.** 40 custom body locations across installed mods with no
`UI_ClothingType_` entry. Display strings for other people's mods; right fix is upstream.

## Files Worth Knowing

- `mod/42/media/lua/shared/Unbreaker.lua` — require override
- `mod/42/media/lua/client/UnbreakerPatches.lua` — vanilla-bug patches
- `data/vanilla_globals.json` — v0.8.0
- `scripts/watch.py` + `scripts/notify.ps1` — Workshop/GitHub comment watcher (s14)
- `scripts/build_workshop.ps1` — ROB RUNS THIS, never the agent
- `workshop_item.template.txt` — VDF. NO `description` field, by design.
- `PUBLISH.md` — runbook

## GOTCHA: four copies of Unbreaker exist

| Path | Role |
|---|---|
| `c:\xampp\htdocs\unbreaker\mod` | repo source |
| `~/Zomboid/mods/Unbreaker` | local dev copy |
| `~/Zomboid/Workshop/Unbreaker/Contents/mods/Unbreaker` | **PZ loads THIS one** |
| Steam `workshop/content/108600/3721648770` | subscription |

All four at v1.4.0. Confirm with the console line, never `mod.info` on disk. Do not touch
`workshop.txt` in the staging folder; it holds the tags.

## Pending

1. **`mod.info` description overclaims** "renamed functions", which Unbreaker has never done,
   and omits the vanilla-patch capability. Ships INSIDE the mod, so it is a repo edit plus a
   re-push.
2. **pz-mod-checker `.claude/context.md` is stale** at session 10 (none of s11 to s14).
3. **pz-mod-checker has an uncommitted feature** (`README.md`, `gui/server.py`,
   `gui/static/index.html`, untracked `unbreaker.py`). Still the only unbacked-up work.
4. **Rob's 4 damaged presets** (Zane, Theo, Hunter, Billy) need rebuilding once. v1.4.0 stops
   further loss but cannot recover data already gone. Backup at
   `~/Zomboid/Lua/saved_outfits.txt.bak.pre-v140`.
5. **`Vehicles/VehicleUtils` unproven in practice.** Promoted on static evidence.

## Recent Sessions

### Session 14 (2026-08-05): comment watcher built, 42.20.2 cleared statically
Built a Workshop/GitHub comment watcher: `scripts/watch.py` + `scripts/notify.ps1`, polling two
Steam comment threads and Unbreaker's GitHub issues and issue comments every 20 minutes, pushing
to Telegram. Verified end to end against a real posted comment. **The scheduled task and
`%LOCALAPPDATA%\pz-watch\` are machine state, not in git** — a fresh clone gets the script and
nothing that runs it. Repo watching on `robotsmeller/unbreaker` was OFF (confirmed via
`user/subscriptions`), so stranger-filed issues generated no notification at all; now on.
Then cleared 42.20.2 statically: no files added or removed, 9 changed, only `ISVehicleMenu.lua`
is a redirect target and its global still assigns, `CharacterCreationMain.lua` byte-identical so
the saved-preset bug remains unfixed upstream. Found that the hotfix's real change is `getText`
arity, not `%%`, which revives the rule declined in s13. Filed #19 for the one launch needed.

### Session 13 (2026-08-05): 42.20.1 checked, outfit patch fixed in game, v1.4.0 shipped
Verified against 42.20.1: Unbreaker unaffected, all 143 targets resolve, and the hotfix did NOT
fix the saved-preset bug, so v1.4.0 was still worth shipping. The hotfix did reverse the 42.20
`getFileWriter` .json block, so pz-mod-checker rules gained an optional `fixed_in` upper bound.
The outfit patch then failed its first in-game test (`OUTFITS_VERSION` nil across files); fixed
to mirror the constant and delegate to the original reader on an unknown format. Retested in
game: five presets listed, `saved_outfits.txt` byte-identical. Rob pushed v1.4.0, live 15:14 UTC.

### Session 12 (2026-08-04): found a vanilla bug destroying saved presets
`CharacterCreationMain.readSavedOutfitFile` splits on `:` and keeps only field 2, but the format
is `PresetName:key=value;...` and B42's own convention puts a colon in every custom slot name
(`ItemBodyLocation.register("KATTAJ1:BackFanny")`). Any preset with a modded slot lost everything
from that slot on, and the truncation was written back on save. Four of Rob's five presets were
already destroyed. Added `UnbreakerPatches.lua`, establishing vanilla-bug patches as a second
category. Also corrected the s11 `no_lua_in_media_root` check: 20 false positives down to 1.

@.claude/rules/code-architecture.md
