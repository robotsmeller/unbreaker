# Unbreaker

A standalone Project Zomboid mod that keeps your mods working between patches.

Every PZ update moves something. A file gets renamed, a global shifts scope, a `require()` path changes. Mods that haven't caught up start crashing silently. Unbreaker intercepts those broken `require()` calls and returns the correct value instead.

**Real modules always win.** Unbreaker only fires when the original load fails. When a mod's author ships a proper fix, Unbreaker steps aside automatically. No config needed.

134 verified redirects covering vanilla module paths that moved in B42 patches. Tested in B42.17 against a 180-mod install.

---

## How it works

When a mod loads, it fetches the scripts and tools it depends on by name. Like looking something up in a filing cabinet by its label. PZ patches sometimes reorganize that cabinet: a file gets moved, a label changes. The mod still asks for the old label, finds nothing, and crashes. The error log tells you something failed but not what or why.

Unbreaker watches every one of those lookups. If a lookup succeeds, it steps aside and returns the result untouched. If it fails, Unbreaker checks its redirect list and finds where the thing actually lives now, then hands it back. The mod gets what it needs without knowing anything went wrong.

When a mod author ships a proper fix, the original lookup succeeds again. Unbreaker never fires. Nothing to unsubscribe, nothing to reconfigure.

---

## Install

Subscribe on the [Steam Workshop](#) *(link pending, will update after first publish)*.

### Diagnostic tool

Not sure if Unbreaker covers your mods? Paste your `console.txt` into the [diagnostic tool](https://robotsmeller.github.io/unbreaker/) to see which `require()` failures are fixed, which cannot be fixed, and why. Nothing is uploaded — the log is processed in your browser.

**Build 42 only.** Unbreaker will not work on B41. The redirect data and override pattern target B42's module layout specifically.

### Load order

Unbreaker must load before other mods to intercept their `require()` calls.

**Workshop installs (most users):** handled automatically. Steam assigns a numeric folder ID (e.g. `2987654321`) that sorts before any alphabetically-named local mod folder. No action needed.

**Local installs:** the folder is named `Unbreaker`, which sorts late. Move it to the top of the mod list manually in the PZ mod manager, or rename the folder with a leading character (e.g. `!Unbreaker`) to force it first.

---

## What it fixes

- `require()` calls targeting vanilla files that moved to auto-loaded global scope in B42
- `require()` calls with filename mismatches (mod requires the wrong filename for its own file)
- Moved globals: old location redirected to new one

### Coverage

The redirect list targets vanilla module paths that moved in B42. Those are a finite set. Once all the moved paths are mapped, every mod that breaks for that reason is covered by a single entry, regardless of how many mods use it.

Other failure modes are outside that scope:

- **Self-broken mods:** the mod has a bug in its own require() call, referencing a file that never existed. Nothing to redirect.
- **Missing dependencies:** mod A requires mod B that isn't installed. Unbreaker can't substitute a mod that isn't there.
- **Major libraries:** damnlib and tsarslib are required by hundreds of mods each. They're on the roadmap but not yet stubbed. Mods that depend on them may still fail until that work is done.

If a mod is still broken after installing Unbreaker, one of those three is almost certainly the cause.

## What it does NOT fix

- **Build 41:** Unbreaker is B42-only. B41 has a different module layout and is not targeted.
- **Brita's Weapon Pack, Arsenal, True Actions:** these need their authors to rewrite large parts of the mod. A polyfill can't do that.
- Deep B42 API rewrites (crafting, animation, vehicles)
- Missing mod dependencies
- **Multiplayer:** untested. Single-player only until verified. See roadmap.

---

## Architecture

```
data/vanilla_globals.json          # Source of truth: all redirects live here
scripts/generate_lua.py            # JSON -> UnbreakerData.lua (run manually or via CI)
mod/42/media/lua/shared/
  Unbreaker.lua                    # require() override + miss ring buffer
  UnbreakerData.lua                # Generated: never edit by hand
```

The core pattern:

```lua
local _require = require
require = function(module)
    local ok, result = pcall(_require, module)
    if ok and result ~= nil then return result end  -- real module wins

    local entry = REDIRECTS[module]
    if entry and entry.global then
        local g = rawget(_G, entry.global)
        if g ~= nil then return g end
    end

    if not ok then error(result, 2) end
    return result
end
```

B42's `require()` returns `nil` silently for missing modules rather than throwing. The `ok and result ~= nil` check catches both failure modes: actual errors and silent nil returns.

---

## Adding a redirect

1. Edit `data/vanilla_globals.json`, add an entry with `"verified": false`
2. Test it in a live PZ session
3. Set `"verified": true` and open a PR

The CI workflow regenerates `UnbreakerData.lua` automatically when the JSON changes.

```json
{
  "module": "ISUI/ISInventoryPaneContextMenu",
  "global": "ISInventoryPaneContextMenu",
  "category": "vanilla_global",
  "since_pz": "42.0.0",
  "verified": true,
  "notes": "Moved to auto-loaded global scope in B42."
}
```

Only entries with `"verified": true` are included in production builds.

---

## Reporting issues

Leave a comment on the Workshop page, or open a GitHub issue with:
- The mod name and Workshop ID
- What fails (crash log snippet if you have one)
- Whether the mod works without Unbreaker installed

---

## License

MIT. See [LICENSE](LICENSE).
