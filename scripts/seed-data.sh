#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "[seed-data] Cargando datos iniciales..."
python "$ROOT_DIR/packages/db-migrations/seeds/initial_seed.py"

echo "[seed-data] Seed completado"
