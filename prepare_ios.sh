#!/bin/zsh
# prepare_ios.sh - Run instead of `briefcase create iOS` before building in Xcode
set -e

echo "Removing previous iOS build..."
rm -rf build/gobattlekit/ios/xcode

echo "Creating iOS project..."
briefcase create iOS --no-input

echo "Adding xcprivacy files for SSL frameworks..."
# Discover the lib-dynload dirs instead of hardcoding the Python version —
# a briefcase/python bump otherwise silently skips the copies and the
# upload fails Apple's privacy-manifest review (ITMS-91061).
dynload_dirs=(build/gobattlekit/ios/xcode/Support/Python.xcframework/*/lib*/python*/lib-dynload(N))
if [[ ${#dynload_dirs[@]} -eq 0 ]]; then
    echo "ERROR: no lib-dynload directories found under the Support package." >&2
    echo "The briefcase template layout may have changed; fix the glob above." >&2
    exit 1
fi
for d in "${dynload_dirs[@]}"; do
    cp resources/PrivacyInfo.xcprivacy "${d}/_hashlib.xcprivacy"
    cp resources/PrivacyInfo.xcprivacy "${d}/_ssl.xcprivacy"
    echo "  ${d}"
done

# Assert the manifests actually landed so a template change can't silently
# ship a build with no privacy manifest (which fails ITMS-91061 at upload).
manifest_count=$(find build/gobattlekit/ios/xcode -name '*.xcprivacy' | wc -l | tr -d ' ')
if [[ "${manifest_count}" -eq 0 ]]; then
    echo "ERROR: no .xcprivacy files present after copy; the build would fail" >&2
    echo "Apple's privacy-manifest review (ITMS-91061). Aborting." >&2
    exit 1
fi
echo "Privacy manifests present: ${manifest_count}"

echo "Done! Next steps:"
echo "  1. Open build/gobattlekit/ios/xcode/GoBattleKit.xcodeproj in Xcode"
echo "  2. Set signing team to Michael Lerner (team MF55GHNQC2, the paid Apple Developer Program account)"
echo "  3. Product → Clean Build Folder (Cmd+Shift+K)"
echo "  4. Product → Archive → Distribute → App Store Connect → Upload"
