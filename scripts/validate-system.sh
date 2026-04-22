#!/bin/bash
# =============================================================================
# validate-system.sh — OrangeNexus ERP SaaS System Validator
# =============================================================================
# Ejecuta 14 validaciones automáticas del sistema y muestra un resumen.
# Uso: ./scripts/validate-system.sh
# =============================================================================

set -uo pipefail

# ---------------------------------------------------------------------------
# Colores y formato
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0
WARNINGS=0
TOTAL=14
ERRORS_DETAIL=()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
print_header() {
    echo ""
    echo -e "${CYAN}${BOLD}🔍 Validando Sistema ERP SaaS OrangeNexus${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_footer() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    if [ "$FAILED" -eq 0 ]; then
        echo -e "${GREEN}${BOLD}✅ Sistema validado: ${PASSED}/${TOTAL} checks passed${NC}"
        if [ "$WARNINGS" -gt 0 ]; then
            echo -e "${YELLOW}⚠️  ${WARNINGS} advertencia(s) detectada(s)${NC}"
        fi
        echo -e "${GREEN}${BOLD}🚀 Listo para desarrollo${NC}"
    else
        echo -e "${RED}${BOLD}❌ Validación fallida: ${PASSED}/${TOTAL} checks passed, ${FAILED} errores${NC}"
        echo ""
        echo -e "${YELLOW}${BOLD}📋 Resumen de errores:${NC}"
        for err in "${ERRORS_DETAIL[@]}"; do
            echo -e "   ${RED}•${NC} $err"
        done
        echo ""
        echo -e "${YELLOW}📖 Ver: docs/TROUBLESHOOTING.md${NC}"
    fi
    echo ""
}

pass() {
    local step="$1"
    local msg="$2"
    printf "  ${GREEN}[%s/%s]${NC} %-45s ${GREEN}✅ %s${NC}\n" "$step" "$TOTAL" "$3" "$msg"
    ((PASSED++))
}

fail() {
    local step="$1"
    local msg="$2"
    local desc="$3"
    local suggestion="$4"
    local doc_ref="${5:-}"
    printf "  ${RED}[%s/%s]${NC} %-45s ${RED}❌ FAILED${NC}\n" "$step" "$TOTAL" "$desc"
    echo -e "         ${RED}Error: ${msg}${NC}"
    echo -e "         ${YELLOW}💡 Sugerencia: ${suggestion}${NC}"
    if [ -n "$doc_ref" ]; then
        echo -e "         ${CYAN}📖 Ver: docs/TROUBLESHOOTING.md#${doc_ref}${NC}"
    fi
    ERRORS_DETAIL+=("$desc — $msg")
    ((FAILED++))
}

warn() {
    local step="$1"
    local msg="$2"
    printf "  ${YELLOW}[%s/%s]${NC} %-45s ${YELLOW}⚠️  %s${NC}\n" "$step" "$TOTAL" "$3" "$msg"
    ((WARNINGS++))
    ((PASSED++))
}

# ---------------------------------------------------------------------------
# Detectar directorio raíz del proyecto
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Verificar que estamos en el proyecto correcto
if [ ! -f "$ROOT_DIR/docker-compose.yml" ]; then
    echo -e "${RED}Error: No se encontró docker-compose.yml en $ROOT_DIR${NC}"
    echo "Ejecutar desde el directorio raíz del proyecto: ./scripts/validate-system.sh"
    exit 1
fi

cd "$ROOT_DIR"

# Variables de conexión (desde .env o defaults)
DB_USER="${POSTGRES_USER:-orangenexus}"
DB_NAME="${POSTGRES_DB:-orangenexus}"
DB_PASS="${POSTGRES_PASSWORD:-orangenexus}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_CONTAINER="orangenexus-db"
REDIS_CONTAINER="orangenexus-redis"
API_PORT="${API_PORT:-8000}"

# Cargar .env si existe
if [ -f "$ROOT_DIR/.env" ]; then
    set -a
    source "$ROOT_DIR/.env" 2>/dev/null || true
    set +a
    DB_USER="${POSTGRES_USER:-orangenexus}"
    DB_NAME="${POSTGRES_DB:-orangenexus}"
    DB_PASS="${POSTGRES_PASSWORD:-orangenexus}"
    DB_PORT="${POSTGRES_PORT:-5432}"
    API_PORT="${API_PORT:-8000}"
fi

# ---------------------------------------------------------------------------
# Helper: ejecutar psql dentro del contenedor
# ---------------------------------------------------------------------------
db_exec() {
    docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -A -c "$1" 2>/dev/null
}

# ---------------------------------------------------------------------------
# Validaciones
# ---------------------------------------------------------------------------
print_header

# [1/14] Docker instalado
STEP=1
DESC="Verificando Docker..."
if command -v docker &>/dev/null; then
    DOCKER_VER=$(docker --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' | head -1)
    if docker info &>/dev/null; then
        pass "$STEP" "v${DOCKER_VER}" "$DESC"
    else
        fail "$STEP" "Docker daemon no está corriendo" "$DESC" \
            "Ejecutar 'sudo systemctl start docker' o iniciar Docker Desktop" \
            "docker-y-postgresql"
    fi
else
    fail "$STEP" "Docker no instalado" "$DESC" \
        "Instalar Docker: https://docs.docker.com/engine/install/" \
        "docker-y-postgresql"
fi

# [2/14] Docker Compose
STEP=2
DESC="Verificando Docker Compose..."
if docker compose version &>/dev/null; then
    COMPOSE_VER=$(docker compose version --short 2>/dev/null)
    pass "$STEP" "v${COMPOSE_VER}" "$DESC"
elif command -v docker-compose &>/dev/null; then
    COMPOSE_VER=$(docker-compose --version | grep -oP '\d+\.\d+\.\d+' | head -1)
    warn "$STEP" "v1 (${COMPOSE_VER}) — se recomienda v2" "$DESC"
else
    fail "$STEP" "Docker Compose no instalado" "$DESC" \
        "Instalar Docker Compose: https://docs.docker.com/compose/install/" \
        "docker-y-postgresql"
fi

# [3/14] PostgreSQL container
STEP=3
DESC="Verificando PostgreSQL container..."
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${DB_CONTAINER}$"; then
    DB_STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$DB_CONTAINER" 2>/dev/null || echo "running")
    if [ "$DB_STATUS" = "healthy" ]; then
        pass "$STEP" "Running (healthy)" "$DESC"
    elif [ "$DB_STATUS" = "starting" ]; then
        warn "$STEP" "Running (starting) — esperando healthcheck" "$DESC"
    else
        pass "$STEP" "Running" "$DESC"
    fi
else
    fail "$STEP" "Container '${DB_CONTAINER}' no está corriendo" "$DESC" \
        "Ejecutar 'docker compose up -d db'" \
        "postgresql-no-inicia"
fi

# [4/14] Redis container
STEP=4
DESC="Verificando Redis container..."
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${REDIS_CONTAINER}$"; then
    REDIS_PING=$(docker exec "$REDIS_CONTAINER" redis-cli ping 2>/dev/null || echo "")
    if [ "$REDIS_PING" = "PONG" ]; then
        pass "$STEP" "Running (PONG)" "$DESC"
    else
        warn "$STEP" "Running (sin respuesta a PING)" "$DESC"
    fi
else
    fail "$STEP" "Container '${REDIS_CONTAINER}' no está corriendo" "$DESC" \
        "Ejecutar 'docker compose up -d redis'" \
        "redis-no-inicia"
fi

# [5/14] PostgreSQL acepta conexiones
STEP=5
DESC="Verificando conexión PostgreSQL..."
if docker exec "$DB_CONTAINER" pg_isready -U "$DB_USER" -d "$DB_NAME" &>/dev/null; then
    pass "$STEP" "Connected" "$DESC"
else
    fail "$STEP" "Connection refused" "$DESC" \
        "Ejecutar 'docker compose up -d db' y esperar 10 segundos" \
        "postgresql-connection-refused"
fi

# [6/14] Database existe
STEP=6
DESC="Verificando database '${DB_NAME}'..."
DB_EXISTS=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -lqt 2>/dev/null | grep -cw "$DB_NAME" || echo "0")
if [ "$DB_EXISTS" -gt 0 ]; then
    pass "$STEP" "Exists" "$DESC"
else
    fail "$STEP" "Database '${DB_NAME}' no existe" "$DESC" \
        "Recrear contenedor: 'docker compose down -v && docker compose up -d db'" \
        "postgresql-no-inicia"
fi

# [7/14] Extensiones PostgreSQL
STEP=7
DESC="Verificando extensiones PostgreSQL..."
EXT_COUNT=$(db_exec "SELECT count(*) FROM pg_extension WHERE extname IN ('uuid-ossp','pgcrypto');" 2>/dev/null || echo "0")
EXT_COUNT=$(echo "$EXT_COUNT" | tr -d '[:space:]')
if [ "$EXT_COUNT" = "2" ]; then
    pass "$STEP" "uuid-ossp + pgcrypto" "$DESC"
elif [ "$EXT_COUNT" = "1" ]; then
    warn "$STEP" "Solo 1 de 2 extensiones instaladas" "$DESC"
else
    fail "$STEP" "Extensiones no instaladas (${EXT_COUNT}/2)" "$DESC" \
        "Ejecutar: docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c \"CREATE EXTENSION IF NOT EXISTS \\\"uuid-ossp\\\"; CREATE EXTENSION IF NOT EXISTS pgcrypto;\"" \
        "verificar-que-rls-está-activo"
fi

# [8/14] Migraciones aplicadas
STEP=8
DESC="Verificando migraciones..."
ALEMBIC_VER=$(db_exec "SELECT version_num FROM alembic_version LIMIT 1;" 2>/dev/null || echo "")
ALEMBIC_VER=$(echo "$ALEMBIC_VER" | tr -d '[:space:]')
if [ -n "$ALEMBIC_VER" ]; then
    # Contar migraciones
    MIGRATION_COUNT=$(ls "$ROOT_DIR/packages/db-migrations/alembic/versions/"*.py 2>/dev/null | wc -l)
    if [ "$ALEMBIC_VER" = "006_indexes_and_rls" ]; then
        pass "$STEP" "Applied (${MIGRATION_COUNT} migrations, head)" "$DESC"
    else
        warn "$STEP" "En revisión ${ALEMBIC_VER} (no es head)" "$DESC"
    fi
else
    fail "$STEP" "No hay migraciones aplicadas (tabla alembic_version vacía o no existe)" "$DESC" \
        "Ejecutar: cd packages/db-migrations && alembic upgrade head" \
        "alembic-no-encuentra-db"
fi

# [9/14] Tablas creadas
STEP=9
DESC="Verificando tablas..."
TABLE_COUNT=$(db_exec "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';" 2>/dev/null || echo "0")
TABLE_COUNT=$(echo "$TABLE_COUNT" | tr -d '[:space:]')
if [ "$TABLE_COUNT" -ge 21 ]; then
    pass "$STEP" "${TABLE_COUNT} tables found" "$DESC"
elif [ "$TABLE_COUNT" -gt 0 ]; then
    warn "$STEP" "${TABLE_COUNT} tablas (esperado: 21+)" "$DESC"
else
    fail "$STEP" "0 tablas encontradas" "$DESC" \
        "Ejecutar migraciones: cd packages/db-migrations && alembic upgrade head" \
        "migrations-ya-aplicadas"
fi

# [10/14] RLS habilitado
STEP=10
DESC="Verificando RLS..."
RLS_COUNT=$(db_exec "SELECT count(*) FROM pg_tables WHERE schemaname='public' AND rowsecurity=true;" 2>/dev/null || echo "0")
RLS_COUNT=$(echo "$RLS_COUNT" | tr -d '[:space:]')
if [ "$RLS_COUNT" -ge 15 ]; then
    pass "$STEP" "Enabled on ${RLS_COUNT} tables" "$DESC"
elif [ "$RLS_COUNT" -gt 0 ]; then
    warn "$STEP" "RLS en ${RLS_COUNT} tablas (esperado: 15+)" "$DESC"
else
    fail "$STEP" "RLS no habilitado en ninguna tabla" "$DESC" \
        "Verificar migración 006: cd packages/db-migrations && alembic upgrade head" \
        "verificar-que-rls-está-activo"
fi

# [11/14] Seed data
STEP=11
DESC="Verificando seed data..."
TENANT_COUNT=$(db_exec "SELECT count(*) FROM tenants;" 2>/dev/null || echo "0")
TENANT_COUNT=$(echo "$TENANT_COUNT" | tr -d '[:space:]')
if [ "$TENANT_COUNT" -ge 1 ]; then
    BRANCH_COUNT=$(db_exec "SELECT count(*) FROM branches;" 2>/dev/null || echo "0")
    BRANCH_COUNT=$(echo "$BRANCH_COUNT" | tr -d '[:space:]')
    ROLE_COUNT=$(db_exec "SELECT count(*) FROM roles;" 2>/dev/null || echo "0")
    ROLE_COUNT=$(echo "$ROLE_COUNT" | tr -d '[:space:]')
    pass "$STEP" "Loaded (${TENANT_COUNT} tenant, ${BRANCH_COUNT} branch, ${ROLE_COUNT} role)" "$DESC"
else
    fail "$STEP" "No hay datos en la tabla tenants" "$DESC" \
        "Ejecutar: cd packages/db-migrations && python seeds/initial_seed.py" \
        "alembic-no-encuentra-db"
fi

# [12/14] Backend health
STEP=12
DESC="Verificando backend health..."
HEALTH_RESPONSE=$(curl -s --connect-timeout 5 --max-time 10 "http://localhost:${API_PORT}/health" 2>/dev/null || echo "")
if echo "$HEALTH_RESPONSE" | grep -q '"status".*"ok"'; then
    API_VER=$(echo "$HEALTH_RESPONSE" | grep -oP '"version"\s*:\s*"\K[^"]+' || echo "unknown")
    pass "$STEP" "Healthy (v${API_VER})" "$DESC"
else
    fail "$STEP" "Backend no responde en localhost:${API_PORT}" "$DESC" \
        "Iniciar backend: cd apps/api && uvicorn app.main:app --reload --port ${API_PORT}" \
        "database-connection-failed"
fi

# [13/14] Frontend build
STEP=13
DESC="Verificando frontend..."
if [ -d "$ROOT_DIR/apps/web" ]; then
    if [ -d "$ROOT_DIR/apps/web/.next" ]; then
        pass "$STEP" "Build exists (.next/)" "$DESC"
    elif [ -f "$ROOT_DIR/apps/web/package.json" ]; then
        if [ -d "$ROOT_DIR/apps/web/node_modules" ]; then
            warn "$STEP" "node_modules OK, pero no hay build (.next/)" "$DESC"
        else
            warn "$STEP" "Falta instalar deps: cd apps/web && npm install" "$DESC"
        fi
    else
        fail "$STEP" "package.json no encontrado en apps/web" "$DESC" \
            "Verificar la estructura del proyecto" \
            "build-errors"
    fi
else
    fail "$STEP" "Directorio apps/web no existe" "$DESC" \
        "Verificar la estructura del proyecto" \
        "build-errors"
fi

# [14/14] JWT auth test
STEP=14
DESC="Verificando JWT auth..."
if echo "$HEALTH_RESPONSE" | grep -q '"status".*"ok"'; then
    # Intentar login con credenciales de prueba
    LOGIN_RESPONSE=$(curl -s --connect-timeout 5 --max-time 10 \
        -X POST "http://localhost:${API_PORT}/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"email":"admin@orangenexus.com","password":"Admin123!"}' 2>/dev/null || echo "")

    if echo "$LOGIN_RESPONSE" | grep -q '"access_token"'; then
        pass "$STEP" "Working (login OK)" "$DESC"
    elif echo "$LOGIN_RESPONSE" | grep -q '"detail"'; then
        DETAIL=$(echo "$LOGIN_RESPONSE" | grep -oP '"detail"\s*:\s*"\K[^"]+' || echo "unknown")
        if [ "$DETAIL" = "Invalid credentials" ]; then
            warn "$STEP" "Endpoint responde pero credenciales de test inválidas" "$DESC"
        else
            warn "$STEP" "Endpoint responde: ${DETAIL}" "$DESC"
        fi
    else
        warn "$STEP" "No se pudo verificar (backend puede no tener usuario de test)" "$DESC"
    fi
else
    fail "$STEP" "No se puede verificar JWT (backend no responde)" "$DESC" \
        "Iniciar el backend primero" \
        "token-inválido"
fi

# ---------------------------------------------------------------------------
# Resumen
# ---------------------------------------------------------------------------
print_footer

# Exit code
if [ "$FAILED" -gt 0 ]; then
    exit 1
else
    exit 0
fi
