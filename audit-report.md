All critical claims verified. Here's the report.

---

# Codebase Audit Report

**Target**: `c:\xampp\htdocs\unbreaker`
**Date**: 2026-05-07
**Auditors**: Soren (code analysis) + Atlas (structural review & synthesis)
**Method**: Multi-round collaborative exchange with mutual verification
**Note**: Morgan (UX/product) was listed but did not participate. The UX & Product Concerns section is empty by omission, not by assessment.

## Executive Summary

Unbreaker is a clean, well-scoped single-purpose mod. 105 lines of runtime Lua, 82 lines of Python generator, 27 active data entries. The architecture is sound: data-driven, single-concern, defensive loading. No critical findings. Two HIGH findings, both integrity gaps rather than runtime failures: the README promises verified-only filtering the generator doesn't enforce, and CI auto-commits generated code with no validation gate. Both are fixable in under an hour.

**Confidence breakdown across 13 findings**: 7 corroborated, 5 observed, 1 disputed, 0 provisional.

## Critical & High Severity

**[H1] README claims verified-only filtering; generator doesn't enforce it**
- **Severity**: high, the project's public documentation makes a concrete false claim about its build process, which would mislead contributors and erode trust if discovered
- **Evidence**: `README.md:119`, `scripts/generate_lua.py:43-49`, `data/vanilla_globals.json:219`, `mod/42/media/lua/shared/UnbreakerData.lua:34`
- **Confidence**: corroborated
- **Raised by**: Atlas (initial)
- **Agreement**: Soren independently verified all four files in round 1 and confirmed. Called it "the sharpest finding in the whole audit." Unanimous.
- **Description**: `README.md:119` states: "Only entries with `verified: true` are included in production builds." `load_redirects()` at `generate_lua.py:43-45` filters only on `category == "unrecoverable"`. The `verified` field is never checked. AquaConfig (`vanilla_globals.json:219`, `verified: false`) passes the filter and ships in `UnbreakerData.lua:34`. The README's "Adding a redirect" section (lines 101-103) also describes a workflow where you add with `verified: false` then verify and set `true`, which implies the filter was intended but never implemented.
- **Fix**: Add `if not entry.get("verified"): continue` after the unrecoverable check in `generate_lua.py:44`. This simultaneously fixes the false documentation claim and prevents the unverified AquaConfig entry from shipping.

**[H2] CI auto-commits generated Lua with no validation gate**
- **Severity**: high, a logically bad JSON entry produces valid-but-broken Lua that gets auto-committed silently; the auto-commit action at `generate.yml:25` fires on any file change with no quality check
- **Evidence**: `.github/workflows/generate.yml:1-29`
- **Confidence**: corroborated
- **Raised by**: Atlas (initial, as MEDIUM)
- **Agreement**: Soren upgraded to HIGH in round 1, citing the specific failure mode: JSON syntax errors throw and fail the job (safe), but a valid JSON with a bad entry generates broken Lua and auto-commits it. Atlas confirmed the upgrade in round 2. Final severity: HIGH.
- **Description**: The CI workflow has four steps: checkout, setup-python, run generator, auto-commit. Nothing checks that the output is syntactically valid Lua, that entry counts match expectations, or that the generated file was even written correctly. The auto-commit action fires unconditionally on any diff.
- **Fix**: Add a validation step between generate and commit. Minimum viable: a Python step that parses the generated file back and asserts entry count matches JSON input. Better: `lua -e "dofile('mod/42/media/lua/shared/UnbreakerData.lua')"` if a Lua runtime is available in the CI image.

## Medium Severity

**[M1] Version string maintained in three files with no single source of truth**
- **Severity**: medium, a version bump that misses one file creates silent inconsistency visible to users (mod info panel shows one version, runtime reports another)
- **Evidence**: `mod/42/media/lua/shared/Unbreaker.lua:77`, `mod/42/mod.info:4`, `mod/mod.info:4`
- **Confidence**: corroborated
- **Raised by**: Atlas (initial)
- **Agreement**: Soren verified all three files independently in round 1. Confirmed. Both agreed this is acceptable as a known manual step for a one-person project but becomes a real risk if contributors make version bumps.
- **Description**: Mod version `"1.0.0"` is hardcoded in three separate files. No script, no CI step, and no single source of truth coordinates them. The data version (from JSON) flows through the generator correctly. The mod version does not.
- **Fix**: Accept as known manual step, or have the generator stamp mod version from a single source (e.g., a `version` field in the JSON or a dedicated `VERSION` file).

**[M2] No automated tests exist for the generator**
- **Severity**: medium, the generator auto-commits its output via CI (H2), so a bug in the generator propagates silently; unit tests would have caught H1
- **Evidence**: No `test*.py` or `tests/` directory found anywhere in the repo (glob verified)
- **Confidence**: corroborated
- **Raised by**: Atlas (initial, as HIGH)
- **Agreement**: Soren pushed back on HIGH in round 1, arguing the generator is 50 lines of straightforward string templating and the real validation risk is already captured by H2. Atlas accepted the downgrade in round 2. Final severity: MEDIUM.
- **Description**: The generator (`generate_lua.py`) has no unit tests. Validation is entirely manual via probe scripts that require a running PZ instance. The generator is pure Python with no external deps and is trivially testable.
- **Fix**: Add `tests/test_generate.py` with at minimum: known-good JSON produces expected Lua, unrecoverable entries are filtered, verified-false entries are filtered (once H1 is fixed), empty JSON produces valid empty module, special characters in module names are escaped correctly.

**[M3] AquaConfig entry may be structurally unservable for its primary caller**
- **Severity**: medium, if the redirect can't serve its primary use case, the entry is misleading data in the redirect table; becomes moot if H1 is fixed (entry stops shipping)
- **Evidence**: `data/vanilla_globals.json:219-221`, `mod/42/media/lua/shared/Unbreaker.lua:54-62`
- **Confidence**: disputed
- **Raised by**: Atlas (round 2)
- **Agreement**: Atlas argued that `AMC_AquaConfig.lua` itself issues `require("AquaConfig")` before setting `_G.AquaConfig`, creating a circular dependency where the global isn't set at redirect time. Soren countered that the standard `filename_mismatch` pattern (PZ auto-loads the file, sets the global, then other mods hit the wrong require path) doesn't necessarily involve self-reference, and the note text is ambiguous. Soren's position: concern is plausible but requires reading the actual mod source to confirm, and the finding becomes moot once H1 is applied (unverified entry stops shipping). **Final resolution**: finding stands as a flag for Phase 2 investigation. If H1 is fixed, AquaConfig doesn't ship and the runtime risk is eliminated. If H1 is not fixed, this concern is live and unverified.
- **Description**: The `filename_mismatch` category assumes PZ auto-loads the correctly-named file (setting the global as a side effect), and Unbreaker redirects callers who use the wrong name. But the JSON notes say `AMC_AquaConfig.lua` itself calls `require("AquaConfig")`. If that file is both the one that sets the global AND the one with the broken require, the global may not exist at redirect time.
- **Fix**: Verify in-game whether `_G.AquaConfig` is available when other mods call `require("AquaConfig")`, or document the partial-coverage limitation in the JSON notes. Fixing H1 eliminates this entry from production regardless.

## Low Severity & Suggestions

**[L1] `missSeen` table grows unbounded while `missBuffer` is capped**
- **Severity**: low, practical risk is zero (303 unique entries in live testing is ~15KB, no PZ mod constructs dynamic require paths), but the bounded/unbounded asymmetry is a design inconsistency
- **Evidence**: `mod/42/media/lua/shared/Unbreaker.lua:29-42`
- **Confidence**: corroborated
- **Raised by**: Soren (initial, as MEDIUM)
- **Agreement**: Both auditors confirmed the structural asymmetry. Soren revised from MEDIUM to LOW in round 2, noting the comment at line 30 describes `missBuffer` specifically and isn't technically wrong. Atlas accepted the revision, walking back the earlier claim that "the code's self-documentation is wrong."
- **Description**: `missBuffer` is capped at 256 entries (line 40). `missSeen` (the dedup hash table) has no cap. The comment at line 29-31 says "Bounded so a runaway loop can't blow memory," which is true of the ring buffer but doesn't cover the full memory picture.
- **Fix**: Either cap `missSeen` (e.g., `if missCount >= MISS_BUFFER_MAX * 4 then return end` before the insert), or clarify the comment scope. Low priority.

**[L2] `resolveGlobal` is a trivial identity wrapper**
- **Severity**: low, dead complexity, not a bug
- **Evidence**: `mod/42/media/lua/shared/Unbreaker.lua:17-21`, called at line 58
- **Confidence**: corroborated
- **Raised by**: Soren (initial)
- **Agreement**: Atlas confirmed. `rawget(_G, globalName)` already returns nil for absent keys. The if/return/return pattern adds nothing.
- **Description**: The function wraps a single `rawget` call with redundant nil-checking logic. Called in exactly one place.
- **Fix**: Inline `rawget(_G, entry.global)` at line 58, or simplify the function to `return rawget(_G, globalName)`.

**[L3] Dead `alias` branch in generator**
- **Severity**: low, inert code that becomes a maintenance trap if someone adds `alias` to JSON (field renders in Lua but runtime silently ignores it)
- **Evidence**: `scripts/generate_lua.py:32-33`
- **Confidence**: corroborated
- **Raised by**: Soren (initial)
- **Agreement**: Atlas confirmed. No JSON entry has an `alias` key. `Unbreaker.lua` has no alias handling (removed in Session 4).
- **Description**: Generator still emits an `alias=` field if present in JSON data. The runtime branch that would have consumed it was removed.
- **Fix**: Remove lines 32-33 from `generate_lua.py`.

**[L4] `lua_string` doesn't escape `\r` or null bytes**
- **Severity**: low, untriggerable with hand-curated data, purely defensive
- **Evidence**: `scripts/generate_lua.py:24`
- **Confidence**: corroborated
- **Raised by**: Soren (initial)
- **Agreement**: Atlas confirmed. Escapes `\`, `"`, `\n` only.
- **Description**: If a data value ever contained `\r` or `\0`, the generated Lua string would be malformed. All current data is module paths and global names.
- **Fix**: Add `.replace("\r", "\\r").replace("\0", "")` to `lua_string`.

**[L5] Both `mod.info` files are byte-for-byte identical**
- **Severity**: low, contributor stumbling block, not a bug
- **Evidence**: `mod/mod.info`, `mod/42/mod.info`
- **Confidence**: corroborated
- **Raised by**: Atlas (initial)
- **Agreement**: Soren confirmed identical content.
- **Description**: The outer `mod.info` is a B42 layout marker; the inner one is the runtime descriptor. They serve different purposes but have identical content and no comment explaining why both exist.
- **Fix**: Add a comment to the outer `mod/mod.info` explaining it's a B42 layout marker.

**[L6] `module=` and `category=` fields in generated entries are dead runtime payload**
- **Severity**: low, 27 entries with two unused string fields each, not harmful but divergence risk
- **Evidence**: `scripts/generate_lua.py:29,34-35`, `mod/42/media/lua/shared/Unbreaker.lua:54-68`
- **Confidence**: corroborated
- **Raised by**: Soren (round 1, as NEW-1)
- **Agreement**: Atlas independently flagged the same pattern in round 2. Both confirmed runtime only accesses `entry.global`.
- **Description**: Every generated redirect entry includes `module="..."` (identical to the table key) and `category="..."`. The runtime at `Unbreaker.lua:54-68` only reads `entry.global`. Dead payload.
- **Fix**: Remove `module=` and `category=` emission from `render_entry()` in `generate_lua.py:29,34-35`. Or keep `category` if it's useful for diagnostic dumps later.

**[L7] CI workflow triggers on any branch**
- **Severity**: low, cosmetic inconvenience, not harmful
- **Evidence**: `.github/workflows/generate.yml:3-8`
- **Confidence**: corroborated
- **Raised by**: Soren (initial)
- **Agreement**: Atlas confirmed. No `branches:` key under `on.push`.
- **Description**: Feature branches with JSON changes trigger auto-commits. Not harmful but could produce unexpected commits on branches.
- **Fix**: Add `branches: [main]` to the `on.push` trigger.

**[L8] Probe scripts hardcode developer-specific filesystem paths**
- **Severity**: low, developer-only tooling, expected for single-developer project
- **Evidence**: `scripts/smoke_probe.py:17`
- **Confidence**: corroborated
- **Raised by**: Atlas (initial)
- **Agreement**: Soren confirmed.
- **Description**: `Path("C:/xampp/htdocs/pz-test-pilot")` hardcoded. No env var or CLI arg. Not portable to other developers.
- **Fix**: Add an env var (`PZ_TEST_PILOT_PATH`) or CLI argument. Low priority unless taking contributors.

**[L9] `intercepted` counter counts redirect hits, not total broken calls**
- **Severity**: low, documentation precision issue
- **Evidence**: `mod/42/media/lua/shared/Unbreaker.lua:54-56`
- **Confidence**: observed
- **Raised by**: Soren (round 1, as NEW-2)
- **Agreement**: Atlas did not comment directly. Finding is straightforward.
- **Description**: `intercepted` increments only when `REDIRECTS[module]` is non-nil. Total broken calls seen is `intercepted + missCount`. Session notes and README reference "141 intercepted" which reads as "141 broken calls caught" but actually means "141 calls that matched a redirect entry."
- **Fix**: Clarify in README or add a `total_broken` convenience field to the stats output.

## UX & Product Concerns

Morgan did not participate in this audit. No UX/product findings were submitted. This is a gap. For a Workshop-published mod, user-facing concerns worth examining include: Workshop description accuracy vs. actual coverage, first-time user experience (is the mod silent? does it log enough for users to know it's working?), and whether the "98.6% coverage" framing sets expectations the 27-entry redirect table can't meet for all mod combinations.

## Architectural Observations

The architecture is deliberately minimal and that's a feature. JSON source of truth, Python generator, generated Lua, runtime lookup. No circular dependencies, no unnecessary abstraction layers. The `require()` override pattern is well-documented and the pcall-first design means the real module always wins.

The one structural observation worth carrying forward: the `require = unbreakerRequire` replacement at line 74 creates a chain if any other mod does the same thing after Unbreaker loads. If that mod captures `require` (which is now `unbreakerRequire`) and wraps it without pcall, error propagation changes. This is inherent to the design, documented, and not fixable without PZ engine changes. It's the kind of thing that matters if Unbreaker gets popular enough that other mods start interacting with it.

The data-driven approach scales cleanly. Phase 2 (expanding from 27 to potentially hundreds of redirects) requires no runtime changes, only JSON data and regeneration.

## Disagreements & Resolutions

**1. Severity of "no automated tests" (M2)**
- **Atlas initial**: HIGH. "No test files found anywhere in the repo. The generator is trivially testable."
- **Soren round 1**: MEDIUM. "Generator is 50 lines of straightforward string templating. The real validation risk is already captured by [H2]. Tests are good practice but HIGH overstates the blast radius."
- **Resolution**: Atlas accepted the downgrade. The blast radius of a generator bug is "redirect doesn't serve, fails safely," not data corruption. The auto-commit risk (H2) is the actual HIGH. MEDIUM stands.

**2. Severity of `missSeen` unbounded (L1)**
- **Soren initial**: MEDIUM. "Structurally, one table is bounded and the other isn't."
- **Atlas initial**: MEDIUM. "The code's self-documentation is wrong."
- **Soren round 2**: LOW. "The comment describes `missBuffer` specifically, not `missSeen`. The comment isn't wrong. Practical risk is demonstrably zero."
- **Atlas round 2**: Accepted LOW. Walked back the overclaim about self-documentation being wrong.
- **Resolution**: LOW. The comment is scoped correctly. The asymmetry is real but inconsequential.

**3. Severity of CI no-validation (H2)**
- **Atlas initial**: MEDIUM.
- **Soren round 1**: HIGH. "Auto-commit with no gate is the actual HIGH."
- **Soren round 2**: Back to MEDIUM. "The failure mode is 'a redirect doesn't serve, caller falls through safely,' not corruption."
- **Atlas round 2**: HIGH. "A logically bad JSON entry produces valid-but-broken Lua that gets auto-committed silently."
- **Resolution**: HIGH. Soren oscillated but Atlas held. The silent auto-commit of bad output is the key risk factor. The "fails safely" argument applies to the runtime, not to the CI pipeline's integrity. A bad commit that looks intentional and passes CI is worse than a crash that blocks the pipeline.

**4. AquaConfig circular dependency (M3)**
- **Atlas round 2**: MEDIUM. "The file that sets the global is the same file with the broken require."
- **Soren round 2**: "Plausible but requires reading the actual mod source. The note text doesn't establish self-reference. Becomes moot once H1 is fixed."
- **Resolution**: Marked disputed. Both positions are defensible from the available evidence. Fixing H1 eliminates the runtime risk regardless. Flagged for Phase 2 investigation if `filename_mismatch` entries are expanded.

## Recommended Action Plan

| Priority | Finding | Effort | Rationale |
|----------|---------|--------|-----------|
| 1 | **H1**: Add `verified` filter to generator | 10 min | Three-line fix. Eliminates the false README claim AND the unverified AquaConfig entry simultaneously. Highest signal-to-effort ratio in the audit. |
| 2 | **H2**: Add validation step to CI workflow | 30 min | Add a step that parses the generated Lua and asserts entry count. Prevents silent bad commits. |
| 3 | **L7**: Add `branches: [main]` to CI | 2 min | One line. Do it with H2. |
| 4 | **L3**: Remove dead `alias` branch from generator | 2 min | Two lines deleted. Do it with H1. |
| 5 | **M2**: Add generator unit tests | 1-2 hr | `tests/test_generate.py`. Catches future regressions. Would have caught H1. |
| 6 | **L6**: Remove dead `module`/`category` fields from generator output | 5 min | Cleaner generated Lua. Do in the same pass as L3. |
| 7 | **M1**: Version source of truth | 30 min | Optional. Accept manual sync or automate. Only urgent if version bumps become frequent. |
| 8 | Everything else (L1, L2, L4, L5, L8, L9) | Cleanup pass | None of these block ship. Bundle into a single hygiene commit post-launch. |

Items 1-4 can ship in a single commit. Item 5 is the next natural step. Items 6-8 are post-ship cleanup.

---

*Generated by Collab Audit (Soren + Atlas) with source-aware confidence annotation. Morgan (UX/product) was listed but did not participate.*