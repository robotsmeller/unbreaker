-- Offline test for the saved-outfit guard in UnbreakerPatches.lua.
-- Run from the repo root:  lua tests/lua/test_outfit_guard.lua
--
-- Stubs the handful of PZ globals the patch touches, then loads the real patch
-- file against three versions of the vanilla reader: the 42.20 buggy one, a
-- fixed one, and one that changed its output shape. Kahlua is Lua 5.1; nothing
-- here depends on anything newer.

local FILE = {}

function getFileReader(_, _)
    local i = 0
    return {
        readLine = function() i = i + 1; return FILE[i] end,
        close = function() end,
    }
end

string.split = function(s, sep)
    local t = {}
    for part in string.gmatch(s, "([^" .. sep .. "]+)") do t[#t + 1] = part end
    return t
end

luautils = {
    stringStarts = function(s, p) return string.sub(s, 1, #p) == p end,
    -- verbatim from 42.20.4 shared/luautils.lua
    split = function(inputstr, sep)
        local t = {}
        local i = 1
        for str in string.gmatch(inputstr, "([^" .. sep .. "]+)") do
            t[i] = str
            i = i + 1
        end
        return t
    end,
}

local bootFns = {}
Events = { OnGameBoot = { Add = function(fn) bootFns[#bootFns + 1] = fn end } }
getCore = function() return { getVersion = function() return "42.20.4 test" end } end

local OUTFITS_VERSION = 1

-- verbatim logic from 42.20.4 CharacterCreationMain.readSavedOutfitFile
local function vanillaBuggy()
    local retVal = {}
    local f = getFileReader(nil, true)
    local version = 0
    local line = f:readLine()
    while line ~= nil do
        if luautils.stringStarts(line, "VERSION=") then
            version = tonumber(string.split(line, "=")[2])
        elseif version == OUTFITS_VERSION then
            local s = luautils.split(line, ":")
            retVal[s[1]] = s[2]
        end
        line = f:readLine()
    end
    f:close()
    return retVal
end

-- a later build that fixed the colon bug its own way
local function vanillaFixed()
    local retVal = {}
    local f = getFileReader(nil, true)
    local line = f:readLine()
    while line ~= nil do
        local a, b = string.match(line, "^([^:]+):(.*)$")
        if a and not luautils.stringStarts(line, "VERSION=") then retVal[a] = b end
        line = f:readLine()
    end
    f:close()
    return retVal
end

-- a later build that changed what the reader returns
local function vanillaReshaped()
    local r = vanillaFixed()
    for k, v in pairs(r) do r[k] = { raw = v } end
    return r
end

local function load(vanillaFn)
    CharacterCreationMain = { savefile = "saved_outfits.txt", readSavedOutfitFile = vanillaFn }
    bootFns = {}
    _G.UnbreakerPatches = nil
    dofile("mod/42/media/lua/client/UnbreakerPatches.lua")
    for _, fn in ipairs(bootFns) do fn() end
end

local failures = 0
local function check(name, cond)
    print((cond and "PASS " or "FAIL ") .. name)
    if not cond then failures = failures + 1 end
end

local MODDED = "Zane:gender=male;KATTAJ1:BackFanny=Base.Bag;Hat=Base.Cap"
local PLAIN = "Billy:gender=male;Hat=Base.Cap"

-- 1. 42.20 buggy vanilla, modded preset: fixed reader wins, nothing truncated
FILE = { "VERSION=1", MODDED, PLAIN }
load(vanillaBuggy)
local r = CharacterCreationMain.readSavedOutfitFile()
check("buggy vanilla: modded preset kept whole", r.Zane == "gender=male;KATTAJ1:BackFanny=Base.Bag;Hat=Base.Cap")
check("buggy vanilla: plain preset intact", r.Billy == "gender=male;Hat=Base.Cap")
check("buggy vanilla: verdict", UnbreakerPatches.outfitVerdict() == "using fixed reader")

-- 2. buggy vanilla, no modded slots: identical output, ours used
FILE = { "VERSION=1", PLAIN }
load(vanillaBuggy)
r = CharacterCreationMain.readSavedOutfitFile()
check("buggy vanilla, no colons: intact", r.Billy == "gender=male;Hat=Base.Cap")
check("buggy vanilla, no colons: verdict", UnbreakerPatches.outfitVerdict() == "using fixed reader")

-- 3. a build that fixed it: vanilla's output differs from the known bug, so we step aside
FILE = { "VERSION=1", MODDED, PLAIN }
load(vanillaFixed)
r = CharacterCreationMain.readSavedOutfitFile()
check("fixed vanilla: preset whole", r.Zane == "gender=male;KATTAJ1:BackFanny=Base.Bag;Hat=Base.Cap")
check("fixed vanilla: verdict defers", UnbreakerPatches.outfitVerdict() == "vanilla reader has changed, using vanilla")

-- 4. a build that reshaped the return value: vanilla's table comes back untouched
FILE = { "VERSION=1", PLAIN }
load(vanillaReshaped)
r = CharacterCreationMain.readSavedOutfitFile()
check("reshaped vanilla: vanilla's shape returned", type(r.Billy) == "table" and r.Billy.raw == "gender=male;Hat=Base.Cap")

-- 5. unknown file format: vanilla reader handles it
FILE = { "VERSION=2", "Zane:whatever" }
load(vanillaBuggy)
r = CharacterCreationMain.readSavedOutfitFile()
check("unknown format: verdict", UnbreakerPatches.outfitVerdict() == "unknown file format, using vanilla")
check("unknown format: vanilla result (empty)", next(r) == nil)

-- 6. vanilla reader throws: fixed reader still answers
FILE = { "VERSION=1", PLAIN }
load(function() error("boom") end)
r = CharacterCreationMain.readSavedOutfitFile()
check("vanilla throws: fixed reader used", r.Billy == "gender=male;Hat=Base.Cap")

print(failures == 0 and "ALL PASS" or (failures .. " FAILED"))
os.exit(failures == 0 and 0 or 1)
