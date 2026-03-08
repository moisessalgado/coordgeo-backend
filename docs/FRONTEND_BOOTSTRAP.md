# Frontend Bootstrap Guide - React + Vite + TypeScript

Este guia descreve o setup real usado hoje no `coordgeo-frontend`.

## 1. Prerequisitos

- Node.js `20.19+` (ou `22.12+`)
- npm
- Backend Django rodando em `http://localhost:8000`

## 2. Inicializar projeto (caso novo)

```bash
npm create vite@latest coordgeo-frontend -- --template react-ts
cd coordgeo-frontend
npm install
```

Dependencias principais:

```bash
npm install react-router-dom axios zustand maplibre-gl maplibre-gl-draw @turf/turf
```

Dependencias de build/lint:

```bash
npm install -D vite typescript @vitejs/plugin-react eslint @eslint/js typescript-eslint eslint-plugin-react-hooks eslint-plugin-react-refresh globals
npm install -D tailwindcss @tailwindcss/vite postcss autoprefixer
```

## 3. Configuracao do Vite + Tailwind v4

`vite.config.ts`:

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
})
```

`src/index.css`:

```css
@import "tailwindcss";
```

## 4. Variaveis de ambiente

`.env`:

```bash
VITE_API_URL=http://localhost:8000/api/v1
VITE_MAP_STYLE=https://demotiles.maplibre.org/style.json
```

`.env.production`:

```bash
VITE_API_URL=https://api.example.com/api/v1
VITE_MAP_STYLE=https://demotiles.maplibre.org/style.json
```

## 5. Estrutura base

```text
src/
  components/
    Auth/
    Map/
    Organizations/
    Projects/
  pages/
  services/
  state/
  types/
  App.tsx
  main.tsx
```

## 6. Contrato de API e interceptadores

- `Authorization: Bearer <access_token>` em requests autenticadas.
- `X-Organization-ID: <uuid>` para endpoints org-scoped.
- Endpoints sem `X-Organization-ID`:
  - `/token/`
  - `/token/refresh/`
  - `/auth/register/`
  - `/user/profile/`
  - `/user/organizations/`
  - `/user/default-organization/`
  - `/organizations/create-team/`

`src/services/api.ts` deve incluir:

- Request interceptor para JWT e `X-Organization-ID`.
- Response interceptor para refresh no `401`.
- Retry de rede somente para metodos idempotentes (`GET`, `HEAD`, `OPTIONS`) com limite baixo.

## 7. Rotas esperadas

```tsx
<Routes>
  <Route path="/" element={<LandingPage />} />
  <Route path="/login" element={<LoginPage />} />
  <Route path="/signup" element={<SignupPage />} />
  <Route path="/select-org" element={<OrgSelectPage />} />
  <Route path="/map" element={<MapPage />} />
  <Route path="/settings" element={<SettingsPage />} />
  <Route path="/upgrade" element={<UpgradePage />} />
  <Route path="*" element={<Navigate to="/" replace />} />
</Routes>
```

Observacao:
- O fluxo atual tenta resolver organizacao automaticamente ao entrar em rotas protegidas.
- Sem org ativa apos resolucao, redireciona para `/select-org`.

## 8. Validacao local

```bash
npm run dev
npm run lint
npm run build
```

Checagem rapida do backend:

```bash
curl -X POST http://localhost:8000/api/v1/token/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'
```

## 9. Troubleshooting

### 401 Unauthorized

1. Verificar `Authorization: Bearer <token>`.
2. Confirmar expiracao do access token e refresh automatico.
3. Confirmar que login usa `/api/v1/token/`.

### 400 Missing X-Organization-ID

1. Confirmar que endpoint nao esta na lista de excecoes.
2. Confirmar org ativa no store antes da request.

### CORS

Confirmar backend com origem do frontend (`http://localhost:5173`).

## 10. Checklist de bootstrap concluido

- [x] Vite + React + TypeScript
- [x] Tailwind v4 via `@tailwindcss/vite`
- [x] Axios com interceptadores JWT e org
- [x] Zustand para auth/org/map
- [x] Rotas principais (`/`, `/login`, `/signup`, `/select-org`, `/map`, `/settings`, `/upgrade`)
- [x] Integracao com endpoints `/api/v1/`

