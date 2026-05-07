#Requires -Version 5.1
# Builds the Workshop content folder layout that SteamCMD expects.
# Run before every Workshop upload. Output: build/workshop/

$ErrorActionPreference = "Stop"
$root  = Split-Path -Parent $PSScriptRoot
$mod   = Join-Path $root "mod"
$build = Join-Path $root "build\workshop"

if (-not (Test-Path $mod)) {
    throw "mod/ folder not found at $mod"
}
if (-not (Test-Path "$mod\preview.png")) {
    throw "mod\preview.png not found. Workshop needs a preview thumbnail."
}

if (Test-Path $build) {
    Remove-Item -Recurse -Force $build
}

$dest = Join-Path $build "Contents\mods\Unbreaker"
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
