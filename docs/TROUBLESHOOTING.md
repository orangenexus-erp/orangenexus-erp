# 🔧 Troubleshooting Guide — OrangeNexus ERP SaaS

> Guía completa de resolución de problemas comunes.
> Cada sección incluye: **Síntoma → Causa raíz → Solución → Verificación.**

---

## Índice

- [Docker y PostgreSQL](#docker-y-postgresql)
  - [Puerto 5432 ocupado](#puerto-5432-ocupado)
  - [PostgreSQL no inicia](#postgresql-no-inicia)
  - [Permisos de volúmenes](#permisos-de-volúmenes)
  - [Conexión rechazada](#postgresql-connection-refused)
  - [Redis no inicia](#redis-no-inicia)
- [Migraciones](#migraciones)
  - [Alembic no encuentra DB](#alembic-no-encuentra-db)
  - [Migrations ya aplicadas](#migrations-ya-aplicadas)
  - [Error en SQL de migration](#error-en-sql-de-migration)
  - [Rollback de migrations](#rollback-de-migrations)
- [RLS (Row Level Security)](#rls-row-level-security)
  - [Verificar que RLS está activo](#verificar-que-rls-está-activo)
  - [Testear políticas RLS](#testear-políticas-rls)
  - [Problemas de aislamiento multi-tenant](#problemas-de-aislamiento-multi-tenant)
- [JWT Authentication](#jwt-authentication)
  - [Token inválido](#token-inválido)
  - [Token expirado](#token-expirado)
  - [Refresh token no funciona](#refresh-token-no-funciona)
  - [Cookies no se guardan](#cookies-no-se-guardan)
- [Backend FastAPI](#backend-fastapi)
  - [Errores de importación](#errores-de-importación)
  - [Database connection failed](#database-connection-failed)
  - [CORS errors](#cors-errors)
  - [Uvicorn no arranca](#uvicorn-no-arranca)
- [Frontend Next.js](#frontend-nextjs)
  - [Build errors](#build-errors)
  - [API connection failed](#api-connection-failed)
  - [Auth redirect loops](#auth-redirect-loops)
  - [Hydration errors](#hydration-errors)

---

## Docker y PostgreSQL

### Puerto 5432 ocupado

**Síntoma:**
```
Error response from daemon: Ports are not available: exposing port TCP 0.0.0.0:5432 -> 0.0.0.0:0:
listen tcp4 0.0.0.0:5432: bind: address already in use
```

**Causa raíz:** Otro proceso (PostgreSQL local u otro contenedor) ocupa el puerto 5432.

**Solución:**

```bash
# Identificar qué proceso usa el puerto
sudo lsof -i :5432
# o en Linux:
sudo ss -tlnp | grep 5432
```

**Opción A:** Detener el proceso que ocupa el puerto:
```bash
# Si es PostgreSQL local
sudo systemctl stop postgresql

# Si es otro contenedor Docker
docker stop $(docker ps -q --filter "publish=5432")
```

**Opción B:** Cambiar el puerto en `.env`:
```bash
# En .env
POSTGRES_PORT=5433
```
> ⚠️ Si cambias el puerto, actualizar también `DATABASE_URL` y `SYNC_DATABASE_URL` en `apps/api/.env`.

**Verificación:**
```bash
docker compose up -d db && docker compose ps
```

---

### PostgreSQL no inicia

**Síntoma:**
```
orangenexus-db    | FATAL: data directory "/var/lib/postgresql/data" has wrong ownership
```
O el contenedor aparece como `Exited (1)`.

**Causa raíz:** Datos corruptos en el volumen o permisos incorrectos.

**Solución:**

```bash
# Ver logs detallados
docker compose logs db

# Opción 1: Recrear volumen (BORRA TODOS LOS DATOS)
docker compose down -v
docker compose up -d db redis

# Opción 2: Reparar permisos (conserva datos)
docker compose down
docker volume inspect orangenexus-erp_pgdata
# Ajustar permisos del directorio montado
```

**Verificación:**
```bash
docker exec orangenexus-db pg_isready -U orangenexus -d orangenexus
# Output: accepting connections
```

---

### Permisos de volúmenes

**Síntoma:**
```
Permission denied: '/var/lib/postgresql/data/...'
```

**Causa raíz:** El usuario del host no tiene permisos sobre el directorio del volumen Docker.

**Solución:**

```bash
# Identificar el volumen
docker volume inspect orangenexus-erp_pgdata

# Recrear el volumen limpio
docker compose down -v
docker compose up -d db redis
```

> Si usas bind mounts en lugar de volumes nombrados:
```bash
sudo chown -R 999:999 ./data/postgres
```

**Verificación:**
```bash
docker compose ps
# db debe estar: Up (healthy)
```

---

### PostgreSQL connection refused

**Síntoma:**
```
psql: error: connection to server at "localhost" (127.0.0.1), port 5432 failed:
Connection refused. Is the server running on that host and accepting TCP/IP connections?
```

**Causa raíz:** El contenedor de PostgreSQL no está corriendo o no mapea el puerto correctamente.

**Solución:**

```bash
# 1. Verificar que el contenedor existe y está corriendo
docker compose ps

# 2. Si no está corriendo, levantarlo
docker compose up -d db

# 3. Esperar a que esté healthy
docker compose ps --format "table {{.Name}}\t{{.Status}}"

# 4. Si sigue sin funcionar, verificar red Docker
docker network ls
docker network inspect orangenexus-erp_default
```

**Verificación:**
```bash
docker exec orangenexus-db pg_isready -U orangenexus
# Output: accepting connections
```

---

### Redis no inicia

**Síntoma:**
```
orangenexus-redis  | Exited (1)
```

**Causa raíz:** Puerto 6379 ocupado o problema de memoria.

**Solución:**

```bash
# Ver logs
docker compose logs redis

# Si el puerto está ocupado
sudo lsof -i :6379

# Detener proceso conflictivo
sudo systemctl stop redis-server  # Si hay Redis local

# Recrear
docker compose up -d redis
```

**Verificación:**
```bash
docker exec orangenexus-redis redis-cli ping
# Output: PONG
```

---

## Migraciones

### Alembic no encuentra DB

**Síntoma:**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server:
Connection refused
```

**Causa raíz:** `alembic.ini` tiene una URL que apunta a un host que no resuelve (ej: `db` en vez de `localhost`).

**Solución:**

Verificar `packages/db-migrations/alembic.ini`:
```ini
# Para desarrollo local (fuera de Docker)
sqlalchemy.url = postgresql://orangenexus:orangenexus@localhost:5432/orangenexus

# Para ejecución dentro de Docker
sqlalchemy.url = postgresql://orangenexus:orangenexus@db:5432/orangenexus
```

**Alternativa:** Usar variable de entorno:
```bash
cd packages/db-migrations
SQLALCHEMY_URL=postgresql://orangenexus:orangenexus@localhost:5432/orangenexus alembic upgrade head
```

**Verificación:**
```bash
cd packages/db-migrations
alembic current
# Output: 006_indexes_and_rls (head)
```

---

### Migrations ya aplicadas

**Síntoma:**
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.DuplicateTable) relation "tenants" already exists
```

**Causa raíz:** Las tablas ya fueron creadas (posiblemente por una ejecución previa) pero `alembic_version` no lo refleja.

**Solución:**

```bash
# Ver estado actual
cd packages/db-migrations
alembic current

# Opción A: Stamp la versión correcta (sin ejecutar SQL)
alembic stamp 006_indexes_and_rls

# Opción B: Reset completo (BORRA TODOS LOS DATOS)
docker exec orangenexus-db psql -U orangenexus -d orangenexus -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
alembic upgrade head
```

**Verificación:**
```bash
alembic current
# Output: 006_indexes_and_rls (head)
```

---

### Error en SQL de migration

**Síntoma:**
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.SyntaxError) syntax error at or near "..."
```

**Causa raíz:** SQL inválido en el archivo de migración.

**Solución:**

```bash
# 1. Identificar cuál migración falló
cd packages/db-migrations
alembic current

# 2. El output muestra la última migración exitosa
# La siguiente es la que falla

# 3. Editar el archivo de migración correspondiente en:
#    packages/db-migrations/alembic/versions/

# 4. Reintentar
alembic upgrade head
```

**Verificación:**
```bash
alembic current
# Output: debe mostrar la migración más reciente
```

---

### Rollback de migrations

**Síntoma:** Necesidad de revertir una migración (cambio incorrecto, debug).

**Causa raíz:** N/A — es un procedimiento operativo.

**Solución:**

```bash
cd packages/db-migrations

# Revertir una migración
alembic downgrade -1

# Revertir a una versión específica
alembic downgrade 005_purchases

# Revertir todas las migraciones
alembic downgrade base

# Ver historial de migraciones
alembic history
```

**Verificación:**
```bash
alembic current
# Output: debe mostrar la revisión a la que hiciste downgrade
```

---

## RLS (Row Level Security)

### Verificar que RLS está activo

**Síntoma:** Duda sobre si RLS está habilitado en las tablas.

**Causa raíz:** N/A — es un procedimiento de verificación.

**Solución:**

```bash
# Listar tablas con RLS habilitado
docker exec orangenexus-db psql -U orangenexus -d orangenexus -c \
  "SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname='public' ORDER BY tablename;"
```

Las tablas transaccionales deben tener `rowsecurity = t`:
- `branches`, `roles`, `users`, `chart_of_accounts`, `cost_centers`
- `journal_entries`, `integration_rules`, `customers`, `services`
- `sales_documents`, `bank_accounts`, `treasury_movements`
- `suppliers`, `purchase_documents`, `tax_withholdings`

Las tablas de sistema (`tenants`, `alembic_version`, tablas de detalle/líneas) pueden tener `f`.

**Verificación:**
```bash
docker exec orangenexus-db psql -U orangenexus -d orangenexus -c \
  "SELECT count(*) FROM pg_tables WHERE schemaname='public' AND rowsecurity=true;"
# Output esperado: 15
```

---

### Testear políticas RLS

**Síntoma:** Necesidad de confirmar que las políticas filtran correctamente por tenant.

**Solución:**

```bash
# Crear rol de prueba
docker exec orangenexus-db psql -U orangenexus -d orangenexus -c "
  DO \$\$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'rls_test') THEN
      CREATE ROLE rls_test LOGIN PASSWORD 'rls_test';
    END IF;
  END \$\$;
  GRANT SELECT ON ALL TABLES IN SCHEMA public TO rls_test;
"

# Test SIN tenant configurado (debe retornar 0 filas)
docker exec orangenexus-db psql -U rls_test -d orangenexus -c "SELECT count(*) FROM branches;"
# Output esperado: 0

# Test CON tenant configurado
TENANT_ID=$(docker exec orangenexus-db psql -U orangenexus -d orangenexus -t -A -c "SELECT id FROM tenants LIMIT 1;")
docker exec orangenexus-db psql -U rls_test -d orangenexus -c "
  SET app.current_tenant = '$TENANT_ID';
  SELECT count(*) FROM branches;
"
# Output esperado: 1 (o más, según seed data)
```

---

### Problemas de aislamiento multi-tenant

**Síntoma:** Un tenant ve datos de otro tenant.

**Causa raíz:** Posibles causas:
1. Se usa un usuario superuser (bypass RLS).
2. `app.current_tenant` no se configura en la sesión.
3. La política RLS está mal definida.
4. La tabla no tiene RLS habilitado.

**Solución:**

```bash
# 1. Verificar que RLS está habilitado en la tabla
docker exec orangenexus-db psql -U orangenexus -d orangenexus -c \
  "SELECT rowsecurity FROM pg_tables WHERE tablename='<TABLA>';"

# 2. Verificar políticas de la tabla
docker exec orangenexus-db psql -U orangenexus -d orangenexus -c \
  "SELECT policyname, cmd, qual FROM pg_policies WHERE tablename='<TABLA>';"

# 3. Verificar que la app configura el tenant
# En el backend, el middleware debe ejecutar:
#   SET app.current_tenant = '<tenant_id>';

# 4. Asegurar que NO se usa un rol superuser para consultas de la app
docker exec orangenexus-db psql -U orangenexus -d orangenexus -c \
  "SELECT rolsuper FROM pg_roles WHERE rolname='orangenexus';"
```

> ⚠️ **Importante:** Los superusers (`rolsuper = t`) bypassean RLS por defecto.
> Para testing de RLS, usar un rol sin privilegios de superuser.

---

## JWT Authentication

### Token inválido

**Síntoma:**
```json
{"detail": "Invalid token"}
```
O HTTP 401 al enviar un request con `Authorization: Bearer <token>`.

**Causa raíz:**
1. Token malformado.
2. `SECRET_KEY` diferente entre generación y validación.
3. Algoritmo incorrecto.

**Solución:**

```bash
# 1. Verificar que el SECRET_KEY es consistente
grep SECRET_KEY apps/api/.env
grep SECRET_KEY .env
# Deben ser iguales

# 2. Verificar que el token tiene 3 partes (header.payload.signature)
echo "<TOKEN>" | tr '.' '\n' | wc -l
# Output esperado: 3

# 3. Decodificar el header del token
echo "<TOKEN>" | cut -d'.' -f1 | base64 -d 2>/dev/null
# Output esperado: {"alg":"HS256","typ":"JWT"}

# 4. Obtener un nuevo token
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@orangenexus.com", "password": "Admin123!"}' | python3 -m json.tool
```

**Verificación:**
```bash
curl -s http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <NEW_TOKEN>"
# Debe retornar datos del usuario
```

---

### Token expirado

**Síntoma:**
```json
{"detail": "Token has expired"}
```

**Causa raíz:** El `access_token` tiene un TTL de `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 30 min).

**Solución:**

```bash
# 1. Usar refresh token para obtener nuevo access token
curl -s -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<REFRESH_TOKEN>"}' | python3 -m json.tool

# 2. Si el refresh token también expiró, hacer login de nuevo
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@orangenexus.com", "password": "Admin123!"}'
```

> **Para desarrollo**, puedes extender la duración del token:
```bash
# En apps/api/.env
ACCESS_TOKEN_EXPIRE_MINUTES=480   # 8 horas
REFRESH_TOKEN_EXPIRE_DAYS=30
```

---

### Refresh token no funciona

**Síntoma:**
```json
{"detail": "Invalid refresh token"}
```

**Causa raíz:**
1. El refresh token ya fue usado (rotación de tokens).
2. El token fue revocado.
3. El refresh token expiró (`REFRESH_TOKEN_EXPIRE_DAYS`).

**Solución:**

```bash
# 1. Verificar refresh tokens en la base de datos
docker exec orangenexus-db psql -U orangenexus -d orangenexus -c \
  "SELECT id, user_id, revoked, expires_at FROM refresh_tokens ORDER BY created_at DESC LIMIT 5;"

# 2. Si todos están revocados, hacer login nuevo
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@orangenexus.com", "password": "Admin123!"}'

# 3. Limpiar tokens viejos (opcional)
docker exec orangenexus-db psql -U orangenexus -d orangenexus -c \
  "DELETE FROM refresh_tokens WHERE expires_at < NOW();"
```

---

### Cookies no se guardan

**Síntoma:** El frontend no guarda las cookies de sesión; cada recarga pierde la autenticación.

**Causa raíz:**
1. Dominio/puerto mismatch entre frontend y backend.
2. `SameSite` cookie policy.
3. CORS no permite credentials.

**Solución:**

```bash
# 1. Verificar CORS en el backend
grep CORS_ORIGINS apps/api/.env
# Debe incluir: http://localhost:3000

# 2. Verificar que el backend envía las cabeceras correctas
curl -v -X OPTIONS http://localhost:8000/api/v1/auth/login \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" 2>&1 | grep -i "access-control"

# 3. Asegurar que el frontend envía credentials
# En el código del frontend, verificar:
# fetch(url, { credentials: 'include' })
# o axios.defaults.withCredentials = true
```

> **Nota:** En el esquema actual de OrangeNexus, la autenticación es basada en tokens (Bearer), no cookies. Si usas cookies, asegurar que `httpOnly`, `secure` y `sameSite` están correctos.

---

## Backend FastAPI

### Errores de importación

**Síntoma:**
```
ModuleNotFoundError: No module named 'app.core.security'
```
o
```
ImportError: cannot import name 'xxx' from 'app.models'
```

**Causa raíz:** Dependencias no instaladas o working directory incorrecto.

**Solución:**

```bash
# 1. Verificar que estás en el directorio correcto
cd apps/api

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Si usas virtualenv
python -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt

# 4. Verificar instalación
python -c "import fastapi; print(fastapi.__version__)"
python -c "import sqlalchemy; print(sqlalchemy.__version__)"
python -c "import jwt; print(jwt.__version__)"
```

**Verificación:**
```bash
cd apps/api
python -c "from app.main import app; print('Imports OK')"
```

---

### Database connection failed

**Síntoma:**
```
sqlalchemy.exc.OperationalError: (sqlalchemy.dialects.postgresql.asyncpg)
<class 'OSError'>: [Errno 111] Connect call failed ('127.0.0.1', 5432)
```

**Causa raíz:**
1. PostgreSQL no está corriendo.
2. `DATABASE_URL` incorrecta.
3. Contraseña o usuario incorrectos.

**Solución:**

```bash
# 1. Verificar PostgreSQL
docker compose ps

# 2. Verificar DATABASE_URL
grep DATABASE_URL apps/api/.env

# Formato correcto para desarrollo local:
# DATABASE_URL=postgresql+asyncpg://orangenexus:orangenexus@localhost:5432/orangenexus

# Formato correcto dentro de Docker:
# DATABASE_URL=postgresql+asyncpg://orangenexus:orangenexus@db:5432/orangenexus

# 3. Test de conexión manual
docker exec orangenexus-db psql -U orangenexus -d orangenexus -c "SELECT 1;"
```

**Verificación:**
```bash
curl -s http://localhost:8000/health
# Output: {"status":"ok","service":"api","version":"0.1.0"}
```

---

### CORS errors

**Síntoma:**
En la consola del navegador:
```
Access to fetch at 'http://localhost:8000/api/v1/...' from origin 'http://localhost:3000'
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present
```

**Causa raíz:** El origen del frontend no está en la lista de CORS permitidos.

**Solución:**

```bash
# 1. Verificar y corregir CORS_ORIGINS en .env
# apps/api/.env
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# 2. Reiniciar el backend
# Ctrl+C y luego:
cd apps/api && uvicorn app.main:app --reload --port 8000

# 3. Verificar headers CORS
curl -s -I -X OPTIONS http://localhost:8000/api/v1/auth/login \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST"
# Buscar: Access-Control-Allow-Origin: http://localhost:3000
```

---

### Uvicorn no arranca

**Síntoma:**
```
ERROR: [Errno 98] Address already in use
```

**Causa raíz:** Otro proceso ocupa el puerto 8000.

**Solución:**

```bash
# Encontrar el proceso
lsof -i :8000

# Matar el proceso
kill -9 <PID>

# O usar otro puerto
uvicorn app.main:app --reload --port 8001
```

---

## Frontend Next.js

### Build errors

**Síntoma:**
```
Type error: Property 'xxx' does not exist on type 'yyy'
```
o
```
Module not found: Can't resolve 'xxx'
```

**Causa raíz:** Dependencias faltantes o errores de TypeScript.

**Solución:**

```bash
# 1. Reinstalar dependencias
cd apps/web
rm -rf node_modules .next
npm install  # o pnpm install

# 2. Verificar types
npx tsc --noEmit

# 3. Si el error persiste, limpiar caché
npx next build --no-cache
```

**Verificación:**
```bash
cd apps/web
npx next build
# Output: ✓ Compiled successfully
```

---

### API connection failed

**Síntoma:**
```
Error: fetch failed
  cause: Error: connect ECONNREFUSED 127.0.0.1:8000
```

**Causa raíz:** El backend no está corriendo o la URL de la API es incorrecta.

**Solución:**

```bash
# 1. Verificar que el backend corre
curl -s http://localhost:8000/health

# 2. Verificar la variable de entorno
grep NEXT_PUBLIC_API_URL apps/web/.env.local
# Debe ser: NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# 3. Reiniciar el frontend después de cambiar .env.local
cd apps/web
npm run dev
```

> **Nota:** Las variables `NEXT_PUBLIC_*` se inyectan en build time. Si cambias `.env.local`, debes reiniciar `next dev` o hacer `next build` de nuevo.

---

### Auth redirect loops

**Síntoma:** El navegador hace un bucle infinito de redirecciones entre `/login` y `/dashboard` (o similar).

**Causa raíz:**
1. El middleware redirige a login cuando no hay token.
2. Después del login, redirige a dashboard.
3. El dashboard verifica el token pero no lo encuentra (middleware re-ejecuta).
4. Loop infinito.

**Solución:**

```bash
# 1. Limpiar cookies del navegador para localhost:3000
# En Chrome: DevTools > Application > Cookies > Clear

# 2. Verificar el middleware
cat apps/web/middleware.ts

# 3. Asegurar que las rutas públicas están excluidas
# El middleware debe permitir: /login, /register, /api, /_next, /favicon.ico

# 4. Verificar que el token se guarda correctamente
# DevTools > Application > Local Storage (o Cookies) > buscar access_token
```

**Verificación:**
```bash
# Abrir en modo incógnito para descartar caché
# http://localhost:3000/login
```

---

### Hydration errors

**Síntoma:**
```
Error: Hydration failed because the initial UI does not match what was rendered on the server.
```

**Causa raíz:** Diferencia entre el render del servidor y del cliente (típicamente por datos dinámicos como timestamps o tokens).

**Solución:**

```bash
# 1. Envolver componentes dinámicos con 'use client'
# O usar dynamic imports con ssr: false

# 2. Evitar acceder a window/document/localStorage en el render inicial

# 3. Usar useEffect para datos que solo existen en el cliente
```

**Ejemplo de fix:**
```tsx
// ❌ Mal
const token = localStorage.getItem('token');

// ✅ Bien
const [token, setToken] = useState<string | null>(null);
useEffect(() => {
  setToken(localStorage.getItem('token'));
}, []);
```

---

## Comandos Útiles de Diagnóstico

### Estado general del sistema

```bash
# Todo en un comando
echo "=== Docker ===" && docker compose ps && \
echo "=== DB ===" && docker exec orangenexus-db pg_isready -U orangenexus && \
echo "=== Redis ===" && docker exec orangenexus-redis redis-cli ping && \
echo "=== API ===" && curl -s http://localhost:8000/health && \
echo ""
```

### Logs en tiempo real

```bash
# Logs de todos los servicios
docker compose logs -f

# Solo PostgreSQL
docker compose logs -f db

# Solo Redis
docker compose logs -f redis

# Backend (si corre con uvicorn directo)
# Los logs aparecen en la terminal donde se ejecutó uvicorn
```

### Reset completo

```bash
# ⚠️ BORRA TODOS LOS DATOS
docker compose down -v
docker compose up -d db redis

# Esperar a que PostgreSQL esté listo
sleep 10

# Re-aplicar migraciones y seed
cd packages/db-migrations
alembic upgrade head
python seeds/initial_seed.py
```

---

## ¿Problema no listado?

1. Ejecutar el script de validación: `./scripts/validate-system.sh`
2. Revisar logs: `docker compose logs`
3. Verificar variables de entorno en los archivos `.env`
4. Verificar que todas las dependencias están instaladas
