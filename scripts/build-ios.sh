#!/bin/sh
set -eu
"$(dirname "$0")/build-native-ios.sh" iphoneos
cd "$(dirname "$0")/../apps/ios"
xcodegen generate --spec project.yml
xcodebuild -project NodeLift.xcodeproj -scheme NodeLift -configuration Release \
    -sdk iphoneos -destination 'generic/platform=iOS' -derivedDataPath build/device \
    CODE_SIGNING_ALLOWED=NO build
