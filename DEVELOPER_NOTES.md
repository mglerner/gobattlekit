# GoBattleKit Developer Notes

## iOS Build Process

1. `briefcase create iOS`
2. Open `build/gobattlekit/ios/xcode/GoBattleKit.xcodeproj` in Xcode
3. Set signing team to Michael Lerner (Personal Team) — resets on each `briefcase create`
4. **Add PrivacyInfo.xcprivacy** (required by Apple, resets on each `briefcase create`):
   - Right-click grey GoBattleKit folder in project navigator
   - New File → search "Privacy" → select "App Privacy"
   - Name it `PrivacyInfo`, add to GoBattleKit target
   - Contents: see `resources/PrivacyInfo.xcprivacy` in this repo
5. Product → Clean Build Folder (Cmd+Shift+K)
6. Product → Archive → Distribute → App Store Connect → Upload

## Android Build Process
```bash
briefcase update android
briefcase build android
briefcase run android -d "@Medium_Phone_API_36.1"
```

## Version Bumping
- Update `version` in `pyproject.toml`
- Apple requires a new version or build number for each upload

## Known Issues
- iOS navigation bar cannot be hidden via Python/Rubicon — requires native Xcode project modification
- Android white border around container in light mode — cosmetic, accepted
- `Window content exceeds available space` warning on iOS — cosmetic, harmless

## PvPoke Data URLs
```python
BASE_URL = "https://raw.githubusercontent.com/pvpoke/pvpoke/refs/heads/master/src/data"
```
Note: The old URL format (`/master/` without `refs/heads/`) stopped working in March 2026.
