# Workshop Publish Runbook

Steps to publish Unbreaker to the Steam Workshop. Read end-to-end before starting.

## Prerequisites (already done)

- SteamCMD installed at `C:\steamcmd\steamcmd.exe`
- Build script at `scripts/build_workshop.ps1`
- VDF manifest at `workshop_item.txt`
- A Steam account that owns Project Zomboid

## First-time publish

### 1. Build the Workshop content folder

```powershell
.\scripts\build_workshop.ps1
```

This rebuilds `build/workshop/` with the layout SteamCMD expects:

```
build/workshop/
├── preview.png
└── Contents/
    └── mods/
        └── Unbreaker/  (mod.info, poster.png, 42/...)
```

### 2. Verify the VDF manifest

Open `workshop_item.txt` and confirm:

- `appid` is `108600` (Project Zomboid)
- `publishedfileid` is `0` (this signals "create new" on first upload)
- `contentfolder` and `previewfile` are absolute paths that exist
- `visibility` is `2` (private/hidden) for the first upload so you can verify before going public

### 3. Run SteamCMD

```powershell
& C:\steamcmd\steamcmd.exe +login YOUR_STEAM_USERNAME +workshop_build_item C:\xampp\htdocs\unbreaker\workshop_item.txt +quit
```

SteamCMD will prompt for your Steam password and a Steam Guard 2FA code. Type them when prompted.

On success the output ends with something like:

```
Successfully created item. PublishedFileId: 3480731959
```

**Save that numeric ID.** You need it for updates.

### 4. Update the VDF for future use

Edit `workshop_item.txt` and replace `"publishedfileid" "0"` with the numeric ID from step 3. Subsequent uploads use that ID to update the existing item instead of creating a new one.

### 5. Finish setup on the Workshop web page

Open `https://steamcommunity.com/sharedfiles/filedetails/?id=YOUR_ID` and:

- Paste the BBCode from `assets/workshop-description.txt` into the description field
- Add tags: `Build 42`, `Library`, `Bug Fix`, `Modding Tools`
- Add screenshots if you have any
- Confirm the title is `Unbreaker`
- Leave visibility on Hidden until you finish review

### 6. Test the hidden upload

Subscribe to the hidden Workshop item from your own Steam client (you can see it because you uploaded it). Load PZ. Confirm Unbreaker appears in the mod manager and loads cleanly. Watch console.txt for the `[Unbreaker] loaded v1.2.0` line.

### 7. Go public

On the Workshop page, change visibility from Hidden to Public. The item is now live.

### 8. Post-publish

- Pin a comment on the Workshop page (suggested: link to the diagnostic tool, single-player note, bug report format)
- Update the Workshop link in `docs/index.html` (footer) and `README.md` (subscribe link), then commit and push

## Updating an existing item

After first publish:

1. Make changes (add redirects to `data/vanilla_globals.json`, regen, bump version, etc.)
2. Update `changenote` in `workshop_item.txt`
3. Run `.\scripts\build_workshop.ps1`
4. Run the same SteamCMD command from step 3 above

Steam updates the item in place using the saved `publishedfileid`.

## Troubleshooting

**`ERROR! Failed to create workshop item (k_EResultAccessDenied)`**
You don't own PZ on this Steam account, or you've never accepted the Workshop legal agreement. Open Steam, browse any PZ Workshop item, and click subscribe — that triggers the agreement prompt. Then retry.

**`ERROR! Failed to create workshop item (k_EResultLimitExceeded)`**
You've hit Steam's rate limit. Wait an hour and retry.

**`Login Failure: Account Logon Denied`**
Steam Guard challenge. SteamCMD should prompt for the code; if it doesn't, log in via the Steam client first to clear the challenge.

**Item uploads but content is wrong**
Check `build/workshop/` matches the structure shown in step 1. Re-run the build script if anything looks off.

## What gets uploaded

Only the contents of `build/workshop/`. Everything else in the repo (scripts, docs, .git, etc.) is ignored. The `build/` folder is gitignored.
