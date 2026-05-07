-- Unbreaker — require() polyfill for Project Zomboid mods.
--
-- Wraps require() so that when a module fails to load, we check a redirect
-- table for a known fix (a vanilla global that moved, a filename mismatch).
-- The original require() is always tried first via pcall — real modules win.

if _G.Unbreaker_Loaded then return end
_G.Unbreaker_Loaded = true

local DATA_OK, DATA = pcall(require, "UnbreakerData")
if not DATA_OK or type(DATA) ~= "table" then
    DATA = { redirects = {}, version = "0.0.0-empty" }
end

local REDIRECTS = DATA.redirects or {}

local _require = require

-- intercepted: calls where a redirect entry exists (served or not)
-- unknown: broken calls with no redirect entry at all
local intercepted = 0
local served = 0
local missed = 0
local unknown = 0

-- Ring buffer of module names we couldn't redirect (for diagnostic dumps).
-- Both missBuffer (captured names) and missSeen (dedup) are bounded.
local MISS_BUFFER_MAX = 256
local MISS_SEEN_MAX = MISS_BUFFER_MAX * 4
local missBuffer = {}
local missSeen = {}
local missCount = 0

local function recordMiss(module)
    if missSeen[module] then return end
    if missCount >= MISS_SEEN_MAX then return end
    missSeen[module] = true
    missCount = missCount + 1
    if #missBuffer >= MISS_BUFFER_MAX then return end
    missBuffer[#missBuffer + 1] = module
end

-- B42 require() quirk: vanilla files set `_G.Name = SomeClass:derive(...)` as
-- a side-effect and never `return` anything, so require() succeeds with nil.
-- Mods that store the require() result in a local and try to use it crash
-- later with "attempt to index nil". We treat (ok and nil) the same as a
-- pcall failure, consult REDIRECTS, and fall back to original behaviour if
-- there's no entry for the module.
local function unbreakerRequire(module)
    local ok, result = pcall(_require, module)
    if ok and result ~= nil then return result end

    local entry = REDIRECTS[module]
    if entry then
        intercepted = intercepted + 1
        if entry.global then
            local g = rawget(_G, entry.global)
            if g ~= nil then
                served = served + 1
                return g
            end
        end
        missed = missed + 1
        recordMiss(module)
    else
        unknown = unknown + 1
        recordMiss(module)
    end

    if not ok then error(result, 2) end
    return result
end

require = unbreakerRequire

_G.Unbreaker = {
    version = "1.0.1",
    data_version = DATA.version,
    redirect_count = 0,
    stats = function()
        return {
            intercepted = intercepted,
            served = served,
            missed = missed,
            unknown = unknown,
            total_broken = intercepted + unknown,
        }
    end,
    has_redirect = function(module)
        return REDIRECTS[module] ~= nil
    end,
    list_redirects = function()
        local list = {}
        for k, _ in pairs(REDIRECTS) do
            list[#list + 1] = k
        end
        return list
    end,
    misses = function()
        local list = {}
        for i = 1, #missBuffer do list[i] = missBuffer[i] end
        return { total = missCount, captured = list }
    end,
}

local n = 0
for _ in pairs(REDIRECTS) do n = n + 1 end
_G.Unbreaker.redirect_count = n

print("[Unbreaker] loaded v" .. _G.Unbreaker.version .. " — " .. n .. " redirects (data v" .. tostring(DATA.version) .. ")")
