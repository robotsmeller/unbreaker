All claims verified against the actual code. Now producing the brief.

---

# Pre-Flight Plan Review

**Plan**: Take Unbreaker (PZ Build 42 require() polyfill mod) from Phase 1 verified locally to polished, public, Workshop-ready v1.0
**Date**: 2026-05-07
**Reviewers**: Soren (implementation) + Atlas (architecture & synthesis) + Morgan (UX/design)
**Method**: Multi-round collaborative pre-flight review with two exchange rounds

## Plan Description

Take Unbreaker (PZ Build 42 require() polyfill mod) from Phase 1 verified locally to polished, public, Workshop-ready v1.0. Architecture is proven: live B42.17 probes show 139/141 broken require() calls served (98.6% hit rate) in a 180-mod install. Data is at 27 verified redirects with a miss ring buffer that captured 303 candidates this session. Plan must cover: (1) Workshop publish pipeline via SteamCMD plus GitHub Actions including 2FA strategy; (2) docs hygiene, README, SCOPE, CHANGELOG, CONTRIBUTING; (3) Phase 2 data expansion strategy from the 303-entry miss buffer (which entries to add, how to triage, how to verify); (4) multiplayer verification plan (checksum risk is the open question); (5) kill-switch criteria, concrete thresholds for when to archive the project; (6) contributor onboarding, JSON-only contribution path that lets non-Lua-literate users add redirects, including possible GitHub Pages issue-submission form that pipes to Issues; (7) PZ Mod Checker integration as the diagnostic feeder; (8) the realistic risk surface, TIS API breakage, Workshop comment management, Brita and Arsenal expectation gap. Three projects in the ecosystem: Unbreaker (player-facing), PZ Mod Checker (player and modder diagnostic), pz-test-pilot (developer-only verification harness). Only Unbreaker ships to Workshop. Stack: Lua (Kahlua, no io or os, no networking), Python stdlib for tooling, GitHub Actions for CI, B42 versioned mod layout (mod/42/media/...). Maintainer is solo; community help is hoped-for but not guaranteed. Output a polish-and-ship roadmap with concrete phases, decision points, and red flags.

## Readiness Assessment

- **Implementation (Soren)**: ⚠️ CAUTION — Architecture is proven and code is solid, but CI workflow has never successfully committed since the B42 layout migration, and the load order question is unanswered.
- **Architecture (Atlas)**: ✅ GO — pcall-first design means worst failure mode is "does nothing," never "breaks something." The architecture is empirically proven; remaining gaps are operational, not structural.
- **UX/Design (Morgan)**: ⚠️ CAUTION — The code is ready to ship but the expectation-management layer is not. Workshop description must set the scope boundary before Brita subscribers set it for you.
- **Overall**: ⚠️ CAUTION — Ship-ready after eight concrete pre-ship items are resolved. The architecture is sound. The gaps are operational and solvable within days, not weeks. One gap (load order) is a potential correctness blocker that must be answered empirically before any Workshop publish.

## Morgan's Design Brief

### Direction: "Duct Tape Charm" (Direction B) — Unanimous

**Character:** Self-aware utility. The friend who fixes your stuff and makes a joke about it. Warm, slightly irreverent, technically solid underneath. Signals: "we know this is a band-aid, and that's fine, band-aids work." Matches the existing product voice ("Stopgap, not a replacement").

**Color palette:**
- `#1a1a2e` (background, dark navy)
- `#25253e` (surface/cards)
- `#e0e0e0` (body text)
- `#e6b800` (accent, caution-tape yellow, on-brand for fix/repair)
- `#ff6b6b` (danger/error/unrecoverable)

**Typography:**
- Body: DM Sans, 16px/400 (friendly, readable)
- Headings: Space Grotesk, 22-32px/700 (geometric but warm)
- Module paths/code: JetBrains Mono, always monospaced

**Caveat:** `mod/poster.png` and `mod/preview.png` exist locally but are untracked in git. Nobody has seen them. If the existing thumbnail establishes a different visual identity, Direction B must match the existing assets rather than override them. Check the images before committing to visual direction.

**Scoped surfaces (the only UX surfaces that exist):**
1. Steam Workshop page (first contact, expectation-setting)
2. GitHub README (contributor onboarding)
3. In-game console output (only in-game visibility)
4. GitHub Issue templates (already decent)

**Do NOT build:** GitHub Pages submission form. Premature. Existing issue templates handle the use case. Build contributor infrastructure after there are contributors. (Unanimous)

### Top 3 Design Recommendations

**1. Workshop description must name Brita explicitly in paragraph one.** (Unanimous)

This is the highest-priority UX action. "Unbreaker" as a name promises everything. The description must promise less, specifically, in the first two lines before anyone subscribes. Draft text:

> Fixes broken require() calls caused by PZ patches. Works silently when it works.
> Does NOT fix Brita's Weapon Pack, Arsenal, or True Actions. Those need deep rewrites the mod authors must do.

Then the existing draft from HANDOFF.md:

> Keeps your mods working between PZ patches. Fixes broken require() calls, renamed functions, and moved globals. The minor API shuffles that come with almost every weekly update. When a mod's author publishes a proper fix, Unbreaker automatically steps aside. Stopgap, not a replacement.

**2. Pin a Workshop comment with scope boundary on day one.** (Majority: Morgan + Atlas. Soren neutral.)

Before user comments arrive, pin a comment listing: top 5 mods Unbreaker helps, the 3 named mods it cannot help, "Report issues on GitHub" link, "Singleplayer verified / MP untested" status.

**3. Silent success is a structural review-skew problem.** (Identified by Soren, endorsed by all.)

When Unbreaker works, the player sees nothing. When it partially works, the player sees remaining crashes and blames Unbreaker. No feedback path from "works silently" to "leaves positive review." The console print is the only signal. Not fixable at launch. Accept that the review-to-subscriber ratio will be skewed negative. Satisfied users have no prompt to act.

## Soren's Implementation Blueprint

### Recommended approach: Option C "Tiered Ship" — Unanimous

Ship v1.0 with current 27 redirects. No batch probe as a ship prerequisite. The batch probe of 303 misses is Phase 2 post-ship work.

**Rationale for not waiting on the batch probe:** The 303-miss list was captured on B42.17. Every PZ patch can invalidate it. The verification window is 2-3 weeks. Coupling the ship date to a pz-test-pilot session that depends on harness stability (Session 2 hit two B42 bugs in the harness itself) is the wrong dependency. If B42.x+1 drops before the batch probe completes, Option C collapses to shipping with 27 entries anyway.

**Key code patterns:**
- `pcall(_require, module)` always fires first. Real modules win.
- `(ok and result == nil)` triggers redirect lookup (B42 quirk: require returns nil silently for side-effect-only modules).
- `rawget(_G, entry.global)` serves the vanilla global if it exists.
- Miss ring buffer (256 cap) captures unserved require paths for Phase 2 triage.

### Pre-ship code changes (ordered by dependency):

| # | Change | File | Complexity |
|---|--------|------|-----------|
| 1 | Fix `file_pattern` path | `.github/workflows/generate.yml:28` | One line: `mod/media/...` to `mod/42/media/...` |
| 2 | Fix docstring | `scripts/generate_lua.py:5` | One line: update stated output path |
| 3 | Verify generated output matches JSON | Run `python scripts/generate_lua.py`, diff against committed `UnbreakerData.lua` | 5 minutes. Confirmed match in this review. |
| 4 | Remove alias dead code | `Unbreaker.lua:64-75` | Remove 12 lines. Zero JSON entries use `alias`. The code path has a latent bug: `resolveGlobal(entry.alias)` treats the alias string as a global name, but alias strings would be module paths (with slashes), which never match globals. Re-add when there's data that exercises it. |
| 5 | Bump version | Both `mod.info` files + `Unbreaker.lua:89` | `0.1.0-dev` to `1.0.0` |
| 6 | Add AquaConfig exemption comment | `data/vanilla_globals.json` line 221 | Document why `verified: false` is intentional (can't verify without mod installed). Not a blocker. |

### Test strategy:

| Layer | How | Difficulty |
|-------|-----|-----------|
| `generate_lua.py` correctness | Unit test: known JSON to expected Lua output. Pure Python, no deps. | Easy |
| Unbreaker.lua redirect logic | Live probe via pz-test-pilot. No unit test possible (Kahlua). | Medium |
| New redirects valid (Phase 2) | `batch_probe.py`: probe each `_G.Foo` exists via pz-test-pilot | Medium |
| Workshop publish pipeline | Manual first time. Replicate in GH Action post-launch. | Hard (2FA) |
| Load order | Empirical test: does Unbreaker's override catch require() calls from mods that load before it? | **Critical. Must be answered before ship.** |

### Complexity estimate:
Pre-ship checklist items: 1-2 days of focused work (excluding load order investigation, which depends on PZ testing access). Phase 2 batch probe: 1-3 days including one pz-test-pilot session.

## Atlas's Architecture Blueprint

### System design: Tiered Release (v1.0 now, v1.1 gated on evidence)

**v1.0 (this week, manual publish):**
- Current 27 redirects ship as-is
- Manual SteamCMD upload (one command: `steamcmd +login ... +workshop_build_item ...`)
- Workshop description with scope boundary
- README, CHANGELOG, "singleplayer verified / MP untested" disclaimer
- Copy `workshopid` from Workshop URL into both `mod.info` files immediately after first publish, commit

**v1.0.x (weeks 2-3, manual patches):**
- Phase 2 triage: batch-probe 303 misses via pz-test-pilot, add verified winners
- Target: 80+ redirects
- Each batch is a manual re-upload with updated data
- Multiplayer test if a willing second account is available

**v1.1 gate (evaluate at 4 weeks post-launch):**
- Trigger for CI automation: manual upload frequency exceeds once per week
- Trigger for CONTRIBUTING.md + contributor docs: issue velocity > 3/week or first external PR received
- Trigger for PZ Mod Checker integration: separate repo, separate timeline, pull not push

### SteamCMD 2FA strategy: Manual for v1.0, defer automation

Two automation paths exist; neither is good for a solo maintainer right now:
1. `steam-totp` generates codes from shared secret in CI. Works but requires storing Steam Guard shared secret as a GH secret. Full account compromise if leaked.
2. Sentry file / cached credentials. Breaks when Steam rotates tokens (weeks to months).

Decision: publish manually for v1.0. The update cadence (data changes less than weekly) doesn't justify the 2FA risk. Revisit if upload frequency exceeds once per week post-launch.

### Integration points:

- **PZ Mod Checker**: Separate repo, separate ship timeline. PZMC can fetch Unbreaker's JSON independently. Don't couple the ship dates.
- **pz-test-pilot**: Developer-only. Never ships to Workshop. Used for batch probe sessions. Current stability on B42.17 is unknown, needs checking before Phase 2 begins.
- **GitHub Actions**: `generate.yml` auto-regenerates `UnbreakerData.lua` on JSON change (after the path bug is fixed). `publish.yml` deferred to post-launch.

### Kill-switch criteria (evaluate monthly):

| Condition | Action |
|-----------|--------|
| TIS ships a breaking API change that invalidates the require() override pattern entirely | Archive project |
| No activity in 90 days AND < 200 subscribers AND no external issues filed | Archive project |
| Issue volume > 20/week with no community help materializing | Archive or seek co-maintainer |
| A competing mod ships that does the same thing better | Evaluate, then archive or differentiate |

Note: 30-day/100-subscriber threshold from initial review was too tight. Extended to 90 days minimum with at least one external signal required. Issue velocity (3/week) is a better automation trigger than subscriber count.

### Build sequence:

```
Week 1:  Pre-ship checklist (8 items below) → manual Workshop publish
Week 2-3: Phase 2 batch probe → add verified entries → manual re-uploads
Week 4+:  Evaluate automation triggers, write CONTRIBUTING.md if justified
```

## Risks & Concerns

### Code Risks

| Risk | Raised by | Consensus | Detail |
|------|-----------|-----------|--------|
| **CI workflow has never committed since B42 migration** | Soren, confirmed by all | Unanimous | `generate.yml:28` references `mod/media/lua/shared/UnbreakerData.lua`, actual output is `mod/42/media/lua/shared/UnbreakerData.lua`. One-line fix. Currently committed file is correct (maintainer ran locally), but any contributor PR relying on CI auto-generation will produce stale output. |
| **Alias code path is dead with a latent bug** | Soren (round 1), confirmed by all | Unanimous (remove) | Zero JSON entries have `alias` field. `resolveGlobal(entry.alias)` would treat module paths as global names, which never match. Remove before ship; re-add with a test case when needed. |
| **`verified: false` not enforced by generator** | Atlas (round 1) | Unanimous (not a blocker) | `generate_lua.py:44` filters only `category == "unrecoverable"`. AquaConfig ships `verified: false`. Failure mode is benign: if `_G.AquaConfig` doesn't exist, redirect falls through to nil (same as no entry). Policy violation, not correctness risk. Document the exemption case. |
| **`generate_lua.py` docstring lies about output path** | Atlas (round 2), confirmed | Unanimous | Line 5 says `mod/media/lua/shared/UnbreakerData.lua`. Actual: `mod/42/media/...`. Trivial fix. |
| **Version string is `0.1.0-dev`** | Soren (round 2) | Unanimous | Both mod.info files and Unbreaker.lua:89. Must bump before Workshop publish. |

### Architecture Risks

| Risk | Raised by | Consensus | Detail |
|------|-----------|-----------|--------|
| **Load order is unverified and "U" sorts late** | Soren (round 1), escalated by all | **Unanimous: ship blocker.** | PZ's shared Lua load order mechanism is undocumented. "Unbreaker" sorts after most mods alphabetically. If mods loading before Unbreaker call require() before the override is in place, those calls are permanently uncaught. The 98.6% hit rate proves the override works when it fires; it does not prove it fires before all relevant calls. Fix options: rename to sort first (`_Unbreaker`, `00_Unbreaker`), find a mod.info priority field, or empirically confirm load order is not alphabetical by mod name. |
| **Multiplayer checksum risk** | All | Unanimous (document, don't block) | PZ checksums mod files. If server lacks Unbreaker, client's extra files cause checksum mismatch. Not a code problem. Documentation: "Singleplayer verified. For multiplayer, server must also have Unbreaker installed." Empirical MP test is Phase 2, not a ship gate. |
| **B42 patch cadence makes data stale within weeks** | Morgan (round 2), endorsed by all | Unanimous (acknowledged, no mechanical fix at v1.0) | Every B42.x+1 can silently invalidate verified entries. A global that existed in B42.17 might not exist in B42.19. Redirects that start returning nil from `rawget(_G, ...)` after a patch are a diagnostic blind spot: the miss buffer doesn't record them because the entry exists. Worth documenting. No mechanical solution at v1.0. |
| **`workshopid` missing from both mod.info files** | Atlas (round 2) | Unanimous | First SteamCMD publish generates a Workshop item ID. If not committed to mod.info before second publish, a duplicate Workshop item gets created. Must be a documented step in publish checklist. |

### UX Risks

| Risk | Raised by | Consensus | Detail |
|------|-----------|-----------|--------|
| **Brita/Arsenal expectation gap** | Morgan (round 1) | Unanimous on mechanism, disputed on magnitude | Brita's Weapon Pack has 14M+ subscribers. "Unbreaker" as a name implies it can fix anything broken. Morgan estimated 70% of early Workshop comments would be Brita complaints. Soren challenged the specific number (no evidence). All three agree on the fix: name Brita, Arsenal, and True Actions explicitly as out-of-scope in paragraph one of the Workshop description, before anyone subscribes. |
| **No in-game feedback for partial success** | Morgan (round 1) | Unanimous (accepted, not solvable at v1.0) | When Unbreaker serves 139/141 calls, the player sees nothing. If 2 mods still crash, they assume Unbreaker is broken. No way to surface "fixed 12 of your mods but these 2 need author updates" without an in-game UI, which conflicts with the "invisible" design goal. The console print is the only signal. |
| **Workshop comment management strategy missing** | Morgan (round 1) | Unanimous | Solo maintainer + frustrated player comments = burnout vector. Pinned comment with scope boundary on day one. No other tooling until comment volume justifies it. |
| **`preview.png` and `poster.png` are untracked** | Atlas (round 2) | Unanimous | Both files exist locally, never committed. mod.info has no `icon=` field. Workshop VDF needs a preview image path. These must be committed and included in the mod package before publish. |
| **Silent success skews reviews negative** | Soren (round 2) | Unanimous (acknowledged, not fixable at launch) | Satisfied users have no prompt to leave positive reviews. The review-to-subscriber ratio will be skewed negative because the mod's best UX outcome is invisibility. |

## Gaps in the Plan

| Gap | Identified by | Resolution |
|-----|--------------|------------|
| **No mechanism to detect when existing verified entries break after a PZ patch** | Morgan (round 2) | The miss buffer catches new failures but not redirects that start returning nil after a patch changes a global. Add a `stale_check` mode to `final_probe.py` that re-verifies all existing entries. Run after each PZ patch. Phase 2 work. |
| **Contributor verification requires pz-test-pilot, which is not documented for external use** | Morgan (round 1) | Make Rob's verification role explicit in CONTRIBUTING.md: "Submit your entry without `verified: true`. Maintainer runs the probe, sets verified, merges." Lower the contributor bar. Don't require contributors to run pz-test-pilot. |
| **No `--check` mode in `generate_lua.py` for CI validation** | Soren (round 1) | Add a `--check` flag that diffs output against committed file, exits non-zero on mismatch. Use in CI to catch stale generated output in PRs. Post-ship. |
| **`missSeen` grows unbounded** | Soren (round 1) | 303 entries in practice is trivial. Not a real risk. Document the design decision in a code comment. |
| **No README exists** | Morgan (journey analysis) | Write before publish. Scope: what it does, what it doesn't, install instructions, "Report issues" link, license. |
| **WorldGen/features family (~50 miss entries) may not have matching globals** | Soren (round 1) | These may be module-return-value files, not side-effect globals. Probe before batch-adding. If they don't set globals, adding redirects would change behavior from "pass-through nil" to "consumed but still nil." Phase 2 triage, not v1.0. |

## Open Questions

| # | Question | Owner | Urgency | Notes |
|---|----------|-------|---------|-------|
| 1 | **What controls PZ shared Lua load order?** | Rob | **SHIP BLOCKER** | If alphabetical by mod name, "U" sorts late and many require() calls from A-T mods are never intercepted. Must be answered empirically or via PZ source/docs before any Workshop publish. Fix may be as simple as renaming to `_Unbreaker` or `00_Unbreaker`. |
| 2 | Is pz-test-pilot stable on current B42.x? | Rob | High (gates Phase 2 timeline) | Session 2 hit two B42 bugs in the harness. If B42.18 introduced new regressions, Phase 2 batch probe timeline is undefined. Not a v1.0 ship blocker. |
| 3 | What do `mod/poster.png` and `mod/preview.png` look like? | Rob | High (determines whether Direction B requires visual redesign) | Both untracked. If they already establish a visual identity, the Workshop presence should match, not override. |
| 4 | Does AquaConfig's `AMC_AquaConfig.lua` return a table or set `_G.AquaConfig`? | Rob | Low | Determines whether the current `global: "AquaConfig"` entry is correct or should use alias. Only verifiable with the mod installed. |
| 5 | MP checksum: does server-side install resolve checksum mismatch? | Rob | Medium (Phase 2) | Current "requires server-side install" framing is a reasonable guess but unverified. Needs a real MP test with two accounts or a willing tester. |

## Recommended First Phase

### Pre-Ship Checklist (8 items, ordered by dependency)

This is the minimum viable scope. Everything else is post-ship.

| # | Item | Blocker? | Effort |
|---|------|----------|--------|
| 1 | **Answer load order question empirically** | YES | Variable. One PZ test session, or rename mod to `_Unbreaker`/`00_Unbreaker` as a safe default. |
| 2 | Fix `generate.yml:28` file_pattern to `mod/42/media/lua/shared/UnbreakerData.lua` | YES | 1 line |
| 3 | Fix `generate_lua.py:5` docstring path | No | 1 line |
| 4 | Run generator locally, diff against committed UnbreakerData.lua (confirmed matching in this review, but verify after any JSON edits) | YES | 5 min |
| 5 | Remove alias dead code from `Unbreaker.lua:64-75` | No | 12 lines removed |
| 6 | Bump version `0.1.0-dev` to `1.0.0` in both mod.info files + `Unbreaker.lua:89` | YES | 3 lines |
| 7 | Commit `mod/poster.png`, `mod/preview.png` to git. Verify they work for Workshop VDF. | YES | 5 min |
| 8 | Write Workshop description with Brita/Arsenal/True Actions named as out-of-scope in paragraph one. Write minimal README. | YES | 30 min |

**After first publish:** Copy `workshopid` from Workshop URL into both `mod.info` files. Commit immediately. This prevents duplicate Workshop items on subsequent uploads.

**What is NOT a ship prerequisite:** Batch probe of 303 misses. SteamCMD CI automation. CONTRIBUTING.md. MP verification. GitHub Pages form. PZ Mod Checker integration. `--check` mode for generator. These are all Phase 2 or later.

### Phase 2 (weeks 2-4 post-ship):
- Batch-probe 303 misses via pz-test-pilot (target: 80+ verified redirects)
- Write CONTRIBUTING.md with explicit "submit unverified, maintainer verifies" workflow
- MP checksum test if feasible
- Add `stale_check` mode to `final_probe.py` for post-patch validation
- Evaluate automation triggers

### Decision points:
- If B42.x+1 drops before batch probe completes: ship whatever's verified, don't wait
- If manual upload frequency > 1/week: build `publish.yml` with SteamCMD automation
- If issue velocity > 3/week or first external PR arrives: write CONTRIBUTING.md
- Monthly kill-switch evaluation against criteria above

---
*Generated by Collab Plan (Soren + Atlas + Morgan), collaborative pre-flight review with extended thinking*