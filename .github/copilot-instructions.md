# GeoDjango Multi-Tenant Codebase Guide

## Architecture Overview

This is a **multi-tenant SaaS geospatial platform** using Django + GeoDjango + PostGIS.

**Key isolation unit**: `Organization` is the root of all multi-tenancy. Every user must belong to at least one org (personal orgs are created automatically).

**Data hierarchy**: 
- `User` (custom model, email-based auth) → `Organization` (personal/team) → `Membership` (role-based) 
- `Organization` → `Projects` → `Layers` → `Datasources` (shared across projects)
- Organizations own: Datasources, Permissions, Teams (sub-groups within org)

**Spatial focus**: Uses PostGIS backend, supports Vector/Raster/PMTiles/MVT datasources. Frontend renders via MapLibre GL.

## Core Multi-Tenancy Rule

**Organization is the root isolation boundary.** All tenant-owned data MUST have:

```python
organization = models.ForeignKey(
    Organization,
    on_delete=models.CASCADE,
    db_index=True  # Required for query performance
)
```

No org-owned model may exist without this field.

## Active Organization Context (REQUIRED)

**Users may belong to multiple organizations.** The frontend MUST send a header to specify which organization is active:

```
X-Organization-ID: <uuid>
```

**Backend middleware MUST:**
1. Extract `X-Organization-ID` from request headers
2. Validate user is member of that organization
3. Attach `request.active_organization` to request object

**Error handling:**
- Header missing → `400 Bad Request`
- User not member → `403 Forbidden`

**Never infer organization implicitly** or use `.first()` as it's arbitrary when users have multiple memberships.

### Middleware Implementation (TODO)

Create `organizations/middleware.py`:

```python
from django.http import JsonResponse
from organizations.models import Organization, Membership

class ActiveOrganizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for non-API endpoints or auth endpoints
        if not request.path.startswith('/api/') or 'token' in request.path:
            return self.get_response(request)
        
        # Skip for unauthenticated requests (will be handled by auth)
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        org_id = request.headers.get('X-Organization-ID')
        
        if not org_id:
            return JsonResponse(
                {'error': 'X-Organization-ID header required'},
                status=400
            )
        
        try:
            # Validate membership
            membership = Membership.objects.get(
                organization_id=org_id,
                user=request.user
            )
            request.active_organization = membership.organization
            request.active_membership = membership
        except Membership.DoesNotExist:
            return JsonResponse(
                {'error': 'User is not member of specified organization'},
                status=403
            )
        
        return self.get_response(request)
```

Add to `config/settings.py`:
```python
MIDDLEWARE = [
    # ... other middleware ...
    'organizations.middleware.ActiveOrganizationMiddleware',
]
```

## Critical Patterns

### Multi-Tenant Query Filtering
**Every API ViewSet must filter by active organization.** Use `request.active_organization`:

```python
def get_queryset(self):
    active_org = self.request.active_organization
    return self.queryset.filter(organization=active_org)
```

**For User ViewSet** (users can be in multiple orgs, show only org members):
```python
def get_queryset(self):
    active_org = self.request.active_organization
    return User.objects.filter(
        org_memberships__organization=active_org
    ).distinct()
```

Apply this to all ViewSets accessing org-owned data (projects, datasources, layers, teams). Never expose cross-org data.

### Organization Enforcement on Create (CRITICAL)
**NEVER trust organization from request.data**. Always enforce in `perform_create()`:

```python
def perform_create(self, serializer):
    # Use active organization from middleware, NEVER from client
    serializer.save(organization=self.request.active_organization)
```

**Failure to do this is a tenant data breach vulnerability.**

**Why this matters:**
- User may belong to multiple organizations
- Frontend controls which org is active via header
- Using `.first()` is arbitrary and creates UX bugs
- Active organization must be explicit, never implicit

### Permission Classes (Required)
All org-scoped ViewSets MUST include:

```python
permission_classes = [IsAuthenticated]  # Add IsOrgMember when implemented
```

For admin-only operations, check `Membership.role == 'ADMIN'` in custom permission classes.

### Custom User Model (Email Authentication)
[accounts/models.py](accounts/models.py): `User.USERNAME_FIELD = "email"` - authenticate by email, not username.

### JWT Authentication
Configured in [config/settings.py](config/settings.py#L145-L152). All API endpoints require JWT tokens (`Authorization: Bearer <token>`). Unauthenticated requests return 401.

### GeoDjango Models
Import from `django.contrib.gis.db import models` for spatial fields. [projects/models.py](projects/models.py) uses `gis_models.GeometryField` for project boundaries.

### Spatial Performance Rules
All geometry fields MUST use spatial index:

```python
geom = models.GeometryField(spatial_index=True, srid=4326)
```

**Performance requirements:**
- Support bounding box filtering on all spatial querysets
- Never return full geometries in list endpoints (use `defer('geom')` or simplified versions)
- Prefer MVT (Mapbox Vector Tiles) or PMTiles for large datasets
- Never return raster blobs via REST API
- Use `.simplify()` for geometry previews in listings

### JSON Metadata Fields
[projects/models.py](projects/models.py#L45-L50) and [data/models.py](data/models.py#L40-L43): Use `JSONField` for flexible styling (MapLibre config) and extensible metadata without schema changes.

### Test Isolation Pattern (Mandatory)
[accounts/tests/test_api_isolation.py](accounts/tests/test_api_isolation.py): Create separate users, orgs, and memberships per test. Use `client.force_authenticate(user=...)` to set auth context. Assert queries filter correctly (e.g., user from Org A should NOT see Org B data).

**Every org-scoped model MUST include:**
1. **Isolation test**: User from Org A cannot see Org B data
2. **Creation enforcement test**: Cannot create resource with foreign org ID
3. **Permission test**: Member vs Admin access (when applicable)
4. **Queryset filtering test**: Verify only active org data returned
5. **Cascade deletion test**: Org deletion removes all owned data
6. **Missing header test**: Returns 400 when X-Organization-ID absent
7. **Unauthorized org test**: Returns 403 when user not member of org in header

Example test structure:
```python
def test_organization_isolation(self):
    # User from org_a should NOT see org_b's data
    self.client.force_authenticate(user=self.user_a)
    headers = {'HTTP_X_ORGANIZATION_ID': str(self.org_a.id)}
    response = self.client.get('/api/projects/', **headers)
    project_ids = [p['id'] for p in response.data['results']]
    self.assertNotIn(str(self.project_b.id), project_ids)

def test_missing_organization_header(self):
    self.client.force_authenticate(user=self.user_a)
    response = self.client.get('/api/projects/')  # No header
    self.assertEqual(response.status_code, 400)

def test_unauthorized_organization(self):
    self.client.force_authenticate(user=self.user_a)
    headers = {'HTTP_X_ORGANIZATION_ID': str(self.org_b.id)}  # user_a not member
    response = self.client.get('/api/projects/', **headers)
    self.assertEqual(response.status_code, 403)
```

## Database & Setup

**Database**: PostgreSQL 13+ with PostGIS extension (not SQLite).

**Critical requirements:**
- PostGIS extension must be enabled
- All foreign keys to `Organization` must have `db_index=True`
- Use spatial indexes on all geometry fields (see Spatial Performance Rules)
- Test database must use PostGIS template

**Connection** [config/settings.py](config/settings.py#L97-L110):
- Host: localhost, Port: 5432, Name: geodjango
- Credentials: User `django` / Password stored in settings (dev-only)
- Test DB uses PostGIS template: `template_postgis`

**Required system packages** (from README):
```bash
sudo apt install binutils libproj-dev gdal-bin libgdal-dev libgeos-dev libpq-dev postgresql postgresql-contrib postgis
```

## API Structure

**Router-based DRF** [api/urls.py](api/urls.py): Single `DefaultRouter` registers all ViewSets → auto-generates URL patterns (`/api/users/`, `/api/organizations/`, etc.).

**Registered endpoints**:
- `/api/users/` → UserViewSet
- `/api/organizations/` → OrganizationViewSet
- `/api/memberships/` → MembershipViewSet
- `/api/teams/` → TeamViewSet
- `/api/projects/` → ProjectViewSet
- `/api/layers/` → LayerViewSet
- `/api/datasources/` → DatasourceViewSet
- `/api/permissions/` → PermissionViewSet

All endpoints support list, create, retrieve, update, destroy actions.

## API Response Standards (Required)

**All list endpoints MUST:**
- Be paginated (use DRF's `PageNumberPagination`)
- Support filtering (use `django-filter` or `DjangoFilterBackend`)
- Support ordering (`ordering_fields` in ViewSet)
- Include proper permission classes

**Standard DRF paginated response:**
```json
{
  "count": 42,
  "next": "http://api.example.com/api/projects/?page=2",
  "previous": null,
  "results": [...]
}
```

**Never return unbounded querysets.** This is a performance and security issue.

**Spatial data in responses:**
- Use GeoJSON format for geometry fields
- Consider separate detail endpoint for full geometries
- List endpoints should return simplified or bounding box only

## Running & Testing

### WSL + Virtualenv (critical for AI agents)

- Always run Python commands in WSL from the project root using the local virtualenv at `./venv`.
- Prefer invoking the interpreter directly instead of relying on `python` from PATH.
- **Canonical test command** (execute from PowerShell/Windows):
    ```bash
    wsl bash -lc "cd /home/moises/dev/django/geodjango; ./venv/bin/python manage.py test -v 2"
    ```
- Alternative test command (from WSL shell):
    ```bash
    ./venv/bin/python run_tests.py
    ```
- Development server:
    ```bash
    ./venv/bin/python manage.py runserver
    ```
- If activation is needed in a terminal session, use:
    ```bash
    source venv/bin/activate
    ```
    and then run `python ...` commands in the same session.
- Do not attempt multiple Python launch strategies before trying the canonical WSL command above; treat it as the default.

**Production server** (Gunicorn required for PMTiles HTTP Range header support):
```bash
gunicorn config.wsgi:application --bind 127.0.0.1:8000
```

## Common Workflows

1. **Adding a new API feature**: Create ViewSet in app's views.py with multi-tenant filtering using `request.active_organization`, register in api/urls.py.
2. **Adding org-scoped data**: ForeignKey to Organization, filter by `request.active_organization` in get_queryset().
3. **User authentication checks**: Use `self.request.user` in ViewSets; JWT middleware enforces auth.
4. **Spatial data**: Use `GeometryField` in models, include geometry in serializers for GeoJSON output.
5. **Role-based access**: Check `request.active_membership.role` (MEMBER or ADMIN) in permissions classes before modifying org data.

## 🚨 NEXT STEPS - Implementation Priority

**CRITICAL: Implement Active Organization Middleware NOW** before continuing development:

1. ✅ Create `organizations/middleware.py` (see Active Organization Context section above)
2. ✅ Add middleware to `config/settings.py` MIDDLEWARE list
3. ✅ Update all existing ViewSets to use `request.active_organization`
4. ✅ Update all tests to include `HTTP_X_ORGANIZATION_ID` header
5. ✅ Add tests for missing/invalid header scenarios
6. ✅ Update frontend to send `X-Organization-ID` header on all API calls

**Why this is critical:**
- Current `.first()` approach is arbitrary and will cause UX bugs
- Users belonging to multiple orgs won't be able to control context
- Fixing this later requires changing every ViewSet and test
- Architectural decision that affects entire codebase

**Do NOT proceed with new features until this is implemented.**

## Git Conventions

**Commit messages**: Always write commit messages in **Portuguese (pt-BR)** whenever possible. Use clear, descriptive messages following conventional commits style:

```
feat: adiciona endpoint para filtrar projetos por região
fix: corrige vazamento de dados entre organizações
docs: atualiza documentação da API de datasources
refactor: reorganiza estrutura de testes de isolamento
test: adiciona testes para permissões de camadas
chore: atualiza dependências do projeto
```

**Branch naming**: Use Portuguese for feature branches: `feature/nome-da-funcionalidade`, `fix/correcao-do-bug`, `docs/atualizacao-readme`.

## Security Checklist (Pre-Merge)

Before merging any PR with org-scoped data:
- [ ] `get_queryset()` filters by `request.active_organization`
- [ ] `perform_create()` uses `request.active_organization` (NEVER from client/request.data)
- [ ] Permission classes include `IsAuthenticated`
- [ ] Multi-tenant isolation tests pass (Org A ≠ Org B)
- [ ] Tests include missing/invalid `X-Organization-ID` header scenarios
- [ ] List endpoints are paginated
- [ ] No unbounded querysets exposed
- [ ] Spatial indexes on all geometry fields
- [ ] No sensitive data (passwords/keys) in code

## SaaS Future-Proofing

The `Organization` model should support future quota enforcement:
- `subscription_plan` - Free/Pro/Enterprise tiers
- `user_limit` - Max users per org
- `storage_limit` - Max data storage
- `datasource_limit` - Max datasources
- `project_limit` - Max projects

When implementing creation endpoints, consider adding quota validation hooks for future scalability.

## Key Files Reference

- **Models**: [accounts/models.py](accounts/models.py) (User), [organizations/models.py](organizations/models.py) (Org/Team/Membership), [projects/models.py](projects/models.py) (Project/Layer), [data/models.py](data/models.py) (Datasource)
- **API Configuration**: [config/settings.py](config/settings.py), [api/urls.py](api/urls.py)
- **Tests**: [accounts/tests/test_api_isolation.py](accounts/tests/test_api_isolation.py) (multi-tenant pattern example)
- **Frontend**: [templates/core/map.html](templates/core/map.html) (MapLibre GL integration)
