#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

export ALEMBIC_CONFIG="$ROOT_DIR/packages/db-migrations/alembic.ini"

echo "[init-db] Ejecutando migrations..."
cd "$ROOT_DIR/packages/db-migrations"
alembic upgrade head

echo "[init-db] Base de datos inicializada"
