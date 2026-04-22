#!/bin/bash
# =============================================================================
# quick-start.sh — OrangeNexus ERP SaaS Quick Start
# =============================================================================
# Ejecuta todo el setup automáticamente desde cero.
# Uso: ./scripts/quick-start.sh
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
NC='\033[0m'

STEP_NUM=0
TOTAL_STEPS=10

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
step() {
    ((STEP_NUM++))
    echo ""
    echo -e "${CYAN}${BOLD}[${STEP_NUM}/${TOTAL_STEPS}] $1${NC}"
    echo -e "${CYAN}$(printf '%.0s─' {1..55})${NC}"
}

success() {
    echo -e "  ${GREEN}✅ $1${NC}"
}

error() {
    echo -e "  ${RED}❌ $1${NC}"
}

info() {
    echo -e "  ${YELLOW}ℹ️  $1${NC}"
}

abort() {
    echo ""
    echo -e "${RED}${BOLD}❌ Setup abortado: $1${NC}"
    echo -e "${YELLOW}📖 Ver: docs/TROUBLESHOOTING.md${NC}"
    exit 1
}

wait_for_container() {
    local container="$1"
    local max_wait="${2:-60}"
    local elapsed=0
    while [ $elapsed -lt $max_wait ]; do
        if docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null | grep -q "healthy"; then
            return 0
        fi
        sleep 2
        ((elapsed+=2))
        printf "."
    done
    echo ""
    return 1
}

# ---------------------------------------------------------------------------
# Detectar directorio raíz
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

echo ""
echo -e "${CYAN}${BOLD}🍊 OrangeNexus ERP SaaS — Quick Start${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  Directorio: ${ROOT_DIR}"
echo ""

# ==========================================================================
# [1/10] Verificar dependencias
# ==========================================================================
step "Verificando dependencias del sistema"

# Docker
if ! command -v docker &>/dev/null; then
    abort "Docker no está instalado. Instalar desde https://docs.docker.com/engine/install/"
fi
if ! docker info &>/dev/null; then
    abort "Docker daemon no está corriendo. Iniciar Docker y reintentar."
fi
DOCKER_VER=$(docker --version | grep -oP '\d+\.\d+\.\d+' | head -1)
success "Docker v${DOCKER_VER}"

# Docker Compose
if docker compose version &>/dev/null; then
    COMPOSE_VER=$(docker compose version --short 2>/dev/null)
    success "Docker Compose v${COMPOSE_VER}"
elif command -v docker-compose &>/dev/null; then
    info "Docker Compose v1 detectado — se recomienda v2"
else
    abort "Docker Compose no instalado"
fi

# Python
if command -v python3 &>/dev/null; then
    PY_VER=$(python3 --version | grep -oP '\d+\.\d+\.\d+')
    success "Python v${PY_VER}"
else
    abort "Python 3 no está instalado. Instalar Python 3.11+"
fi

# pip
if command -v pip3 &>/dev/null || python3 -m pip --version &>/dev/null 2>&1; then
    success "pip disponible"
else
    info "pip no detectado — intentando con 'python3 -m pip'"
fi

# Node.js (opcional para frontend)
if command -v node &>/dev/null; then
    NODE_VER=$(node --version)
    success "Node.js ${NODE_VER}"
else
    info "Node.js no instalado — frontend no se podrá compilar"
fi

# npm/pnpm
if command -v pnpm &>/dev/null; then
    success "pnpm $(pnpm --version)"
elif command -v npm &>/dev/null; then
    success "npm $(npm --version)"
else
    info "npm/pnpm no detectado"
fi

# ==========================================================================
# [2/10] Copiar archivos de configuración
# ==========================================================================
step "Configurando variables de entorno"

if [ ! -f "$ROOT_DIR/.env" ]; then
    cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
    success "Copiado .env.example → .env"
else
    info ".env ya existe (no se sobrescribe)"
fi

if [ ! -f "$ROOT_DIR/apps/api/.env" ]; then
    cp "$ROOT_DIR/apps/api/.env.example" "$ROOT_DIR/apps/api/.env"
    success "Copiado apps/api/.env.example → apps/api/.env"
else
    info "apps/api/.env ya existe"
fi

if [ ! -f "$ROOT_DIR/apps/web/.env.local" ]; then
    cp "$ROOT_DIR/apps/web/.env.local.example" "$ROOT_DIR/apps/web/.env.local"
    success "Copiado apps/web/.env.local.example → apps/web/.env.local"
else
    info "apps/web/.env.local ya existe"
fi

# Cargar variables
set -a
source "$ROOT_DIR/.env" 2>/dev/null || true
set +a

DB_USER="${POSTGRES_USER:-orangenexus}"
DB_NAME="${POSTGRES_DB:-orangenexus}"
DB_CONTAINER="orangenexus-db"
REDIS_CONTAINER="orangenexus-redis"

# ==========================================================================
# [3/10] Levantar Docker Compose
# ==========================================================================
step "Levantando infraestructura (PostgreSQL + Redis)"

docker compose up -d db redis 2>&1 | while IFS= read -r line; do
    echo "  $line"
done

success "Contenedores iniciados"

# ==========================================================================
# [4/10] Esperar a PostgreSQL
# ==========================================================================
step "Esperando a que PostgreSQL esté listo"

printf "  Esperando"
if wait_for_container "$DB_CONTAINER" 60; then
    echo ""
    success "PostgreSQL healthy"
else
    echo ""
    # Intentar una segunda vez con pg_isready
    if docker exec "$DB_CONTAINER" pg_isready -U "$DB_USER" -d "$DB_NAME" &>/dev/null; then
        success "PostgreSQL acepta conexiones"
    else
        error "PostgreSQL no respondió en 60 segundos"
        info "Revisando logs..."
        docker compose logs --tail=10 db
        abort "PostgreSQL no está listo. Ver logs arriba."
    fi
fi

# Verificar Redis también
if docker exec "$REDIS_CONTAINER" redis-cli ping &>/dev/null; then
    success "Redis respondiendo (PONG)"
else
    info "Redis aún no responde — puede necesitar más tiempo"
fi

# ==========================================================================
# [5/10] Ejecutar migraciones
# ==========================================================================
step "Ejecutando migraciones de base de datos"

# Instalar dependencias de migraciones
pip3 install -q alembic sqlalchemy psycopg2-binary 2>/dev/null || \
    python3 -m pip install -q alembic sqlalchemy psycopg2-binary 2>/dev/null

cd "$ROOT_DIR/packages/db-migrations"

# Verificar si ya están aplicadas
CURRENT=$(alembic current 2>/dev/null | grep -o '006_indexes_and_rls' || echo "")
if [ "$CURRENT" = "006_indexes_and_rls" ]; then
    info "Migraciones ya aplicadas (head: 006_indexes_and_rls)"
else
    alembic upgrade head 2>&1 | while IFS= read -r line; do
        echo "  $line"
    done
    if [ $? -eq 0 ]; then
        success "Migraciones aplicadas correctamente"
    else
        abort "Error al aplicar migraciones"
    fi
fi

cd "$ROOT_DIR"

# ==========================================================================
# [6/10] Cargar seed data
# ==========================================================================
step "Cargando datos iniciales (seed)"

# Verificar si ya hay datos
TENANT_COUNT=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -A -c "SELECT count(*) FROM tenants;" 2>/dev/null || echo "0")
TENANT_COUNT=$(echo "$TENANT_COUNT" | tr -d '[:space:]')

if [ "$TENANT_COUNT" -ge 1 ]; then
    info "Seed data ya existe (${TENANT_COUNT} tenant(s))"
else
    cd "$ROOT_DIR/packages/db-migrations"
    python3 seeds/initial_seed.py 2>&1 | while IFS= read -r line; do
        echo "  $line"
    done
    success "Seed data cargado"
    cd "$ROOT_DIR"
fi

# ==========================================================================
# [7/10] Instalar dependencias backend
# ==========================================================================
step "Instalando dependencias del backend (FastAPI)"

cd "$ROOT_DIR/apps/api"
pip3 install -q -r requirements.txt 2>/dev/null || \
    python3 -m pip install -q -r requirements.txt 2>/dev/null

if python3 -c "import fastapi; import sqlalchemy; import jwt" 2>/dev/null; then
    success "Dependencias del backend instaladas"
else
    error "Algunas dependencias no se instalaron correctamente"
    info "Ejecutar manualmente: cd apps/api && pip install -r requirements.txt"
fi

cd "$ROOT_DIR"

# ==========================================================================
# [8/10] Instalar dependencias frontend
# ==========================================================================
step "Instalando dependencias del frontend (Next.js)"

cd "$ROOT_DIR/apps/web"
if command -v node &>/dev/null; then
    if [ -d "node_modules" ]; then
        info "node_modules ya existe"
    else
        if command -v pnpm &>/dev/null; then
            pnpm install --silent 2>&1 | tail -3 | while IFS= read -r line; do echo "  $line"; done
        elif command -v npm &>/dev/null; then
            npm install --silent 2>&1 | tail -3 | while IFS= read -r line; do echo "  $line"; done
        fi
        success "Dependencias del frontend instaladas"
    fi
else
    info "Node.js no instalado — saltando instalación de frontend"
fi

cd "$ROOT_DIR"

# ==========================================================================
# [9/10] Ejecutar validación
# ==========================================================================
step "Ejecutando validación del sistema"

if [ -x "$ROOT_DIR/scripts/validate-system.sh" ]; then
    bash "$ROOT_DIR/scripts/validate-system.sh"
    VALIDATION_EXIT=$?
else
    info "Script de validación no encontrado o no ejecutable"
    info "Ejecutar: chmod +x scripts/validate-system.sh && ./scripts/validate-system.sh"
    VALIDATION_EXIT=1
fi

# ==========================================================================
# [10/10] Instrucciones finales
# ==========================================================================
step "Instrucciones para ejecutar"

echo ""
echo -e "  ${BOLD}📦 Backend (FastAPI):${NC}"
echo -e "  ${CYAN}cd apps/api${NC}"
echo -e "  ${CYAN}uvicorn app.main:app --reload --port 8000${NC}"
echo -e "  → API:  http://localhost:8000"
echo -e "  → Docs: http://localhost:8000/docs"
echo ""
echo -e "  ${BOLD}🌐 Frontend (Next.js):${NC}"
echo -e "  ${CYAN}cd apps/web${NC}"
echo -e "  ${CYAN}npm run dev${NC}"
echo -e "  → Web: http://localhost:3000"
echo ""
echo -e "  ${BOLD}📋 Comandos útiles:${NC}"
echo -e "  ${CYAN}./scripts/validate-system.sh${NC}    — Validar sistema"
echo -e "  ${CYAN}docker compose logs -f${NC}          — Ver logs"
echo -e "  ${CYAN}docker compose down${NC}             — Detener infraestructura"
echo ""

if [ "$VALIDATION_EXIT" -eq 0 ]; then
    echo -e "${GREEN}${BOLD}🚀 ¡Setup completado exitosamente!${NC}"
else
    echo -e "${YELLOW}${BOLD}⚠️  Setup completado con advertencias. Revisar validación arriba.${NC}"
fi

echo ""
