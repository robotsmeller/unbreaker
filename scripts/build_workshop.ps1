#Requires -Version 5.1
# Builds the Workshop content folder layout that SteamCMD expects,
# plus the SteamCMD VDF manifest with the full description spliced in
# from assets/workshop-description.txt.
# Run before every Workshop upload.
# Outputs:
#   build/workshop/             - content folder, point contentfolder at this
#   build/workshop_item.txt     - the VDF, point SteamCMD at this

$ErrorActionPreference = "Stop"
$root  = Split-Path -Parent $PSScriptRoot
$mod   = Join-Path $root "mod"
$build = Join-Path $root "build\workshop"
$tpl   = Join-Path $root "workshop_item.template.txt"
$desc  = Join-Path $root "assets\workshop-description.txt"
$out   = Join-Path $root "build\workshop_item.txt"

if (-not (Test-Path $mod)) {
    throw "mod/ folder not found at $mod"
}
if (-not (Test-Path "$mod\preview.png")) {
    throw "mod\preview.png not found. Workshop needs a preview thumbnail."
}

if (Test-Path $build) {
    Remove-Item -Recurse -Force $build
}

$dest = Join-Path $build "mods\Unbreaker"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

# Workshop preview lives at the content folder root, not inside the mod.
Copy-Item "$mod\preview.png" (Join-Path $build "preview.png")

# Everything else copies into mods/Unbreaker/
Get-ChildItem $mod | Where-Object { $_.Name -ne "preview.png" } | ForEach-Object {
    Copy-Item -Recurse $_.FullName $dest
}

Write-Host ""
Write-Host "Workshop content built at:" -ForegroundColor Green
Write-Host "  $build"
Write-Host ""
Write-Host "Layout:"
Get-ChildItem -Recurse $build | ForEach-Object {
    $rel = $_.FullName.Substring($build.Length + 1)
    if ($_.PSIsContainer) { Write-Host "  $rel\" } else { Write-Host "  $rel" }
}

# Generate VDF with full description spliced in.
# Template's "description" line is replaced with the escaped contents
# of assets/workshop-description.txt. Newlines become \n, quotes become \".
if (-not (Test-Path $tpl))  { throw "VDF template not found: $tpl" }
if (-not (Test-Path $desc)) { throw "Description not found: $desc" }

$descRaw = Get-Content $desc -Raw -Encoding UTF8
$descRaw = $descRaw -replace "`r`n", "`n"      # normalize line endings
$descRaw = $descRaw.TrimEnd("`n")              # drop trailing blank lines

# SteamCMD's VDF parser is shallow: \n is passed through literally,
# and \" terminates the string instead of escaping the quote. So
# newlines stay as actual newlines (multi-line strings work), and
# any literal " in the source must be replaced with single or curly
# quotes before it ever hits the VDF.
if ($descRaw -match '"') {
    throw 'Description contains a literal double-quote character. Use single quotes or curly quotes instead. SteamCMD VDF will truncate the description at the first ASCII double-quote.'
}

$descEsc = $descRaw -replace '\\', '\\'         # backslashes still need escaping

$tplLines = Get-Content $tpl
$outLines = $tplLines | ForEach-Object {
    if ($_ -match '^\s*"description"') {
        "`t`"description`"`t`t`"$descEsc`""
    } else {
        $_
    }
}
$outLines | Set-Content -Path $out -Encoding UTF8

Write-Host ""
Write-Host "VDF built at:" -ForegroundColor Green
Write-Host "  $out"
Write-Host "  (description spliced from assets\workshop-description.txt)"
Write-Host ""
Write-Host "Run SteamCMD against the generated file:" -ForegroundColor Yellow
Write-Host "  & C:\steamcmd\steamcmd.exe +login robotsmeller +workshop_build_item `"$out`" +quit"
