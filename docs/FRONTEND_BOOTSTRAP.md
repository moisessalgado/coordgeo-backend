# Frontend Bootstrap Guide - React/Vite Setup

## 1. Create New Repository

```bash
# Via GitHub CLI
gh repo create coordgeo-frontend --public --clone --source=https://github.com/moises-salgado/coordgeo-frontend.git

# Ou manualmente no GitHub
# 1. New repository → coordgeo-frontend
# 2. PUBLIC (para código aberto)
# 3. Initialize with README
# 4. Clone locally
```

## 2. Project Initialization

```bash
cd coordgeo-frontend

# Remove default README if exists
rm README.md

# Create new Vite + React + TypeScript project
npm create vite@latest . -- --template react-ts

# Install dependencies
npm install

# Core dependencies
npm install react-router-dom axios zustand maplibre-gl

# Dev dependencies
npm install -D tailwindcss postcss autoprefixer
npm install -D @testing-library/react @testing-library/jest-dom vitest

# Setup Tailwind
npx tailwindcss init -p
```

## 3. Project Structure Setup

```bash
# Create directory structure
mkdir -p src/{components/{Auth,Map,Layout},pages,services,state,types}

# Create placeholder files
touch src/services/{api,auth,geodata}.ts
touch src/state/{authStore,orgStore,mapStore}.ts
touch src/types/{auth,organization,geospatial,api}.ts
```

## 4. Environment Variables

Create `.env` file in root:

```
VITE_API_URL=http://localhost:8000/api
VITE_MAP_STYLE=https://demotiles.maplibre.org/style.json
```

Create `.env.production` :

```
VITE_API_URL=https://api.example.com/api
VITE_MAP_STYLE=https://demotiles.maplibre.org/style.json
```

## 5. Core Type Definitions

**src/types/auth.ts**:
```typescript
export interface User {
  id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
}

export interface TokenResponse {
  access: string;
  refresh: string;
}
```

**src/types/organization.ts**:
```typescript
export interface Organization {
  id: string;
  name: string;
  slug: string;
  description: string;
  org_type: 'personal' | 'team';
  plan: 'free' | 'pro' | 'enterprise';
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface Membership {
  id: string;
  user_id: string;
  organization_id: string;
  role: 'MEMBER' | 'ADMIN';
  created_at: string;
}
```

**src/types/geospatial.ts**:
```typescript
export interface Project {
  id: string;
  name: string;
  description: string;
  geometry: GeoJSON.Geometry;
  organization_id: string;
  created_by_id: string;
  created_at: string;
  updated_at: string;
}

export interface Layer {
  id: string;
  name: string;
  description: string;
  project_id: string;
  datasource_id: string;
  visibility: boolean;
  z_index: number;
  style_config: Record<string, any>; // MapLibre GL style
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Datasource {
  id: string;
  name: string;
  datasource_type: 'pmtiles' | 'mvt' | 'geojson' | 'raster';
  storage_url: string;
  metadata: Record<string, any>;
  is_public: boolean;
  organization_id: string;
  created_at: string;
  updated_at: string;
}
```

**src/types/api.ts**:
```typescript
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  detail?: string;
  [key: string]: any;
}
```

## 6. Tailwind Configuration

**tailwind.config.js** (auto-generated, customize as needed):
```javascript
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {},
  },
  plugins: [],
};
```

**src/index.css**:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

## 7. Git Setup & Initial Commit

```bash
# Initialize git if not already
git init

# Create .gitignore
cat > .gitignore << 'EOF'
# Vite
dist/
node_modules/
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Testing
coverage/
EOF

# First commit
git add .
git commit -m "chore: inicializa projeto frontend React + Vite com configuração base"
git branch -M main
git remote add origin https://github.com/moises-salgado/coordgeo-frontend.git
git push -u origin main
```

## 8. Vite Development Server

Start dev server:
```bash
npm run dev
# Server runs on http://localhost:5173
# Backend at http://localhost:8000 (CORS already configured)
```

## 9. Testing the Connection

Once dev server is running, test API connectivity:

```bash
# In browser console or test script:
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

Expected response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

## 10. Next Steps: Component Development

### LoginForm Component
- Email + password input fields
- Form validation
- Error messages
- Submit calls `authStore.login()`

### OrgSelector Component
- Dropdown/list of user's organizations
- Select organization
- Call `orgStore.setActiveOrg()` + redirect to map

### MapContainer Component
- Initialize MapLibre GL map
- Fetch layers/datasources on org change
- Render layers in correct z-order
- Layer visibility toggles
- GeoJSON overlay support

### Integration Pattern
```tsx
// App.tsx routing
<Routes>
  <Route path="/login" element={<LoginPage />} />
  <Route path="/select-org" element={<OrgSelectPage />} />
  <Route path="/map" element={<MapPage />} />
  <Route path="*" element={<Navigate to="/login" />} />
</Routes>
```

## 11. Backend Integration Checklist

Before starting heavy frontend development, ensure backend has:

- [x] JWT token endpoint (`POST /api/token/`)
- [x] User organizations endpoint (`GET /api/user/organizations/`)
- [x] Paginated project endpoint (`GET /api/projects/`)
- [x] Paginated layers endpoint (`GET /api/layers/`)
- [x] Paginated datasources endpoint (`GET /api/datasources/`)
- [x] CORS configured for `http://localhost:5173`
- [ ] Filtros em Projects/Layers/Datasources (nice-to-have)
- [ ] OpenAPI documentation (Swagger)

## 12. Development Workflow

```bash
# Daily development
npm run dev          # Start Vite server
npm run build        # Build for production
npm run preview      # Preview production build locally
npm test             # Run tests (if setup)
npm run lint         # Lint code (if configured)

# Before committing
git status
git diff
git add .
git commit -m "feat: descrição da funcionalidade"
git push
```

## 13. CI/CD Setup (GitHub Actions)

Create `.github/workflows/deploy.yml`:

```yaml
name: Build & Deploy Frontend

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run build
      - name: Deploy to production
        run: |
          # Your deploy command (Vercel, Netlify, etc.)
```

## Environment Notes

- **Development**: Backend at `localhost:8000`, Frontend at `localhost:5173`
- **Production**: Both behind HTTPS, backend CORS configured for production domain
- **Testing**: Use `.env.test` if needed for test API endpoint

## Troubleshooting

### CORS Error in browser
```
Access to XMLHttpRequest blocked by CORS policy
```
Solution: Verify backend has:
```python
CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]
CORS_ALLOW_CREDENTIALS = True
```

### 401 Unauthorized on API calls
Solutions:
1. Check token is in Authorization header: `Bearer <token>`
2. Check token is not expired (refresh if needed)
3. Check token was obtained from `/api/token/`

### 400 Bad Request (missing X-Organization-ID)
Solution: All API calls except `/api/token/` and `/api/user/organizations/` require header:
```
X-Organization-ID: <uuid>
```

### Cannot read property 'access' from undefined
Problem: Token response format unexpected
Solution: Log response from `/api/token/` endpoint, ensure it returns `{ access, refresh }`

---

**Ready to start development!** 🚀 Follow component development checklist in step 10.

