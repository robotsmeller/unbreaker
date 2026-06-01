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

# Generate VDF by copying the template verbatim.
# IMPORTANT: the VDF intentionally has NO "description" field. The Workshop
# description is managed by hand in the Steam app and must NEVER be pushed.
# A pushed description overwrites manual edits on the Workshop page. Omitting
# the field entirely makes SteamCMD leave the live description untouched.
if (-not (Test-Path $tpl)) { throw "VDF template not found: $tpl" }

if ((Get-Content $tpl -Raw) -match '"description"') {
    throw 'workshop_item.template.txt contains a "description" field. Remove it. Pushing a description overwrites manual edits in the Steam app.'
}

Copy-Item $tpl $out -Force

Write-Host ""
Write-Host "VDF built at:" -ForegroundColor Green
Write-Host "  $out"
Write-Host "  (no description field; Steam-app description is preserved)"
Write-Host ""
Write-Host "Run SteamCMD against the generated file:" -ForegroundColor Yellow
Write-Host "  & C:\steamcmd\steamcmd.exe +login robotsmeller +workshop_build_item `"$out`" +quit"
