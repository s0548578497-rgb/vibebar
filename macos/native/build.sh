#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd -P)"
swiftc "$ROOT/macos/native/ClassicRssiReader.swift" -framework IOBluetooth \
  -o "$ROOT/macos/native/ClassicRssiReader"
