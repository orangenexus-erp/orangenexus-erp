# OrangeNexus ERP SaaS (MVP Venezuela)

Monorepo Turborepo para ERP SaaS multi-tenant con:

- **Backend**: FastAPI + SQLAlchemy async + JWT manual
- **Frontend**: Next.js 14 (App Router) + Tailwind
- **DB**: PostgreSQL 16 + RLS por `tenant_id`
- **Cache**: Redis 7
- **Bot**: Scraping tasa BCV (USD/VES)

## Estructura

```txt
orangenexus-erp/
├── apps/
│   ├── api/
│   └── web/
├── packages/
│   ├── shared-types/
│   └── db-migrations/
├── services/
│   └── fx-rate-bot/
├── scripts/
├── docs/
│   ├── JWT_AUTH.md
│   ├── PRE_DEVELOPMENT_CHECKLIST.md
│   └── TROUBLESHOOTING.md
├── docker-compose.yml
├── turbo.json
└── package.json
```

## Requisitos

- Python 3.11+
- Node.js 18+
- pnpm 9+
- PostgreSQL 16+

## 🚀 Quick Start

### Opción 1: Setup Automático

```bash
./scripts/quick-start.sh
```

Esto ejecuta automáticamente: verificación de dependencias, configuración de `.env`, levanta Docker, aplica migraciones, carga seed data, instala dependencias y valida el sistema.

### Opción 2: Setup Manual

Ver [Pre-Development Checklist](docs/PRE_DEVELOPMENT_CHECKLIST.md) para una guía paso a paso con comandos exactos y outputs esperados.

1. Copiar variables:

```bash
cp .env.example .env
cp apps/web/.env.local.example apps/web/.env.local
cp apps/api/.env.example apps/api/.env
```

2. Levantar infraestructura:

```bash
docker compose up -d db redis
```

3. Instalar dependencias API:

```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

4. Ejecutar migrations y seed:

```bash
cd /home/ubuntu/orangenexus-erp
./scripts/init-db.sh
./scripts/seed-data.sh
```

5. Levantar API:

```bash
cd apps/api
uvicorn app.main:app --reload --port 8000
```

6. Levantar Frontend:

```bash
cd apps/web
pnpm install
pnpm dev
```

### Validar Sistema

```bash
./scripts/validate-system.sh
```

Ejecuta 14 validaciones automáticas (Docker, PostgreSQL, Redis, migraciones, RLS, seed data, backend, frontend, JWT auth) y muestra un resumen con estado de cada check.

### Troubleshooting

Ver [Troubleshooting Guide](docs/TROUBLESHOOTING.md) para solución de problemas comunes con Docker, PostgreSQL, migraciones, RLS, JWT, backend y frontend.

## Auth JWT manual

- Register: `POST /api/v1/auth/register`
- Login: `POST /api/v1/auth/login`
- Refresh: `POST /api/v1/auth/refresh`
- Logout: `POST /api/v1/auth/logout`
- Payload access token: `sub`, `tenant_id`, `role`, `branch_id`, `exp`, `iat`
- Refresh token persistido en tabla `refresh_tokens` con revocación (`revoked`)
- Frontend almacena tokens en cookies `httpOnly` (`onx_access_token`, `onx_refresh_token`)

## Migraciones por módulo

- `001_extensions_and_core`
- `002_accounting`
- `003_sales`
- `004_treasury`
- `005_purchases`
- `006_indexes_and_rls`

## Bot BCV

Ejecución manual:

```bash
./scripts/run-bot.sh
```

Modo scheduler (06:00 AM Caracas):

```bash
FX_BOT_MODE=scheduler python services/fx-rate-bot/main.py
```
