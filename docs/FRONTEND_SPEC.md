# Frontend Architecture Specification - React/Vite

## Overview

Frontend SPA separado em React + Vite que consome APIs multi-tenant do backend Django GeoDjango. Prioridade funcional: **Mapa com camadas da organização ativa**.

## Tech Stack

- **Frontend**: React 19+ (TSX)
- **Build Tool**: Vite
- **State Management**: Zustand
- **HTTP Client**: axios com interceptadores para JWT + X-Organization-ID
- **Map Library**: MapLibre GL JS + maplibre-gl-draw
- **Geoprocessamento cliente**: @turf/turf
- **Auth**: JWT (access + refresh tokens)
- **Style**: Tailwind CSS v4 via `@tailwindcss/vite`

## API Endpoint Reference

Todos endpoints usam JWT Bearer token e (exceto login/bootstrap) requerem header `X-Organization-ID`.

### Authentication & Bootstrap (sem X-Organization-ID)

```
POST /api/v1/token/
Body: { email, password }
Response: { access, refresh }

POST /api/v1/token/refresh/
Body: { refresh }
Response: { access }

POST /api/v1/auth/register/
Body: { email, password, username? }
Response: { id, email, username }

GET /api/v1/user/profile/
Headers: Authorization: Bearer <access_token>
Response: { id, email, username, display_name }

GET /api/v1/user/organizations/
Headers: Authorization: Bearer <access_token>
Response: [{ id, name, slug, description, org_type, plan, owner, created_at, updated_at }, ...]

GET /api/v1/user/default-organization/
Headers: Authorization: Bearer <access_token>
Response: { id, name, slug, ... } ou 404
```

### Core Multi-Tenant Endpoints (com X-Organization-ID)

Todos endpoints retornam formato paginado:
```json
{
  "count": 42,
  "next": "http://localhost:8000/api/v1/projects/?page=2",
  "previous": null,
  "results": [...]
}
```

**Projects** (listagem da organização ativa)
```
GET /api/v1/projects/
Headers: 
  - Authorization: Bearer <token>
  - X-Organization-ID: <org_uuid>
Response: { count, next, previous, results: [{ id, name, description, geometry, created_at, created_by_id }, ...] }
```

**Layers** (camadas do mapa)
```
GET /api/v1/layers/
Headers: 
  - Authorization: Bearer <token>
  - X-Organization-ID: <org_uuid>
Response: { count, next, previous, results: [
  {
    id,
    name,
    description,
    project_id,
    datasource_id,
    visibility,       // boolean
    z_index,          // integer (0-indexed, higher = on top)
    style_config,     // MapLibre GL style JSON
    metadata          // custom fields
  },
  ...
] }
```

**Datasources** (fontes de dados - tiles, geojson, raster)
```
GET /api/v1/datasources/
Headers: 
  - Authorization: Bearer <token>
  - X-Organization-ID: <org_uuid>
Response: { count, next, previous, results: [
  {
    id,
    name,
    datasource_type,   // "vector" | "raster" | "pmtiles" | "mvt"
    storage_url,       // URL ou path (ex: "pmtiles:///static/tiles/car_sc.pmtiles")
    metadata,          // zoom_levels, projection, etc.
    is_public
  },
  ...
] }
```

## Frontend Architecture

### Directory Structure

```
src/
├── components/
│   ├── Auth/
│   │   ├── LoginForm.tsx
│   │   ├── OrgSelector.tsx
│   │   └── SignupForm.tsx
│   ├── Map/
│   │   ├── MapContainer.tsx
│   │   ├── DrawControls.tsx
│   │   ├── CreateLayerModal.tsx
│   │   ├── EditLayerModal.tsx
│   │   ├── DeleteLayerModal.tsx
│   │   ├── FeatureDetailsPanel.tsx
│   │   ├── LayerToggle.tsx
│   ├── Projects/
│   │   ├── ProjectForm.tsx
│   │   ├── CreateProjectModal.tsx
│   │   └── ProjectList.tsx
│   └── Organizations/
│       └── CreateTeamModal.tsx
├── pages/
│   ├── LandingPage.tsx
│   ├── SignupPage.tsx
│   ├── LoginPage.tsx
│   ├── OrgSelectPage.tsx
│   ├── MapPage.tsx
│   ├── SettingsPage.tsx
│   └── UpgradePage.tsx
├── services/
│   ├── api.ts              // axios instance com interceptadores
│   ├── auth.ts             // funções de login/logout
│   └── geodata.ts          // funções para projects/layers/datasources
├── state/
│   ├── authStore.ts        // Zustand store para auth
│   ├── orgStore.ts         // Zustand store para org ativa
│   └── mapStore.ts         // Zustand store para estado do mapa
├── types/
│   ├── auth.ts
│   ├── organization.ts
│   ├── geospatial.ts
│   └── api.ts
├── App.tsx
└── main.tsx

public/
├── index.html
```

### State Management Structure

#### authStore (Zustand)
```typescript
{
  accessToken: string | null,
  refreshToken: string | null,
  userProfile: User | null,
  isLoading: boolean,
  error: string | null,
  
  // Actions
  login(email, password): Promise<void>,
  logout(): void,
  refreshAccessToken(): Promise<void>,
  setTokens(access, refresh): void,
}
```

#### orgStore (Zustand)
```typescript
{
  activeOrgId: string | null,
  organizations: Organization[],
  isFreemium: boolean,
  isLoading: boolean,
  error: string | null,
  
  // Actions
  setActiveOrg(orgId: string): void,
  fetchUserOrganizations(): Promise<void>,
  fetchAndSetDefaultOrg(): Promise<void>,
  resolveAndSetActiveOrg(): Promise<string | null>,
}
```

#### mapStore (Zustand)
```typescript
{
  projects: Project[],
  layers: Layer[],
  datasources: Datasource[],
  hiddenLayerIds: Set<string>,
  activeProjectId: string | null,
  projectScopeKey: string | null,
  isLoading: boolean,
  error: string | null,
  
  // Actions
  fetchMapData(): Promise<void>,
  setProjectScope(scopeKey: string | null): void,
  setActiveProject(projectId: string | null): void,
  syncActiveProject(projects: Project[]): void,
  toggleLayerVisibility(layerId: string): void,
  isLayerVisible(layerId: string): boolean,
}
```

### API Service (axios interceptor pattern)

```typescript
// src/services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
});

// Endpoints sem header de organização
const unaffiliatedPaths = [
  '/token/',
  '/token/refresh/',
  '/auth/register/',
  '/user/profile/',
  '/user/organizations/',
  '/user/default-organization/',
  '/organizations/create-team/',
]

// Request interceptor: adicionar tokens e org header quando necessário
api.interceptors.request.use((config) => {
  const requiresOrg = !unaffiliatedPaths.some((path) => (config.url || '').includes(path))
  if (requiresOrg && activeOrgId) {
    config.headers['X-Organization-ID'] = activeOrgId;
  }
  
  return config;
});

// Response interceptor: refresh token on 401 + retry automático para erro de rede em GET/HEAD/OPTIONS
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // implementação real possui retry de rede idempotente (limite 2)
    // e refresh de token quando status = 401
    return Promise.reject(error);
  }
);

export default api;
```

## Authentication Flow

```
Login Page
    ↓ (email + password)
POST /api/v1/token/ 
    ↓ (access + refresh tokens)
authStore.setTokens()
  ↓ (bootstrap sem X-Organization-ID)
orgStore.resolveAndSetActiveOrg()
  ↓
se houver org ativa: redirect para /map
  ↓
se nao houver org ativa: redirect para /select-org
    ↓ (com JWT + X-Organization-ID header)
GET /api/v1/projects/
GET /api/v1/layers/
GET /api/v1/datasources/
    ↓
Render Map with layers
```

## Map Rendering Logic

1. **Fetch paginado completo**: requests para `/projects/`, `/layers/`, `/datasources/` agregando todas as paginas DRF.
2. **Normalizacao cliente**: mapear IDs numericos para `string` e adaptar payload (`project` -> `project_id`, `datasource` -> `datasource_id`).
3. **Inicializacao do mapa**: `MapContainer` cria instancia MapLibre com estilo de `VITE_MAP_STYLE`.
4. **Sync dinamico**: remove fontes/camadas dinamicas antigas, adiciona sources por datasource e layers por `z_index`.
5. **Style por camada**: `style_config` define `type/layout/paint`; fallback por tipo de datasource (`raster`, `vector`, GeoJSON inline).
6. **Visibilidade local**: `toggleLayerVisibility` controla `hiddenLayerIds` e aplica `layout.visibility` em runtime.
7. **Zoom inicial**: bounds derivados de `project.geometry`; fallback para bounds do Brasil quando nao ha geometria.

## Error Handling Strategy

```typescript
// Patterns
1. 401 Unauthorized → Redirect to login
2. 403 Forbidden (X-Organization-ID) → Show error: "Org access denied"
3. 400 Bad Request (missing X-Organization-ID) → Show error: "Org selection required"
4. Network error (somente idempotentes) → Retry com backoff incremental
5. API error (5xx) → Show user-friendly error + log to service

// User feedback
- Mensagens user-friendly por contexto (auth/org/map)
- Spinner durante loading
```

## Environment Variables

```
VITE_API_URL=http://localhost:8000/api/v1
VITE_MAP_STYLE=https://demotiles.maplibre.org/style.json
```

## Development Setup Checklist

- [ ] git init + setup gitignore
- [ ] npm create vite@latest -- --template react-ts
- [ ] Instalar: react-router-dom, axios, zustand, maplibre-gl, maplibre-gl-draw, @turf/turf
- [ ] Setup state management (authStore, orgStore, mapStore)
- [ ] Implementar api.ts com interceptadores
- [ ] Criar LoginForm component
- [ ] Criar OrgSelector component (ou fluxo equivalente em `OrgSelectPage`)
- [ ] Criar MapContainer component com MapLibre GL
- [ ] Implementar mobile-first layout
- [ ] Setup CI/CD (GitHub Actions)

## Production Deployment

- [ ] Build: `npm run build`
- [ ] Serve: nginx + reverse proxy para `/api/v1` → backend
- [ ] CORS: Backend já configurado para `https://app.example.com`
- [ ] Environment: `.env.production` com corretos `VITE_API_URL`

## Testing Strategy

- Unit tests: Zustand stores, API utils
- Integration tests: Auth flow, org switching
- E2E tests: Full user flow (login → map rendering)
- Use Vitest + @testing-library/react

## Next Steps for Backend

1. ✅ Expor JWT token endpoints
2. ✅ Configurar CORS
3. ✅ Endpoint bootstrap de organizações
4. ✅ Paginação padrão
5. TODO: Adicionar filtros/busca em Projects/Layers/Datasources
6. TODO: Testar CORS cross-origin com Vite dev server
7. TODO: Documentar contrato exato de style_config (MapLibre GL schema)

