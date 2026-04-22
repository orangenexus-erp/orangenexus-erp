# JWT Auth Manual (OrangeNexus ERP)

## Objetivo

Autenticación 100% portable y controlada por el proyecto, sin dependencias externas de auth.

## Flujo

1. **Register** (`POST /api/v1/auth/register`)
   - Crea usuario local en `users`.
   - Emite `access_token` (30 min) y `refresh_token` (7 días).
   - Persiste refresh token en `refresh_tokens`.

2. **Login** (`POST /api/v1/auth/login`)
   - Valida email + password (bcrypt).
   - Emite access y refresh tokens.
   - Guarda refresh token en DB.

3. **Refresh** (`POST /api/v1/auth/refresh`)
   - Valida JWT refresh.
   - Verifica token existente, no revocado y no expirado.
   - Revoca el anterior (rotación) y emite un nuevo par de tokens.

4. **Logout** (`POST /api/v1/auth/logout`)
   - Revoca refresh token activo.

## Payload JWT (access token)

```json
{
  "sub": "user_id",
  "tenant_id": "uuid",
  "role": "admin",
  "branch_id": "uuid",
  "exp": 1234567890,
  "iat": 1234567890
}
```

## Tabla refresh_tokens

```sql
CREATE TABLE refresh_tokens (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id),
  token TEXT NOT NULL UNIQUE,
  expires_at TIMESTAMP NOT NULL,
  revoked BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);
```

## Middleware Backend

`app/middleware/auth.py`:
- Extrae `Bearer token`.
- Valida JWT HS256.
- Extrae `sub`, `tenant_id`, `role`, `branch_id`.
- Publica contexto en `request.state`.

`app/core/dependencies.py`:
- Inyecta contexto a PostgreSQL por request:
  - `SET app.current_tenant = '{tenant_id}'`
  - `SET app.current_user = '{user_id}'`

## Frontend

- `app/api/auth/login`: proxy al backend y set de cookies `httpOnly`.
- `app/api/auth/refresh`: rotación de tokens con cookie `refresh`.
- `app/api/auth/logout`: revocación + limpieza de cookies.
- `lib/api-client.ts`: inyección `Bearer` + auto-refresh en 401.
- `middleware.ts`: protege rutas `/dashboard/*` validando cookie de access token.
