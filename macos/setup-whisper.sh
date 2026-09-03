#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
DEPS="$ROOT/macos/deps"
WHISPER="$DEPS/whisper.cpp"

mkdir -p "$DEPS"
if [ ! -d "$WHISPER/.git" ]; then
  git clone --depth 1 https://github.com/ggml-org/whisper.cpp.git "$WHISPER"
fi

cmake -S "$WHISPER" -B "$WHISPER/build" -DWHISPER_BUILD_SERVER=ON
cmake --build "$WHISPER/build" --config Release -j

if [ ! -f "$WHISPER/models/ggml-large-v3-turbo.bin" ]; then
  "$WHISPER/models/download-ggml-model.sh" large-v3-turbo
fi
if [ ! -f "$WHISPER/models/ggml-silero-v6.2.0.bin" ]; then
  "$WHISPER/models/download-vad-model.sh" silero-v6.2.0
fi
