# 🏗️ Visão Geral da Arquitetura

Uma visão técnica da plataforma **coordgeo**: como os componentes se comunicam, como os dados fluem e quais contratos estão ativos no backend atual.

---

## 🔄 Fluxo de Request (org-scoped)

```
┌──────────────────────────────────────────────────────────────────┐
│                    Frontend (React + MapLibre)                    │
│      Envia Authorization + X-Organization-ID (quando aplicável)   │
└─────────────────────────┬──────────────────────────────────────────┘
                          │
                          │ POST /api/v1/projects/
                          │ Header: X-Organization-ID: <org-uuid>
                          │ Body: {name, description, geometry}
                          │
┌─────────────────────────▼──────────────────────────────────────────┐
│            Django REST Framework + Router (api/urls.py)           │
└─────────────────────────┬──────────────────────────────────────────┘
                          │
┌─────────────────────────▼──────────────────────────────────────────┐
│              Permission Classes (request validation)               │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 1. IsAuthenticated                                            │  │
│  │    -> valida JWT                                               │  │
│  │                                                            │  │
│  │ 2. IsOrgMember                                               │  │
│  │    -> extrai X-Organization-ID                              │  │
│  │    -> valida membership do usuario                          │  │
│  │    -> seta request.active_organization/membership           │  │
│  │    -> 400 sem header / 403 sem membership                   │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────┬──────────────────────────────────────────┘
                          │
┌─────────────────────────▼──────────────────────────────────────────┐
│                 ViewSet (projects/views.py)                        │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ get_queryset(self):                                           │  │
│  │   return Project.objects.filter(organization=active_org)      │  │
│  │                                                            │  │
│  │ perform_create(self, serializer):                            │  │
│  │   serializer.save(organization=active_org, created_by=user)  │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────┬──────────────────────────────────────────┘
                          │
┌─────────────────────────▼──────────────────────────────────────────┐
│                 Django ORM (models layer)                          │
│  Project.objects.filter(organization=active_org)                   │
│  -> SQL com WHERE organization_id = ?                              │
│  -> usa indices definidos em Meta.indexes                          │
└─────────────────────────┬──────────────────────────────────────────┘
                          │
┌─────────────────────────▼──────────────────────────────────────────┐
│          PostgreSQL + PostGIS Extension (Spatial DB)               │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ CREATE INDEX ... ON project(organization_id);             │  │
│  │                                                            │  │
│  │ SELECT * FROM project                                     │  │
│  │ WHERE organization_id = $1                                 │  │
│  │ AND geometry && ST_Box2D(?)                                │  │
│  └────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Modelo de Dados

```mermaid
graph TB
    User["👤 User<br/>email<br/>username<br/>full_name"]
    
    Org["🏢 Organization<br/>name, slug<br/>org_type<br/>plan<br/>owner_id"]
    
    Membership["🔗 Membership<br/>user_id<br/>organization_id<br/>role (enum)"]
    
    Team["👥 Team<br/>name<br/>organization_id<br/>description"]
    
    Project["🗺️ Project<br/>name<br/>organization_id<br/>created_by_id<br/>geometry<br/>+ metadata"]
    
    Layer["📍 Layer<br/>name<br/>project_id<br/>datasource_id<br/>z_index<br/>style_config"]
    
    Datasource["📊 Datasource<br/>name<br/>organization_id<br/>datasource_type<br/>storage_url<br/>metadata"]
    
    Permission["🔒 Permission<br/>resource_type<br/>resource_id<br/>subject_user/team<br/>role"]
    
    User -->|owner_of| Org
    User -->|belongs_to| Membership
    Membership -->|for| Org
    Team -->|within| Org
    Project -->|in| Org
    Project -->|created_by| User
    Layer -->|in| Project
    Layer -->|uses| Datasource
    Datasource -->|in| Org
    Permission -->|granted_to| User
    
    style Org fill:#ff6b6b,color:#fff
    style User fill:#4ecdc4,color:#fff
    style Membership fill:#95e1d3,color:#000
    style Project fill:#45b7d1,color:#fff
    style Layer fill:#90ccf4,color:#000
    style Datasource fill:#f7dc6f,color:#000
    style Team fill:#bb8fce,color:#fff
    style Permission fill:#f8b88b,color:#000
```

> 💡 **Diagrama ER Automático**: Veja [diagrams/data-model.png](./diagrams/data-model.png) para visualização completa do modelo gerado automaticamente com django-extensions.

### Hierarquia de Isolamento

```
Organization (Root)
├── Membership (User → Role)
├── Project 1
│   ├── Layer A (Datasource X)
│   └── Layer B (Datasource Y)
├── Project 2
│   └── Layer C (Datasource Y)
├── Datasource X (Compartilhado entre projects)
├── Datasource Y
└── Datasource Z
```

**Regra crítica**: `Organization` **SEMPRE** é a raiz de isolamento. Nenhum modelo org-scoped pode existir sem FK para Organization.

---

## 🔐 Contexto de Organização Ativa

Usuários podem pertencer a **múltiplas organizações**. O contexto ativo é especificado via header HTTP:

### Request

```http
POST /api/v1/projects/ HTTP/1.1
Authorization: Bearer <JWT_TOKEN>
X-Organization-ID: 550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{
  "name": "Amazon Deforestation 2024",
  "description": "Monitor deforestation in the Amazon",
  "geometry": { "type": "Polygon", "coordinates": [...] }
}
```

### Fluxo na Permission Class

```python
# organizations/permissions.py - IsOrgMember

def has_permission(self, request, view):
    # 1. Extrai header
    org_id = request.headers.get('X-Organization-ID')
    
    if not org_id:
        raise ValidationError({'detail': 'X-Organization-ID header required'})
    
    # 2. Valida membership
    try:
        membership = Membership.objects.get(
            organization_id=org_id,
            user=request.user
        )
    except Membership.DoesNotExist:
        raise PermissionDenied(
            'User is not member of specified organization'
        )
    
    # 3. Setta no request
    request.active_organization = membership.organization
    request.active_membership = membership  # para verificar role depois
    
    return True
```

### Tratamento de Erros

| Cenário | HTTP Status | Motivo |
|---------|------------|--------|
| Header `X-Organization-ID` ausente | `400 Bad Request` | Contexto não especificado |
| User não é membro da org | `403 Forbidden` | Acesso negado |
| JWT token inválido | `401 Unauthorized` | Autenticação falha |
| Org ID mal formatado | `400 Bad Request` | Validation error |

---

## 🔌 API Router

Registrado em `api/urls.py` usando DRF `DefaultRouter`:

```python
router = DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"organizations", OrganizationViewSet)
router.register(r"memberships", MembershipViewSet)
router.register(r"teams", TeamViewSet)
router.register(r"projects", ProjectViewSet)
router.register(r"layers", LayerViewSet)
router.register(r"datasources", DatasourceViewSet)
router.register(r"permissions", PermissionViewSet)

urlpatterns = [
    path("auth/register/", RegisterView.as_view()),
    path("token/", TokenObtainPairView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view()),
    path("user/profile/", UserProfileView.as_view()),
    path("user/organizations/", UserOrganizationsView.as_view()),
    path("user/default-organization/", UserDefaultOrganizationView.as_view()),
]
```

Gera URLs padrão CRUD:
- `GET /api/v1/projects/` - List (paginated)
- `POST /api/v1/projects/` - Create
- `GET /api/v1/projects/{id}/` - Retrieve
- `PATCH /api/v1/projects/{id}/` - Update parcial
- `DELETE /api/v1/projects/{id}/` - Delete

---

## 🗄️ Database Layer

### PostgreSQL + PostGIS

Requisitos:
- PostgreSQL 13+
- PostGIS extension habilitada
- Python psycopg2 para conexão

### Indexes Obrigatórios

Todo modelo org-scoped DEVE ter:

```python
class Meta:
    indexes = [
        models.Index(fields=["organization"]),  # Para filtering
        models.Index(fields=["created_by"]),    # Para auditoria
    ]
```

Modelos com geometria DEVEM ser avaliados para spatial index conforme volume e tipo de query:

```python
class Project(models.Model):
    geometry = gis_models.GeometryField(
        null=True,
        blank=True
    )
```

### Otimizações de Query

```python
# ❌ RUIM - N+1 queries
for project in Project.objects.all():
    print(project.organization.name)  # Query por projeto!

# ✅ BOM - Single query com join
projects = Project.objects.select_related('organization', 'created_by')

# ✅ MELHOR - Para grandes datasets
projects = Project.objects.filter(
    organization=active_org
).values_list('id', 'name')  # Sem geometria pesada
```

---

## 🔄 Autenticação JWT

Configurado com `djangorestframework-simplejwt` e `JWTAuthentication` no DRF.

### Flow

```
1. POST /api/v1/token/ + email + password
    -> retorna {access, refresh}

2. Cliente armazena access token

3. Requests subsequentes:
   Authorization: Bearer <access_token>
   X-Organization-ID: <org-id>

4. Django valida JWT + IsAuthenticated + IsOrgMember
```

### Configuração (config/settings.py)

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}
```

---

## 🌐 Geospatial Stack

### GeoDjango + PostGIS

Modelos espaciais:

```python
from django.contrib.gis.db import models as gis_models

class Project(models.Model):
    geometry = gis_models.GeometryField(
        null=True,
        blank=True,
        help_text="Bounding box or extent of the project"
    )
```

### Serializers

```python
class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"
```

### Queries espaciais

O backend atual armazena geometria em `Project.geometry` e pode ser estendido para filtros espaciais específicos conforme necessidade.

---

## 🧪 Testing Strategy

### Multi-Tenant Isolation Tests

Obrigatório para toda feature nova:

```python
def test_organization_isolation(self):
    """User from Org A cannot see Org B data"""
    self.client.force_authenticate(user=self.user_a)
    headers = {'HTTP_X_ORGANIZATION_ID': str(self.org_a.id)}
    response = self.client.get('/api/v1/projects/', **headers)
    
    project_ids = [p['id'] for p in response.data['results']]
    self.assertNotIn(str(self.project_b.id), project_ids)

def test_missing_organization_header(self):
    """Request without header retorna 400"""
    self.client.force_authenticate(user=self.user_a)
    response = self.client.get('/api/v1/projects/')  # No header!
    self.assertEqual(response.status_code, 400)

def test_unauthorized_organization(self):
    """User not member of org returns 403"""
    self.client.force_authenticate(user=self.user_a)
    headers = {'HTTP_X_ORGANIZATION_ID': str(self.org_b.id)}
    response = self.client.get('/api/v1/projects/', **headers)
    self.assertEqual(response.status_code, 403)
```

---

## 📈 Escalabilidade

### Performance Considerations

1. **Pagination** - Todas list endpoints são paginadas (50 itens/página default)
2. **Spatial queries** - uso de geometrias em `Project` com PostGIS
3. **Select-related** - ViewSets usam `.select_related()` para evitar N+1
4. **Caching** - Redis para sessions/cache (configurável)
5. **Async** - Celery para long-running tasks (Raster processing, etc)

### Quotas (Future)

```python
class Organization(models.Model):
    subscription_plan = CharField(choices=Plan.choices)
    user_limit = IntegerField()
    storage_limit_gb = IntegerField()
    datasource_limit = IntegerField()
```

Quando implementar quotas, usar hooks em `perform_create()` para validação.

---

## 🚀 Deployment

### Production Stack

```
Client (Browser)
    ↓
Reverse Proxy (nginx)
    ↓
Gunicorn (4+ workers)
    ↓
Django Application
    ↓
PostgreSQL + PostGIS
```

### WSGI Server

```bash
gunicorn config.wsgi:application \
  --bind 127.0.0.1:8000 \
  --workers 4 \
  --threads 2 \
  --worker-class gthread
```

---

## 📚 Referências Rápidas

- **Permission class**: [organizations/permissions.py](../organizations/permissions.py#L1)
- **User model**: [accounts/models.py](../accounts/models.py)
- **Organization hirarchy**: [organizations/models.py](../organizations/models.py)
- **Geospatial models**: [projects/models.py](../projects/models.py)
- **API Router**: [api/urls.py](../api/urls.py)

---

**Status**: Production-Ready  
**Last updated**: March 2026
