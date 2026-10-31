#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
test "$(git -C "$ROOT/.deps/llama.cpp" rev-parse HEAD)" = "$(cat "$ROOT/native/llama.lock")"
CMAKE=${NODELIFT_CMAKE:-cmake}
if ! command -v "$CMAKE" >/dev/null 2>&1; then CMAKE="$HOME/Library/Android/sdk/cmake/3.22.1/bin/cmake"; fi
SDK=${1:-iphoneos}
case "$SDK" in iphoneos|iphonesimulator) ;; *) echo 'Use iphoneos or iphonesimulator'; exit 1;; esac
"$CMAKE" -S "$ROOT/native" -B "$ROOT/native/build/$SDK" \
  -DCMAKE_SYSTEM_NAME=iOS -DCMAKE_OSX_SYSROOT="$SDK" -DCMAKE_OSX_ARCHITECTURES=arm64 \
  -DCMAKE_OSX_DEPLOYMENT_TARGET=17.0 -DCMAKE_BUILD_TYPE=Release \
  -DGGML_METAL=ON -DGGML_METAL_EMBED_LIBRARY=ON -DGGML_OPENMP=OFF \
  -DGGML_BLAS=OFF -DGGML_LLAMAFILE=OFF -DGGML_NATIVE=OFF
"$CMAKE" --build "$ROOT/native/build/$SDK" --config Release -j 8
