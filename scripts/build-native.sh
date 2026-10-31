#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PIN=$(cat "$ROOT/native/llama.lock")
if [ ! -d "$ROOT/.deps/llama.cpp/.git" ]; then
  mkdir -p "$ROOT/.deps"
  git clone https://github.com/ggml-org/llama.cpp.git "$ROOT/.deps/llama.cpp"
  git -C "$ROOT/.deps/llama.cpp" checkout --detach "$PIN"
fi
test "$(git -C "$ROOT/.deps/llama.cpp" rev-parse HEAD)" = "$PIN" || { echo 'llama.cpp pin differs; use the locked revision.'; exit 1; }
CMAKE=${NODELIFT_CMAKE:-cmake}
if ! command -v "$CMAKE" >/dev/null 2>&1; then CMAKE="$HOME/Library/Android/sdk/cmake/3.22.1/bin/cmake"; fi
"$CMAKE" -S "$ROOT/native" -B "$ROOT/native/build/host" -DCMAKE_BUILD_TYPE=Release -DGGML_METAL=ON -DGGML_METAL_EMBED_LIBRARY=ON
"$CMAKE" --build "$ROOT/native/build/host" --config Release -j 8
