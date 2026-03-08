# 🔌 Guia de API REST

> Prefixo canônico da API: **`/api/v1/`**.

Referência dos endpoints implementados no backend `coordgeo-backend`.

- **Auth**: JWT Bearer (`Authorization: Bearer <access_token>`)
- **Contexto de organização**: `X-Organization-ID` exigido apenas para endpoints org-scoped
- **Paginação padrão DRF**: `count`, `next`, `previous`, `results`

---

## 🔑 Autenticação

### Obter tokens JWT

```http
POST /api/v1/token/ HTTP/1.1
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response** (`200 OK`):

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Refresh de access token

```http
POST /api/v1/token/refresh/ HTTP/1.1
Content-Type: application/json

{
  "refresh": "<refresh_token>"
}
```

**Response** (`200 OK`):

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Lifetimes atuais (SIMPLE_JWT)

- `ACCESS_TOKEN_LIFETIME`: 5 minutos
- `REFRESH_TOKEN_LIFETIME`: 1 dia
- `ROTATE_REFRESH_TOKENS`: `false`
- `AUTH_HEADER_TYPES`: `Bearer`

---

## 👤 Endpoints de Usuário (sem `X-Organization-ID`)

### Registro público

```http
POST /api/v1/auth/register/ HTTP/1.1
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "secure_password123",
  "username": "newuser"
}
```

**Response** (`201 Created`):

```json
{
  "id": 123,
  "email": "newuser@example.com",
  "username": "newuser"
}
```

### Perfil do usuário autenticado

```http
GET /api/v1/user/profile/ HTTP/1.1
Authorization: Bearer <access_token>
```

### Organizações do usuário (bootstrap)

```http
GET /api/v1/user/organizations/ HTTP/1.1
Authorization: Bearer <access_token>
```

**Response** (`200 OK`, lista não paginada):

```json
[
  {
    "id": 1,
    "name": "Minha Organizacao",
    "slug": "minha-organizacao",
    "description": "",
    "org_type": "personal",
    "plan": "free",
    "owner": 123,
    "created_at": "2026-01-01T10:00:00Z",
    "updated_at": "2026-01-10T10:00:00Z"
  }
]
```

### Organização padrão do usuário

```http
GET /api/v1/user/default-organization/ HTTP/1.1
Authorization: Bearer <access_token>
```

Retorna `200` com a organização padrão (preferindo `personal`) ou `404` se o usuário não tiver organizações.

---

## 👤 `/api/v1/users/` (org-scoped)

Todos os endpoints abaixo exigem:

- `Authorization: Bearer <access_token>`
- `X-Organization-ID: <org-id>`

### Listar usuários

```http
GET /api/v1/users/
```

**Response** (`200 OK`, paginada):

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 123,
      "password": "<hashed>",
      "last_login": null,
      "is_superuser": false,
      "username": "john",
      "first_name": "John",
      "last_name": "Doe",
      "is_staff": false,
      "is_active": true,
      "date_joined": "2026-01-01T10:00:00Z",
      "email": "john@example.com",
      "created_at": "2026-01-01T10:00:00Z",
      "updated_at": "2026-01-01T10:00:00Z",
      "groups": [],
      "user_permissions": []
    }
  ]
}
```

> O serializer atual de `User` expõe `fields = "__all__"`.

### Criar / obter / atualizar / remover usuário

```http
POST   /api/v1/users/
GET    /api/v1/users/<id>/
PATCH  /api/v1/users/<id>/
DELETE /api/v1/users/<id>/
```

---

## 🏢 `/api/v1/organizations/` (org-scoped)

```http
GET    /api/v1/organizations/
POST   /api/v1/organizations/
GET    /api/v1/organizations/<id>/
PATCH  /api/v1/organizations/<id>/
DELETE /api/v1/organizations/<id>/
```

### Ação extra: criar organização TEAM sem header de org

```http
POST /api/v1/organizations/create-team/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Acme Team",
  "slug": "acme-team",
  "description": "Organization for team work"
}
```

### Ação extra: upgrade de plano

```http
POST /api/v1/organizations/<id>/upgrade/
Authorization: Bearer <access_token>
X-Organization-ID: <org-id>
Content-Type: application/json

{
  "plan": "pro"
}
```

---

## 🔗 `/api/v1/memberships/` (org-scoped)

```http
GET    /api/v1/memberships/
POST   /api/v1/memberships/
GET    /api/v1/memberships/<id>/
PATCH  /api/v1/memberships/<id>/
DELETE /api/v1/memberships/<id>/
```

### Exemplo de item

```json
{
  "id": 1,
  "user": 123,
  "organization": 10,
  "role": "admin",
  "joined_at": "2026-01-01T10:00:00Z",
  "updated_at": "2026-01-10T10:00:00Z"
}
```

---

## 👥 `/api/v1/teams/` (org-scoped)

```http
GET    /api/v1/teams/
POST   /api/v1/teams/
GET    /api/v1/teams/<id>/
PATCH  /api/v1/teams/<id>/
DELETE /api/v1/teams/<id>/
```

---

## 🗺️ `/api/v1/projects/` (org-scoped)

```http
GET    /api/v1/projects/
POST   /api/v1/projects/
GET    /api/v1/projects/<id>/
PATCH  /api/v1/projects/<id>/
DELETE /api/v1/projects/<id>/
```

---

## 📍 `/api/v1/layers/` (org-scoped)

```http
GET    /api/v1/layers/
POST   /api/v1/layers/
GET    /api/v1/layers/<id>/
PATCH  /api/v1/layers/<id>/
DELETE /api/v1/layers/<id>/
```

---

## 📊 `/api/v1/datasources/` (org-scoped)

Tipos suportados atualmente:

- `vector`
- `raster`
- `pmtiles`
- `mvt`

```http
GET    /api/v1/datasources/
POST   /api/v1/datasources/
GET    /api/v1/datasources/<id>/
PATCH  /api/v1/datasources/<id>/
DELETE /api/v1/datasources/<id>/
```

---

## 🔒 `/api/v1/permissions/` (org-scoped)

Modelo ACL atual:

- `resource_type`: `organization` | `project` | `datasource`
- `resource_id`: inteiro
- sujeito: **exatamente um** entre `subject_user` e `subject_team`
- `role`: `view` | `edit` | `manage`

```http
GET    /api/v1/permissions/
POST   /api/v1/permissions/
GET    /api/v1/permissions/<id>/
PATCH  /api/v1/permissions/<id>/
DELETE /api/v1/permissions/<id>/
```

### Exemplo de criação

```http
POST /api/v1/permissions/
Authorization: Bearer <access_token>
X-Organization-ID: <org-id>
Content-Type: application/json

{
  "resource_type": "datasource",
  "resource_id": 15,
  "subject_user": 123,
  "role": "edit"
}
```

### Exemplo de item

```json
{
  "id": 99,
  "resource_type": "datasource",
  "resource_id": 15,
  "subject_user": 123,
  "subject_team": null,
  "role": "edit",
  "granted_at": "2026-01-01T10:00:00Z",
  "updated_at": "2026-01-01T10:00:00Z",
  "granted_by": 123
}
```

---

## 🔴 Erros comuns

### 400 Bad Request

```json
{
  "detail": "X-Organization-ID header required"
}
```

### 401 Unauthorized

```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden

```json
{
  "detail": "User is not member of specified organization"
}
```

### 404 Not Found

```json
{
  "detail": "Not found."
}
```

---

## 📦 Paginação

List endpoints de `ModelViewSet` usam paginação DRF (`PAGE_SIZE=50`):

```json
{
  "count": 123,
  "next": "http://api.example.com/api/v1/projects/?page=3",
  "previous": "http://api.example.com/api/v1/projects/?page=1",
  "results": []
}
```

Exceção: endpoints em `APIView` como `/api/v1/user/organizations/` retornam lista simples.

---

**Status**: Production-Ready  
**Last updated**: March 2026
