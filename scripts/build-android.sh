#!/bin/sh
set -eu
python3 "$(dirname "$0")/release-history.py" --check-build
cd "$(dirname "$0")/../apps/android"
if [ -z "${JAVA_HOME:-}" ] && [ -x /usr/libexec/java_home ]; then
    JAVA_HOME=$(/usr/libexec/java_home -v 21)
    export JAVA_HOME
fi
ANDROID_HOME=${ANDROID_HOME:-"$HOME/Library/Android/sdk"}
export ANDROID_HOME
./gradlew --no-daemon assembleDebug
