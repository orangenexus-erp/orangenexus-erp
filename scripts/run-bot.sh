#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
python "$ROOT_DIR/services/fx-rate-bot/main.py"
