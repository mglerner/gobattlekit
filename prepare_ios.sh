#!/bin/zsh
# prepare_ios.sh - Run instead of `briefcase create iOS` before building in Xcode

echo "Removing previous iOS build..."
rm -rf build/gobattlekit/ios/xcode

echo "Creating iOS project..."
briefcase create iOS --no-input

echo "Adding xcprivacy files for SSL frameworks..."
cp resources/PrivacyInfo.xcprivacy "build/gobattlekit/ios/xcode/Support/Python.xcframework/ios-arm64/lib-arm64/python3.13/lib-dynload/_hashlib.xcprivacy"
cp resources/PrivacyInfo.xcprivacy "build/gobattlekit/ios/xcode/Support/Python.xcframework/ios-arm64/lib-arm64/python3.13/lib-dynload/_ssl.xcprivacy"
cp resources/PrivacyInfo.xcprivacy "build/gobattlekit/ios/xcode/Support/Python.xcframework/ios-arm64_x86_64-simulator/lib-arm64/python3.13/lib-dynload/_hashlib.xcprivacy"
cp resources/PrivacyInfo.xcprivacy "build/gobattlekit/ios/xcode/Support/Python.xcframework/ios-arm64_x86_64-simulator/lib-arm64/python3.13/lib-dynload/_ssl.xcprivacy"
cp resources/PrivacyInfo.xcprivacy "build/gobattlekit/ios/xcode/Support/Python.xcframework/ios-arm64_x86_64-simulator/lib-x86_64/python3.13/lib-dynload/_hashlib.xcprivacy"
cp resources/PrivacyInfo.xcprivacy "build/gobattlekit/ios/xcode/Support/Python.xcframework/ios-arm64_x86_64-simulator/lib-x86_64/python3.13/lib-dynload/_ssl.xcprivacy"

echo "Done! Next steps:"
echo "  1. Open build/gobattlekit/ios/xcode/GoBattleKit.xcodeproj in Xcode"
echo "  2. Set signing team to Michael Lerner (Personal Team)"
echo "  3. Product → Clean Build Folder (Cmd+Shift+K)"
echo "  4. Product → Archive → Distribute → App Store Connect → Upload"
