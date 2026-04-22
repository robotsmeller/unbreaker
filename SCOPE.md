# Unbreaker — What It Actually Fixes

Unbreaker is a **polyfill** for Project Zomboid mods. The same concept browsers use to
backfill missing JavaScript APIs: detect what's missing, provide a compatible replacement,
step aside when the real thing arrives.

PZ is in active development. Minor patches drop almost weekly. Mod authors can't always
keep up. Unbreaker bridges the gap between "patch broke it" and "author fixed it."

---

## What It Can Fix

### 1. Broken require() calls — vanilla globals

**The problem:** B42 moved certain game files from require()-able paths into always-loaded
global scope. Old mods still call `require("ISUI/ISInventoryPaneContextMenu")`, PZ can't
find the file, crash.

**The fix:** Intercept the require() call, return the global that's already in memory.

```lua
-- Old mod does:
local ctxMenu = require("ISUI/ISInventoryPaneContextMenu")
-- Unbreaker intercepts, returns:
return ISInventoryPaneContextMenu  -- already loaded, always available
```

**Reliability:** High. The global exists. We're just handing it over.

---

### 2. Broken require() calls — filename mismatches

**The problem:** A mod requires its own file under the wrong name (e.g. requires
`SimpleSilencersModelTable` but the file is `SimpleSilencers_ModelTable.lua`). PZ can't
match them, crash.

**The fix:** Same interception, return the global the auto-loaded file already set up.

**Reliability:** High, if the global name is known and the file loaded successfully.

---

### 3. Renamed functions / method aliases

**The problem:** PZ renames or removes a function. Old mods call the old name, crash.

**The fix:** Register the old name as an alias for the new one.

```lua
-- If PZ renamed getCanon() to getWeaponAttachment():
if ItemType and not ItemType.getCanon then
    ItemType.getCanon = ItemType.getWeaponAttachment
end
```

**Reliability:** Medium-high. Works if the underlying behaviour didn't change, just the name.
Fragile if PZ changed what the function does, not just what it's called.

---

### 4. Moved globals

**The problem:** A global table or value moved to a different namespace between patches.

**The fix:** Register the old location pointing to the new one.

```lua
-- If SomeSystem moved to GameSystems.SomeSystem:
SomeSystem = GameSystems.SomeSystem
```

**Reliability:** High if it's a straight move. Medium if the structure changed.

---

## What It Cannot Fix

### Deep API rewrites
The crafting system, animation system, and vehicle physics were overhauled in B42.
Mods built against the old systems need to be rewritten. Unbreaker can't substitute for
that work. There's no shim that makes old crafting code run on a new crafting engine.

### Missing mod dependencies
If a mod requires `DAMN_MechOverlay` and that library isn't installed, Unbreaker can
silence the require() crash with an empty stub — but the mod's features that depend on
that library won't work. An empty table is not a functioning vehicle overlay system.
This is only useful as a last resort and must be clearly labelled as such.

### Translation file gaps
Fixing missing translation keys requires scanning mod files and writing stub files to
disk. Workshop mods run inside PZ's sandboxed Lua environment with no filesystem access.
Not possible. (PZ Mod Checker handles this separately as an external tool.)

### Multiplayer checksum mismatches
PZ validates Lua file checksums in multiplayer. If Unbreaker's require() interception
causes the client's executed code path to differ from the server's expectation, the
session may reject the client. **Unbreaker's multiplayer safety is unverified.**
Test before using on MP servers.

### Behavioural changes
If PZ changed what something *does* (not just where it lives or what it's called),
Unbreaker can't restore the old behaviour. It can only redirect — it can't reimplement.

### Mods that need full rewrites
Brita's Weapon Pack, Arsenal, True Actions — these mods were deeply broken by B42's
fundamental systems changes. No shim fixes them. They need their authors.

---

## The Automatic Handoff

When a mod author publishes a proper B42 fix, Unbreaker detects it automatically.

The require() override uses a try-first pattern:

```lua
local _require = require
require = function(module)
    local ok, result = pcall(_require, module)
    if ok then return result end           -- real module found, use it
    if STUBS[module] then return STUBS[module]() end  -- fall back to stub
    error("module '" .. module .. "' not found", 2)
end
```

If the real module file now exists (because the mod updated), `pcall` succeeds and
returns the real thing. The stub is never called. No intervention needed.

**You do not need to disable Unbreaker when mods update.** It steps aside on its own.

---

## Scope in One Paragraph (for Workshop description)

> Unbreaker keeps your mods working between PZ patches. It fixes broken require() calls,
> renamed functions, and moved globals — the minor API shuffles that happen with almost
> every update. It does NOT fix mods that need deep rewrites, missing mod dependencies,
> or fundamental gameplay system changes. When a mod's author publishes a proper fix,
> Unbreaker automatically steps aside. It is a stopgap, not a replacement for mod updates.

---

## What "Verified" Means

Every entry in `data/vanilla_globals.json` has a `verified` field.

- `false` — sourced from diagnose data, not yet tested in a live PZ session
- `true` — tested in PZ, confirmed the redirect works and the dependent mod functions

**Only verified entries ship in production releases.** Unverified entries exist in the
data for tracking but are excluded from generated Lua until confirmed.
