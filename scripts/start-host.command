#!/bin/zsh
set -eu
cd "${0:A:h}/../host"
exec python3 -m nodelift.host "$@"
