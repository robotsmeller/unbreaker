# Unbreaker

Standalone Project Zomboid Workshop mod that silently fixes broken require() calls
for popular mods that haven't been updated for Build 42.

## Communication Style

Facts only. No fluff. Research before answering. Disagree when wrong.

---

## SESSION START (REQUIRED)

Before ANY work, use `/session-start` skill OR manually:

1. **Read context files:**
   - `HANDOFF.md` - Current state and priorities
   - `.claude/context.md` - Session history

2. **Check GitHub Issues:**
   ```bash
   gh issue list --state open --limit 20
   ```

3. **Output confirmation:**
   ```
   Unbreaker ready. [X] open issues.
   Continue with: [current task]
   ```

---

## PROJECT INFO

| Property | Value |
|----------|-------|
| Folder | `c:\xampp\htdocs\unbreaker` |
| Tech | Lua (PZ mod), Python (tooling), GitHub Actions (CI/CD) |
| Purpose | Fix broken require() calls in popular B42-incompatible mods |
| Target | Project Zomboid Build 42.x |
| Workshop | TBD |

## Architecture

```
data/vanilla_globals.json        # Source of truth: module -> global name mappings
data/library_stubs/              # API surface stubs for major library mods
scripts/generate_lua.py          # Converts JSON -> mod/media/lua/shared/UnbreakerData.lua
mod/                             # The actual PZ Workshop mod
  mod.info
  media/lua/shared/
    Unbreaker.lua                # require() override with pcall fallback
    UnbreakerData.lua            # Generated from JSON, do not edit manually
.github/workflows/
  generate.yml                   # On data change: regenerate UnbreakerData.lua
  publish.yml                    # On release: push to Steam Workshop via SteamCMD
```

## Key Design Decisions

- **require() override pattern**: `local _req = require; require = function(m) local ok,r = pcall(_req,m); if ok then return r end; return STUBS[m] and STUBS[m]() end`
- **Real module always wins**: pcall tries the original require first. Stub only fires on failure.
- **Data-driven**: All redirects live in JSON, never hardcoded in Lua.
- **UnbreakerData.lua is generated**: Edit JSON, run generate_lua.py, commit both. CI does this automatically.
- **Load order**: Mod named to sort early alphabetically. Test whether PZ respects this.

## Mod Scope

**Phase 1 — Vanilla globals** (safe, reliable):
Module paths that moved from require()-able files to auto-loaded globals in B42.
Each entry: module path -> global name to return.

**Phase 2 — Library stubs** (functional stubs for major broken libraries):
damnlib (KI5 vehicles, 2.4M+ subscribers), tsarslib (Tsar/iBrRus family).
Requires implementing enough of the API surface that dependent mods function.

**Out of scope**:
- Brita/Arsenal (needs full rewrite)
- ModOptions (B42 has native replacement, mods should port)
- Mods with deep B42 API breakage beyond require() failures

## PZ Reference

- Mod lives in: `C:\Users\<user>\Zomboid\mods\` or Steam Workshop
- Lua environment: Kahlua (Java-based Lua 5.1)
- `io.*` and `os.*` NOT available in Kahlua
- `package.preload` status: UNVERIFIED — use require() override instead
- Load order: alphabetical by default; `require=` field in mod.info for dependencies

## GitHub Issues

Issues are the primary update mechanism:
- `mod-request` label: community requests to support a specific mod/library
- `vanilla-global` label: new vanilla global redirect to add
- `library-stub` label: API stub work for a major library
- `bug` label: a stub is causing problems or a mod author updated their mod

@.claude/context.md
