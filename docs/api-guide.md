# 🔌 Guia de API REST

Referência completa dos endpoints disponíveis no **coordgeo**. Todos os endpoints requerem:

- **Authentication**: JWT token no header `Authorization: Bearer <token>`
- **Organization Context**: Header `X-Organization-ID: <uuid>` (obrigatório para endpoints org-scoped)

---

## 🔑 Autenticação

### Obter Token JWT

```http
POST /api/token/ HTTP/1.1
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response** (201):
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Usar Token

```http
GET /api/projects/ HTTP/1.1
Authorization: Bearer <access_token>
X-Organization-ID: 550e8400-e29b-41d4-a716-446655440000
```

### Refresh Token

```http
POST /api/token/refresh/ HTTP/1.1
Content-Type: application/json

{
  "refresh": "<refresh_token>"
}
```

---

## 👤 `/api/users/`

Gestão de usuários. **Nota**: Usuários podem pertencer a múltiplas orgs.

### List Dos Usuários

```http
GET /api/users/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
```

**Response** (200):
```json
{
  "count": 42,
  "next": "http://api.example.com/api/users/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "john@example.com",
      "username": "john",
      "first_name": "John",
      "last_name": "Doe",
      "is_active": true,
      "created_at": "2025-03-01T10:00:00Z"
    }
  ]
}
```

**Query Parameters**:
- `search` - Buscar por email, username ou nome
- `ordering` - Ordenar por `created_at`, `email`
- `page` - Página (default: 1)

### Obter Usuário

```http
GET /api/users/<id>/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
```

### Criar Usuário (Admin)

```http
POST /api/users/ HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "newuser@example.com",
  "username": "newuser",
  "password": "secure_password123",
  "first_name": "John",
  "last_name": "Doe"
}
```

### Atualizar Usuário

```http
PUT /api/users/<id>/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
Content-Type: application/json

{
  "first_name": "Jane",
  "last_name": "Smith"
}
```

### Deletar Usuário

```http
DELETE /api/users/<id>/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
```

---

## 🏢 `/api/organizations/`

Gestão de organizações. Todos endpoints requerem `X-Organization-ID`.

### List de Organizações

```http
GET /api/organizations/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
```

**Response**:
```json
{
  "count": 5,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "My Company",
      "slug": "my-company",
      "description": "A geospatial startup",
      "org_type": "team",
      "plan": "pro",
      "owner_id": "user-uuid",
      "created_at": "2025-01-15T10:00:00Z",
      "updated_at": "2025-03-01T14:30:00Z"
    }
  ]
}
```

### Criar Organização

```http
POST /api/organizations/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
Content-Type: application/json

{
  "name": "New Company",
  "slug": "new-company",
  "description": "A startup",
  "org_type": "team",
  "plan": "free"
}
```

**Response** (201):
```json
{
  "id": "new-uuid",
  "name": "New Company",
  "slug": "new-company",
  ...
}
```

### Obter Organização

```http
GET /api/organizations/<id>/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
```

### Atualizar Organização

```http
PUT /api/organizations/<id>/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated description",
  "plan": "pro"
}
```

### Deletar Organização

```http
DELETE /api/organizations/<id>/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
```

⚠️ **Cascata**: Deleta todos projects, layers, datasources, memberships, teams.

---

## 🔗 `/api/memberships/`

Gestão de memberships (quem é membro de qual org).

### List Memberships

```http
GET /api/memberships/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
```

**Response**:
```json
{
  "count": 3,
  "results": [
    {
      "id": "membership-uuid",
      "user_id": "user-uuid",
      "organization_id": "org-uuid",
      "role": "admin",
      "created_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

### Criar Membership (Invite)

```http
POST /api/memberships/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
Content-Type: application/json

{
  "user_id": "user-uuid",
  "role": "member"  # "member" ou "admin"
}
```

### Atualizar Membership (Mudar Role)

```http
PUT /api/memberships/<id>/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
Content-Type: application/json

{
  "role": "admin"
}
```

### Remover Membership

```http
DELETE /api/memberships/<id>/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
```

---

## 👥 `/api/teams/`

Sub-grupos dentro de uma organização.

### List Teams

```http
GET /api/teams/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
```

**Response**:
```json
{
  "count": 2,
  "results": [
    {
      "id": "team-uuid",
      "name": "GIS Team",
      "organization_id": "org-uuid",
      "description": "Responsáveis por geospatial",
      "created_at": "2025-02-01T10:00:00Z"
    }
  ]
}
```

### Criar Team

```http
POST /api/teams/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
Content-Type: application/json

{
  "name": "Backend Team",
  "description": "Backend developers"
}
```

### Obter Team

```http
GET /api/teams/<id>/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
```

### Atualizar Team

```http
PUT /api/teams/<id>/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated desc"
}
```

### Deletar Team

```http
DELETE /api/teams/<id>/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
```

---

## 🗺️ `/api/projects/`

Projetos geoespaciais - containers para layers.

### List Projects

```http
GET /api/projects/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
```

**Query Parameters**:
- `search` - Buscar por nome
- `ordering` - `-created_at` (default), `name`
- `page` - Paginação

**Response**:
```json
{
  "count": 12,
  "results": [
    {
      "id": "project-uuid",
      "name": "Amazon Deforestation 2024",
      "description": "Monitor deforestation",
      "organization_id": "org-uuid",
      "created_by_id": "user-uuid",
      "geometry": {
        "type": "Polygon",
        "coordinates": [...]
      },
      "created_at": "2025-02-15T10:00:00Z",
      "updated_at": "2025-03-01T14:30:00Z"
    }
  ]
}
```

### Criar Project

```http
POST /api/projects/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
Content-Type: application/json

{
  "name": "Urban Heat Islands",
  "description": "Temperature analysis in cities",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[
      [-122.4, 37.8],
      [-122.4, 37.7],
      [-122.3, 37.7],
      [-122.3, 37.8],
      [-122.4, 37.8]
    ]]
  }
}
```

**Response** (201):
```json
{
  "id": "new-project-uuid",
  "name": "Urban Heat Islands",
  ...
}
```

### Obter Project

```http
GET /api/projects/<id>/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
```

### Atualizar Project

```http
PATCH /api/projects/<id>/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
Content-Type: application/json

{
  "name": "Updated Name",
  "geometry": { "type": "Polygon", "coordinates": [...] }
}
```

### Deletar Project

```http
DELETE /api/projects/<id>/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
```

⚠️ **Cascata**: Deleta todas layers do projeto.

---

## 📍 `/api/layers/`

Representações contextuais de datasources dentro de projetos.

### List Layers

```http
GET /api/layers/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
```

**Query Parameters**:
- `project` - Filtrar por project UUID
- `datasource` - Filtrar por datasource UUID
- `ordering` - `z_index` (default), `name`

**Response**:
```json
{
  "count": 8,
  "results": [
    {
      "id": "layer-uuid",
      "name": "Landsat 8 RGB",
      "description": "Composição RGB do Landsat",
      "project_id": "project-uuid",
      "datasource_id": "datasource-uuid",
      "visibility": true,
      "z_index": 10,
      "style_config": {
        "type": "raster",
        "paint": { "raster-opacity": 0.85 }
      },
      "metadata": {
        "band_count": 11,
        "resolution_m": 30
      },
      "created_at": "2025-02-20T10:00:00Z"
    }
  ]
}
```

### Criar Layer

```http
POST /api/layers/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
Content-Type: application/json

{
  "name": "NDVI Index",
  "description": "Vegetation index",
  "project": "project-uuid",
  "datasource": "datasource-uuid",
  "visibility": true,
  "z_index": 5,
  "style_config": {
    "type": "raster",
    "paint": { "raster-opacity": 0.9 }
  },
  "metadata": { "calculation": "NDVI = (NIR - RED) / (NIR + RED)" }
}
```

### Obter Layer

```http
GET /api/layers/<id>/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
```

### Atualizar Layer

```http
PATCH /api/layers/<id>/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
Content-Type: application/json

{
  "visibility": false,
  "z_index": 2,
  "style_config": { "type": "raster", "paint": { "raster-opacity": 0.5 } }
}
```

### Deletar Layer

```http
DELETE /api/layers/<id>/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
```

---

## 📊 `/api/datasources/`

Fontes de dados compartilhadas entre projetos. Suporta Vector, Raster, PMTiles, MVT.

### List Datasources

```http
GET /api/datasources/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
```

**Query Parameters**:
- `search` - Buscar por nome
- `datasource_type` - Filtrar por tipo (`vector`, `raster`, `pmtiles`, `mvt`)
- `is_public` - Filtrar públicas (`true`/`false`)

**Response**:
```json
{
  "count": 15,
  "results": [
    {
      "id": "datasource-uuid",
      "name": "OpenStreetMap Basemap",
      "description": "OSM vector tiles",
      "organization_id": "org-uuid",
      "created_by_id": "user-uuid",
      "datasource_type": "mvt",
      "storage_url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
      "metadata": {
        "zoom_levels": "0-19",
        "layers": ["buildings", "roads", "water"]
      },
      "is_public": true,
      "created_at": "2025-01-20T10:00:00Z"
    }
  ]
}
```

### Criar Datasource

```http
POST /api/datasources/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
Content-Type: application/json

{
  "name": "Sentinel-2 Imagery",
  "description": "RGB composites from Sentinel-2",
  "datasource_type": "raster",
  "storage_url": "s3://bucket/sentinel2/2024/",
  "metadata": {
    "resolution_m": 10,
    "bands": ["B2", "B3", "B4", "B8"],
    "date_range": "2024-01-01 to 2024-12-31"
  },
  "is_public": false
}
```

### Obter Datasource

```http
GET /api/datasources/<id>/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
```

### Atualizar Datasource

```http
PATCH /api/datasources/<id>/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
Content-Type: application/json

{
  "name": "Updated Name",
  "is_public": true,
  "metadata": { "new_field": "value" }
}
```

### Deletar Datasource

```http
DELETE /api/datasources/<id>/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
```

⚠️ **Cascata**: Deleta todas layers que usam este datasource.

---

## 🔒 `/api/permissions/`

Permissões granulares em recursos específicos.

### List Permissions

```http
GET /api/permissions/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
```

**Response**:
```json
{
  "count": 24,
  "results": [
    {
      "id": "permission-uuid",
      "user_id": "user-uuid",
      "object_type": "project",
      "object_id": "project-uuid",
      "action": "view",
      "is_inherited": false,
      "created_at": "2025-02-10T10:00:00Z"
    }
  ]
}
```

### Criar Permission

```http
POST /api/permissions/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
Content-Type: application/json

{
  "user_id": "user-uuid",
  "object_type": "datasource",
  "object_id": "datasource-uuid",
  "action": "edit"
}
```

### Deletar Permission

```http
DELETE /api/permissions/<id>/ HTTP/1.1
Authorization: Bearer <token>
X-Organization-ID: <org-uuid>
```

---

## 🔴 Error Responses

### 400 Bad Request

```json
{
  "detail": "X-Organization-ID header required"
}
```

Causas:
- Header `X-Organization-ID` ausente
- Dados de request inválidos
- Validation error

### 401 Unauthorized

```json
{
  "detail": "Authentication credentials were not provided."
}
```

Causas:
- Header `Authorization` faltando
- JWT token inválido/expirado

### 403 Forbidden

```json
{
  "detail": "User is not member of specified organization"
}
```

Causas:
- User não é membro da org
- Permission denied

### 404 Not Found

```json
{
  "detail": "Not found."
}
```

Causas:
- Resource não existe na org ativa
- Resource foi deletado

### 500 Internal Server Error

```json
{
  "detail": "Internal server error"
}
```

Causas:
- Bug no servidor
- Database error

---

## 📦 Paginação

Todas list endpoints suportam paginação com size 50 itens/página:

```http
GET /api/projects/?page=2 HTTP/1.1
```

**Response**:
```json
{
  "count": 123,
  "next": "http://api.example.com/api/projects/?page=3",
  "previous": "http://api.example.com/api/projects/?page=1",
  "results": [...]
}
```

---

## 🔍 Filtros e Busca

### Search

```http
GET /api/projects/?search=amazon HTTP/1.1
```

Busca em `name` e `description`.

### Ordering

```http
GET /api/projects/?ordering=-created_at HTTP/1.1
```

Ordena por `-created_at` (descendente) ou qualquer campo.

### Type Filter

```http
GET /api/datasources/?datasource_type=raster HTTP/1.1
```

---

## 🔐 Formato GeoJSON

Geometrias são retornadas em GeoJSON RFC 7946:

```json
{
  "id": "project-uuid",
  "name": "My Project",
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [-122.4, 37.8],
        [-122.4, 37.7],
        [-122.3, 37.7],
        [-122.3, 37.8],
        [-122.4, 37.8]
      ]
    ]
  }
}
```

Tipos suportados: `Point`, `LineString`, `Polygon`, `MultiPoint`, `MultiLineString`, `MultiPolygon`.

---

## 🚀 Exemplos de cliente (JavaScript)

### Obter Token

```javascript
const response = await fetch('http://localhost:8000/api/token/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});
const { access, refresh } = await response.json();
localStorage.setItem('access_token', access);
localStorage.setItem('org_id', 'org-uuid');
```

### Fazer Request

```javascript
const orgId = localStorage.getItem('org_id');
const token = localStorage.getItem('access_token');

const response = await fetch('http://localhost:8000/api/projects/', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'X-Organization-ID': orgId
  }
});
const projects = await response.json();
```

### Criar Projeto

```javascript
const response = await fetch('http://localhost:8000/api/projects/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'X-Organization-ID': orgId,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'New Project',
    description: 'Description',
    geometry: {
      type: 'Polygon',
      coordinates: [[...]]
    }
  })
});
const newProject = await response.json();
```

---

**Status**: Production-Ready  
**Last updated**: March 2025
