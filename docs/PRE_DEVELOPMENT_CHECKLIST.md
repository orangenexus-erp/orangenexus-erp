# ✅ Pre-Development Checklist — OrangeNexus ERP SaaS

> Guía paso a paso para verificar que el entorno está listo antes de comenzar desarrollo.
> Cada paso incluye el comando exacto, output esperado e interpretación.

---

## Orden de Ejecución

| # | Paso | Tiempo est. |
|---|------|-------------|
| 1 | Verificación de Docker | ~5 seg |
| 2 | Verificación de PostgreSQL | ~5 seg |
| 3 | Ejecución de migraciones | ~15 seg |
| 4 | Carga de seed data | ~10 seg |
| 5 | Verificación de backend FastAPI | ~20 seg |
| 6 | Verificación de frontend Next.js | ~30 seg |
| 7 | Verificación de autenticación JWT | ~15 seg |
| 8 | Verificación de RLS | ~10 seg |

**Tiempo total estimado:** ~2 minutos (si todo funciona a la primera).

---

## 1. Verificación de Docker

### 1.1 Docker instalado

```bash
docker --version
```

**Output esperado:**
```
Docker version 24.x.x, build xxxxxxx
```

- ✅ **Success:** Cualquier versión 20+ es aceptable.
- ❌ **Error:** `command not found` → Instalar Docker: https://docs.docker.com/engine/install/

### 1.2 Docker Compose instalado

```bash
docker compose version
```

**Output esperado:**
```
Docker Compose version v2.x.x
```

- ✅ **Success:** Versión 2.x+
- ❌ **Error:** Si solo tienes `docker-compose` (v1), actualizar a v2.

### 1.3 Docker daemon corriendo

```bash
docker info >/dev/null 2>&1 && echo "Docker OK" || echo "Docker NOT running"
```

**Output esperado:**
```
Docker OK
```

- ✅ **Success:** `Docker OK`
- ❌ **Error:** `Docker NOT running` → Ejecutar `sudo systemctl start docker` (Linux) o iniciar Docker Desktop (macOS).

### 1.4 Levantar contenedores

```bash
cd /ruta/al/proyecto/orangenexus-erp
docker compose up -d db redis
```

**Output esperado:**
```
[+] Running 2/2
 ✔ Container orangenexus-redis  Started
 ✔ Container orangenexus-db     Started
```

- ✅ **Success:** Ambos contenedores en estado `Started` o `Running`.
- ❌ **Error:** Puerto en uso → Ver [Troubleshooting: Puerto 5432 ocupado](TROUBLESHOOTING.md#puerto-5432-ocupado).

### 1.5 Verificar contenedores activos

```bash
docker compose ps
```

**Output esperado:**
```
NAME               IMAGE              STATUS                   PORTS
orangenexus-db     postgres:16-alpine Up (healthy)             0.0.0.0:5432->5432/tcp
orangenexus-redis  redis:7-alpine     Up (healthy)             0.0.0.0:6379->6379/tcp
```

- ✅ **Success:** Estado `Up (healthy)` en ambos.
- ⚠️ **Warning:** `Up (health: starting)` → Esperar 30 segundos y verificar de nuevo.
- ❌ **Error:** `Exited` → Revisar logs: `docker compose logs db` o `docker compose logs redis`.

---

## 2. Verificación de PostgreSQL

### 2.1 PostgreSQL acepta conexiones

```bash
docker exec orangenexus-db pg_isready -U orangenexus -d orangenexus
```

**Output esperado:**
```
/var/run/postgresql:5432 - accepting connections
```

- ✅ **Success:** `accepting connections`
- ❌ **Error:** `no response` → PostgreSQL aún arrancando. Esperar 10 seg y reintentar.

### 2.2 Conectar a PostgreSQL

```bash
docker exec orangenexus-db psql -U orangenexus -d orangenexus -c "SELECT version();"
```

**Output esperado:**
```
                                                version
---------------------------------------------------------------------------------------------------------
 PostgreSQL 16.x on x86_64-pc-linux-musl, compiled by gcc (Alpine ...) ...
(1 row)
```

- ✅ **Success:** Se muestra la versión de PostgreSQL 16.
- ❌ **Error:** `FATAL: password authentication failed` → Verificar `POSTGRES_PASSWORD` en `.env`.

### 2.3 Verificar extensiones

```bash
docker exec orangenexus-db psql -U orangenexus -d orangenexus -c "SELECT extname FROM pg_extension WHERE extname IN ('uuid-ossp','pgcrypto');"
```

**Output esperado:**
```
  extname
-----------
 uuid-ossp
 pgcrypto
(2 rows)
```

- ✅ **Success:** Ambas extensiones presentes (2 rows).
- ❌ **Error:** Extensiones faltantes → Las crea automáticamente `postgres-init.sql`. Recrear contenedor: `docker compose down -v && docker compose up -d db`.

---

## 3. Ejecución de Migraciones

### 3.1 Instalar dependencias de migraciones

```bash
cd packages/db-migrations
pip install alembic sqlalchemy psycopg2-binary
```

**Output esperado:**
```
Successfully installed alembic-1.14.x sqlalchemy-2.0.x psycopg2-binary-2.9.x
```

- ✅ **Success:** Paquetes instalados sin errores.
- ❌ **Error:** Problemas de compilación → `pip install psycopg2-binary` en lugar de `psycopg2`.

### 3.2 Verificar estado de migraciones

```bash
cd packages/db-migrations
alembic current
```

**Output esperado (primera vez, DB vacía):**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
```

**Output esperado (migraciones ya aplicadas):**
```
006_indexes_and_rls (head)
```

- ✅ **Success:** Muestra `006_indexes_and_rls (head)` si ya se aplicaron.
- ✅ **Success (primera vez):** No muestra revisión → Proceder a aplicar.

### 3.3 Aplicar migraciones

```bash
cd packages/db-migrations
alembic upgrade head
```

**Output esperado:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001_extensions_and_core
INFO  [alembic.runtime.migration] Running upgrade 001_extensions_and_core -> 002_accounting
INFO  [alembic.runtime.migration] Running upgrade 002_accounting -> 003_sales
INFO  [alembic.runtime.migration] Running upgrade 003_sales -> 004_treasury
INFO  [alembic.runtime.migration] Running upgrade 004_treasury -> 005_purchases
INFO  [alembic.runtime.migration] Running upgrade 005_purchases -> 006_indexes_and_rls
```

- ✅ **Success:** Las 6 migraciones se aplican sin errores.
- ❌ **Error:** `Can't locate revision` → Verificar `alembic.ini` apunta a DB correcta.
- ❌ **Error:** `relation already exists` → Migraciones parcialmente aplicadas. Ver [Troubleshooting: Migrations ya aplicadas](TROUBLESHOOTING.md#migrations-ya-aplicadas).

### 3.4 Verificar tablas creadas

```bash
docker exec orangenexus-db psql -U orangenexus -d orangenexus -c \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';"
```

**Output esperado:**
```
 count
-------
    22
(1 row)
```

- ✅ **Success:** 21+ tablas (incluye `alembic_version`).
- ❌ **Error:** Menos de 21 → Alguna migración falló. Verificar con `alembic current`.

---

## 4. Carga de Seed Data

### 4.1 Ejecutar seed

```bash
cd packages/db-migrations
python seeds/initial_seed.py
```

**Output esperado:**
```
Seed aplicado @ 2025-01-15T10:30:45.123456
```

- ✅ **Success:** Mensaje de seed aplicado con timestamp.
- ❌ **Error:** `connection refused` → PostgreSQL no accesible en `localhost:5432`. Verificar que el contenedor está corriendo.

### 4.2 Verificar seed data

```bash
docker exec orangenexus-db psql -U orangenexus -d orangenexus -c \
  "SELECT name, tax_id FROM tenants LIMIT 5;"
```

**Output esperado:**
```
          name           |    tax_id
-------------------------+--------------
 OrangeNexus Venezuela   | J-00000000-0
(1 row)
```

- ✅ **Success:** Al menos un tenant existe.
- ❌ **Error:** `0 rows` → El seed no insertó datos. Verificar errores en el paso anterior.

### 4.3 Verificar usuario, rol y branch

```bash
docker exec orangenexus-db psql -U orangenexus -d orangenexus -c \
  "SELECT t.name as tenant, b.name as branch, r.name as role FROM tenants t JOIN branches b ON t.id = b.tenant_id JOIN roles r ON t.id = r.tenant_id LIMIT 5;"
```

**Output esperado:**
```
         tenant          |    branch     | role
-------------------------+---------------+-------
 OrangeNexus Venezuela   | Sede Caracas  | Admin
(1 row)
```

- ✅ **Success:** Tenant, branch y rol presentes.

---

## 5. Verificación de Backend FastAPI

### 5.1 Instalar dependencias

```bash
cd apps/api
pip install -r requirements.txt
```

**Output esperado:**
```
Successfully installed fastapi-0.115.5 uvicorn-0.32.0 sqlalchemy-2.0.36 ...
```

- ✅ **Success:** Sin errores de instalación.

### 5.2 Configurar variables de entorno

```bash
cp apps/api/.env.example apps/api/.env
```

> **Nota:** Para desarrollo local (sin Docker), la `DATABASE_URL` debe apuntar a `localhost`:
> ```
> DATABASE_URL=postgresql+asyncpg://orangenexus:orangenexus@localhost:5432/orangenexus
> ```

### 5.3 Iniciar backend

```bash
cd apps/api
uvicorn app.main:app --reload --port 8000
```

**Output esperado:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using StatReload
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

- ✅ **Success:** `Application startup complete` sin errores.
- ❌ **Error:** `ModuleNotFoundError` → Dependencias no instaladas. Ejecutar `pip install -r requirements.txt`.
- ❌ **Error:** `Connection refused` a DB → PostgreSQL no corriendo o URL incorrecta.

### 5.4 Health check

```bash
curl -s http://localhost:8000/health | python3 -m json.tool
```

**Output esperado:**
```json
{
    "status": "ok",
    "service": "api",
    "version": "0.1.0"
}
```

- ✅ **Success:** `"status": "ok"`
- ❌ **Error:** `Connection refused` → Backend no iniciado.

### 5.5 Verificar documentación OpenAPI

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs
```

**Output esperado:**
```
200
```

- ✅ **Success:** HTTP 200. Abrir `http://localhost:8000/docs` en el navegador para explorar la API.

---

## 6. Verificación de Frontend Next.js

### 6.1 Instalar dependencias

```bash
cd apps/web
npm install
# o con pnpm:
pnpm install
```

**Output esperado:**
```
added XXX packages in Xs
```

- ✅ **Success:** Sin errores de instalación.

### 6.2 Configurar variables de entorno

```bash
cp apps/web/.env.local.example apps/web/.env.local
```

### 6.3 Verificar build

```bash
cd apps/web
npx next build
```

**Output esperado:**
```
   ▲ Next.js 14.2.15

   Creating an optimized production build ...
 ✓ Compiled successfully
 ✓ Linting and checking validity of types
 ✓ Collecting page data
 ✓ Generating static pages
 ✓ Collecting build traces
 ✓ Finalizing page optimization

Route (app)                              Size     First Load JS
...
```

- ✅ **Success:** `Compiled successfully` y todas las rutas listadas.
- ❌ **Error:** Type errors → Ejecutar `npx tsc --noEmit` para ver detalles.

### 6.4 Iniciar en modo desarrollo

```bash
cd apps/web
npm run dev
```

**Output esperado:**
```
   ▲ Next.js 14.2.15
   - Local:        http://localhost:3000
```

- ✅ **Success:** Servidor disponible en `http://localhost:3000`.

---

## 7. Verificación de Autenticación JWT

> **Requisito:** Backend debe estar corriendo (paso 5.3).

### 7.1 Obtener IDs del seed

```bash
docker exec orangenexus-db psql -U orangenexus -d orangenexus -t -A -c \
  "SELECT t.id, b.id, r.id FROM tenants t JOIN branches b ON t.id=b.tenant_id JOIN roles r ON t.id=r.tenant_id LIMIT 1;"
```

**Output esperado:**
```
<tenant_uuid>|<branch_uuid>|<role_uuid>
```

Guardar estos valores para el siguiente paso.

### 7.2 Registrar usuario de prueba

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "<TENANT_UUID>",
    "branch_id": "<BRANCH_UUID>",
    "role_id": "<ROLE_UUID>",
    "email": "admin@orangenexus.com",
    "full_name": "Admin OrangeNexus",
    "password": "Admin123!"
  }' | python3 -m json.tool
```

**Output esperado:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
}
```

- ✅ **Success:** Recibe `access_token` y `refresh_token`.
- ❌ **Error:** `409 User already exists` → Usuario ya registrado, proceder a login.

### 7.3 Login

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@orangenexus.com",
    "password": "Admin123!"
  }' | python3 -m json.tool
```

**Output esperado:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
}
```

- ✅ **Success:** Tokens JWT válidos.
- ❌ **Error:** `401 Invalid credentials` → Verificar email/password.

### 7.4 Decodificar token (verificación manual)

```bash
# Extraer el payload del access_token (segunda parte del JWT)
echo "<ACCESS_TOKEN>" | cut -d'.' -f2 | base64 -d 2>/dev/null | python3 -m json.tool
```

**Output esperado:**
```json
{
    "sub": "<user_uuid>",
    "tenant_id": "<tenant_uuid>",
    "role": "Admin",
    "branch_id": "<branch_uuid>",
    "exp": 1705123456,
    "type": "access"
}
```

- ✅ **Success:** Payload contiene `sub`, `tenant_id`, `role`, `branch_id`.

### 7.5 Acceder a endpoint protegido

```bash
curl -s -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>" | python3 -m json.tool
```

- ✅ **Success:** Retorna datos del usuario autenticado.
- ❌ **Error:** `401 Unauthorized` → Token expirado o inválido.

---

## 8. Verificación de RLS (Row Level Security)

### 8.1 Verificar RLS habilitado

```bash
docker exec orangenexus-db psql -U orangenexus -d orangenexus -c \
  "SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname='public' AND rowsecurity=true ORDER BY tablename;"
```

**Output esperado:**
```
      tablename       | rowsecurity
----------------------+-------------
 bank_accounts        | t
 branches             | t
 chart_of_accounts    | t
 cost_centers         | t
 customers            | t
 integration_rules    | t
 journal_entries      | t
 purchase_documents   | t
 roles                | t
 sales_documents      | t
 services             | t
 suppliers            | t
 tax_withholdings     | t
 treasury_movements   | t
 users                | t
(15 rows)
```

- ✅ **Success:** 15 tablas transaccionales con `rowsecurity = t`.
- ❌ **Error:** Tablas sin RLS → Ejecutar migración `006_indexes_and_rls`.

### 8.2 Verificar políticas RLS

```bash
docker exec orangenexus-db psql -U orangenexus -d orangenexus -c \
  "SELECT tablename, policyname FROM pg_policies WHERE schemaname='public' ORDER BY tablename LIMIT 20;"
```

**Output esperado:**
```
      tablename       |          policyname
----------------------+------------------------------
 bank_accounts        | bank_accounts_tenant_policy
 bank_accounts        | bank_accounts_tenant_insert_policy
 branches             | branches_tenant_policy
 branches             | branches_tenant_insert_policy
 ...
```

- ✅ **Success:** Cada tabla tiene dos políticas: `*_tenant_policy` (SELECT/UPDATE/DELETE) y `*_tenant_insert_policy` (INSERT).

### 8.3 Test de aislamiento multi-tenant

```bash
# Sin tenant configurado (debe retornar 0 filas)
docker exec orangenexus-db psql -U orangenexus -d orangenexus -c \
  "SET ROLE orangenexus; SELECT count(*) FROM tenants;"
```

> **Nota:** Como superuser, RLS no aplica por defecto. Para testear correctamente:

```bash
docker exec orangenexus-db psql -U orangenexus -d orangenexus -c "
  CREATE ROLE test_role LOGIN PASSWORD 'test_pass';
  GRANT SELECT ON ALL TABLES IN SCHEMA public TO test_role;
"
```

```bash
docker exec orangenexus-db psql -U test_role -d orangenexus -c \
  "SELECT count(*) FROM branches;"
```

**Output esperado:**
```
 count
-------
     0
(1 row)
```

- ✅ **Success:** 0 filas → RLS impide acceso sin `app.current_tenant` configurado.

---

## Resumen

Una vez completados todos los pasos sin errores:

```
✅ Docker y contenedores funcionando
✅ PostgreSQL con extensiones instaladas
✅ 6 migraciones aplicadas (22 tablas)
✅ Seed data cargado
✅ Backend FastAPI respondiendo en :8000
✅ Frontend Next.js compilando en :3000
✅ JWT auth funcional (register/login/tokens)
✅ RLS habilitado con políticas multi-tenant
```

🚀 **¡Listo para desarrollo!**

---

## Script Automático

Para ejecutar todas las validaciones automáticamente:

```bash
./scripts/validate-system.sh
```

Si algo falla, consultar la [Guía de Troubleshooting](TROUBLESHOOTING.md).
