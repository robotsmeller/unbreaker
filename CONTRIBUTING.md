# Contributing to Unbreaker

## Adding a redirect

The redirect list lives in `data/vanilla_globals.json`. Each entry maps a broken `require()` path to the global that PZ auto-loads in its place.

1. Add your entry with `"verified": false`:

```json
{
  "module": "ISUI/ISInventoryPaneContextMenu",
  "global": "ISInventoryPaneContextMenu",
  "category": "vanilla_global",
  "since_pz": "42.0.0",
  "verified": false,
  "notes": "Moved to auto-loaded global scope in B42."
}
```

2. Run the generator: `python scripts/generate_lua.py`

3. Test it in a live PZ session. Confirm the mod that was failing now loads.

4. Set `"verified": true` and open a PR.

Only entries with `"verified": true` ship in production builds. Unverified entries are filtered out by the generator.

### Categories

| Category | When to use |
|----------|-------------|
| `vanilla_global` | A vanilla PZ file moved from a `require()`-able path to an auto-loaded global in B42 |
| `filename_mismatch` | A mod requires its own file under the wrong name (e.g. underscore vs. no underscore). The file auto-loads and sets a global; the redirect returns that global. |
| `unrecoverable` | The module was removed with no replacement. Entry is documented but never ships. |

### What makes an entry valid

- The global name must exist in `_G` by the time other mods run. If it doesn't, the redirect returns nil and the caller still crashes.
- The `since_pz` field is when the path broke, not when you added the entry. Check git history or the PZ changelog if unsure.
- If you can't test in a live session, set `"verified": false` and note that in the PR. Someone else will verify before merge.

## Reporting a broken stub

If an Unbreaker redirect is now shadowing a real module (because the mod author shipped a B42 fix), open an issue with the **bug** label and include:

- The module name
- The mod that updated
- What breaks with Unbreaker installed vs. without

The pcall-first pattern means real modules always win, so this should be rare. If it's happening, the mod likely registers its module under a path that collides with an Unbreaker entry.

## Repo layout

```
data/vanilla_globals.json        # source of truth (edit this)
scripts/generate_lua.py          # JSON -> Lua codegen (run after editing JSON)
mod/42/media/lua/shared/
  Unbreaker.lua                  # runtime override (rarely needs changes)
  UnbreakerData.lua              # GENERATED — never edit by hand
mod/mod.info                     # outer mod.info — B42 layout marker, must exist
mod/42/mod.info                  # inner mod.info — runtime descriptor
```

The outer `mod/mod.info` and inner `mod/42/mod.info` are both required by PZ's B42 mod layout. They have identical content. If you bump the version, update both plus the `version` string in `Unbreaker.lua`.

## Running tests

```bash
python -m pytest tests/
```

No dependencies beyond the standard library and pytest.
