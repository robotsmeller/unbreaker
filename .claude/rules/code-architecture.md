# Code Architecture Rules

## Lua Mod

- **Kahlua constraints**: No `io.*`, no `os.*`, no `socket`, no `luajava` networking
- **require() override is the core pattern** — never use package.preload (unverified in Kahlua)
- **UnbreakerData.lua is generated** — never edit it manually, always edit the JSON source
- **Lua 5.1 compatible** — no goto, no bitwise operators, no integer division //
- **Error-safe stubs** — all stub functions wrapped in pcall where called, never throw

## Python Tooling (scripts/)

- **stdlib only** — no pip dependencies for the generator
- **Pathlib everywhere** — never os.path string manipulation
- **Type hints** on all function signatures
- **Single responsibility** — generate_lua.py does one thing: JSON in, Lua file out

## Data Format (vanilla_globals.json)

```json
{
  "version": "1.0.0",
  "last_updated": "YYYY-MM-DD",
  "redirects": [
    {
      "module": "ISUI/ISInventoryPaneContextMenu",
      "global": "ISInventoryPaneContextMenu",
      "category": "vanilla_global",
      "since_pz": "42.0.0",
      "verified": true,
      "notes": "..."
    }
  ]
}
```

Categories:
- `vanilla_global` — file moved to auto-loaded global in B42
- `filename_mismatch` — mod requires wrong filename (e.g. underscore mismatch)
- `library_stub` — partial API stub for a major library mod

## GitHub Issues Convention

- Title: `[mod-name] brief description`
- Labels: `vanilla-global`, `library-stub`, `mod-request`, `bug`, `verified`, `needs-testing`
- Every redirect added must have `verified: true` before merging — tested in actual PZ
