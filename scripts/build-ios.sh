#!/bin/sh
set -eu
cd "$(dirname "$0")/../apps/ios"
xcodebuild -project NodeLift.xcodeproj -scheme NodeLift -configuration Release \
    -sdk iphoneos -destination 'generic/platform=iOS' -derivedDataPath build/device \
    CODE_SIGNING_ALLOWED=NO build
