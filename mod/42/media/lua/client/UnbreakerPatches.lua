-- UnbreakerPatches.lua
--
-- Fixes for bugs in VANILLA lua, as opposed to UnbreakerData.lua which redirects
-- broken require() paths to vanilla globals.
--
-- The bar for adding something here is deliberately high. It must be a bug in
-- the base game, not in a mod, so there is no third-party version to track and
-- the patch stays correct until The Indie Stone fixes it upstream. Mod-specific
-- patches do NOT belong here; they live at github.com/robotsmeller/pz-shims,
-- because they go stale the moment their author ships a fix and Unbreaker has
-- no way to know when that happened.
--
-- Every patch guards on the bug still being present where that is detectable,
-- and reports what it did.

local applied = {}

--------------------------------------------------------------------------------
-- saved_outfits.txt truncates at the first colon inside a preset payload
--------------------------------------------------------------------------------
-- Confirmed on B42.20. CharacterCreationMain.readSavedOutfitFile does:
--
--     local s = luautils.split(line, ":")
--     retVal[s[1]] = s[2]
--
-- The file format is  PresetName:key=value;key=value;...  so taking field 2
-- silently discards everything from the SECOND colon onward. Vanilla never hit
-- this because no vanilla body location name contains a colon.
--
-- B42's own registration convention does: ItemBodyLocation.register("KATTAJ1:BackFanny").
-- So the moment a preset contains a modded clothing slot, the payload is cut at
-- that slot and the remainder is lost. The truncated value is then written back
-- on the next save, so each round trip destroys more of the preset. Observed
-- live: presets ending mid-payload at ";KATTAJ1" and ";ALICE", losing the modded
-- slots AND every vanilla slot that came after them.
--
-- The writer is correct and is left alone. Only the read side needs fixing: split
-- on the FIRST colon and keep the entire remainder as the value.

-- Vanilla's OUTFITS_VERSION is a FILE-LOCAL (CharacterCreationMain.lua:453), so it
-- is not reachable from here and reads as nil. The first version of this patch
-- compared against it anyway, so `version == nil` was false for every line, the
-- reader returned an empty table, and the preset dropdown went blank. Caught by
-- loading the game, which no amount of reading the code had caught.
--
-- Mirrored here by value. If vanilla ever bumps the format, this patch does not
-- guess: it hands the file back to the original implementation it replaced.
local KNOWN_OUTFITS_VERSION = 1

local function patchSavedOutfitReader()
    if CharacterCreationMain == nil or CharacterCreationMain.readSavedOutfitFile == nil then
        return false, "CharacterCreationMain.readSavedOutfitFile not found"
    end

    local originalReader = CharacterCreationMain.readSavedOutfitFile

    CharacterCreationMain.readSavedOutfitFile = function()
        local retVal = {}
        local saveFile = getFileReader(CharacterCreationMain.savefile, true)
        if saveFile == nil then
            return retVal
        end

        local version = 0
        local line = saveFile:readLine()
        while line ~= nil do
            if luautils.stringStarts(line, "VERSION=") then
                version = tonumber(string.split(line, "=")[2])
                if version ~= KNOWN_OUTFITS_VERSION then
                    -- Unknown format. Do not touch it.
                    saveFile:close()
                    return originalReader()
                end
            elseif version == KNOWN_OUTFITS_VERSION then
                -- First colon only. The value keeps every colon it contains,
                -- which is what modded body location names depend on.
                local sep = string.find(line, ":", 1, true)
                if sep ~= nil and sep > 1 then
                    retVal[string.sub(line, 1, sep - 1)] = string.sub(line, sep + 1)
                end
            end
            line = saveFile:readLine()
        end
        saveFile:close()

        return retVal
    end

    return true, "saved_outfits.txt reader no longer truncates at modded body locations"
end

--------------------------------------------------------------------------------

local function applyAll()
    local patches = {
        { name = "saved-outfit-colon-truncation", fn = patchSavedOutfitReader },
    }

    local n = 0
    for _, patch in ipairs(patches) do
        -- pcall returns (didNotThrow, patchSucceeded, detail)
        local ran, succeeded, detail = pcall(patch.fn)
        local ok = (ran == true and succeeded == true)
        if ok then
            n = n + 1
        end
        table.insert(applied, {
            name = patch.name,
            ok = ok,
            detail = tostring(detail or (ran and "returned false" or "threw")),
        })
        if not ok then
            print("[Unbreaker] patch SKIPPED: " .. patch.name .. " — " .. tostring(detail))
        end
    end

    print("[Unbreaker] vanilla patches applied: " .. tostring(n) .. "/" .. tostring(#patches))
end

Events.OnGameBoot.Add(applyAll)

_G.UnbreakerPatches = {
    list = function() return applied end,
}
