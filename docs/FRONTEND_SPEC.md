# Frontend Architecture Specification - React/Vite

## Overview

Frontend SPA separado em React + Vite que consome APIs multi-tenant do backend Django GeoDjango. Prioridade funcional: **Mapa com camadas da organização ativa**.

## Tech Stack

- **Frontend**: React 18+ (TSX)
- **Build Tool**: Vite
- **State Management**: React Context + Zustand (para simplificar)
- **HTTP Client**: axios com interceptadores para JWT + X-Organization-ID
- **Map Library**: MapLibre GL JS
- **Auth**: JWT (access + refresh tokens)
- **Style**: Tailwind CSS (recomendado)

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

GET /api/v1/user/organizations/
Headers: Authorization: Bearer <access_token>
Response: [{ id, name, slug, description, org_type, plan, created_at }, ...]
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
    datasource_type,   // "pmtiles" | "mvt" | "geojson" | "raster"
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
│   │   └── OrgSelector.tsx
│   ├── Map/
│   │   ├── MapContainer.tsx
│   │   ├── LayerToggle.tsx
│   │   └── MapLibreGL.tsx
│   └── Layout/
│       ├── Header.tsx
│       └── Sidebar.tsx
├── pages/
│   ├── LoginPage.tsx
│   ├── OrgSelectPage.tsx
│   └── MapPage.tsx
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
  user: User | null,
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
  isLoading: boolean,
  error: string | null,
  
  // Actions
  setActiveOrg(orgId: string): void,
  fetchUserOrganizations(): Promise<void>,
  setOrganizations(orgs): void,
}
```

#### mapStore (Zustand)
```typescript
{
  projects: Project[],
  layers: Layer[],
  datasources: Datasource[],
  visibleLayers: Set<string>,
  isLoading: boolean,
  error: string | null,
  
  // Actions
  fetchProjects(orgId): Promise<void>,
  fetchLayers(orgId): Promise<void>,
  fetchDatasources(orgId): Promise<void>,
  toggleLayerVisibility(layerId): void,
}
```

### API Service (axios interceptor pattern)

```typescript
// src/services/api.ts
import axios from 'axios';
import { useAuthStore } from '../state/authStore';

const api = axios.create({
  baseURL: process.env.VITE_API_URL || 'http://localhost:8000/api/v1',
});

// Request interceptor: adicionar tokens e org header
api.interceptors.request.use((config) => {
  const { accessToken } = useAuthStore.getState();
  const { activeOrgId } = useOrgStore.getState();
  
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  
  if (activeOrgId) {
    config.headers['X-Organization-ID'] = activeOrgId;
  }
  
  return config;
});

// Response interceptor: refresh token on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const { refreshToken } = useAuthStore.getState();
      // Fazer refresh e retry
    }
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
    ↓
Org Selection Page
    ↓ (sem X-Organization-ID, usa token)
GET /api/v1/user/organizations/
    ↓ (lista de orgs)
User selects org
    ↓
orgStore.setActiveOrg()
    ↓
Redirect to Map
    ↓ (com JWT + X-Organization-ID header)
GET /api/v1/projects/
GET /api/v1/layers/
GET /api/v1/datasources/
    ↓
Render Map with layers
```

## Map Rendering Logic

1. **Fetch projectos**: GET /api/v1/projects/ → pegar geometry para zoom inicial
2. **Fetch datasources**: GET /api/v1/datasources/ → mapear ID → URL
3. **Fetch layers**: GET /api/v1/layers/ → construir MapLibre GL spec
4. **Build MapLibre spec**:
   ```typescript
   {
     version: 8,
     sources: {
       [datasource.id]: {
         type: layer.datasource_type,
         url: layer.datasource.storage_url,
         // zoom levels, etc. from datasource.metadata
       }
     },
     layers: layers.map(layer => ({
       id: layer.id,
       source: layer.datasource_id,
       layout: layer.style_config?.layout,
       paint: layer.style_config?.paint,
       visibility: layer.visibility ? "visible" : "none",
       "z-index": layer.z_index,
     }))
   }
   ```
5. **Render**: MapLibre GL consume spec → mapa renderizado
6. **Toggle visibility**: Click em layer → toggle `visibility` → atualizar MapLibre state

## Error Handling Strategy

```typescript
// Patterns
1. 401 Unauthorized → Redirect to login
2. 403 Forbidden (X-Organization-ID) → Show error: "Org access denied"
3. 400 Bad Request (missing X-Organization-ID) → Show error: "Org selection required"
4. Network error → Retry com exponential backoff
5. API error (5xx) → Show user-friendly error + log to service

// User feedback
- Toast notifications para erros transientes
- Modal para erros críticos (auth, org)
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
- [ ] Instalar: react-router-dom, axios, zustand, maplibre-gl, tailwindcss
- [ ] Setup state management (authStore, orgStore, mapStore)
- [ ] Implementar api.ts com interceptadores
- [ ] Criar LoginForm component
- [ ] Criar OrgSelector component
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

