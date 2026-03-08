# 🏢 Isolamento Multi-Tenant

Documentação do padrão de isolamento entre organizações no backend **coordgeo**.

---

## 🎯 Princípio Fundamental

> **Organization é o root de isolamento.** Nenhum dado org-scoped pode ser acessado sem validar que o usuário é membro da organização e que ela é o contexto ativo.

---

## 🔑 Componentes Chave

### 1. Request Header: `X-Organization-ID`

**Obrigatório** em toda request à API:

```http
GET /api/v1/projects/ HTTP/1.1
Authorization: Bearer <JWT>
X-Organization-ID: 550e8400-e29b-41d4-a716-446655440000
```

**Responsabilidade do frontend**:
- Enviar header em TODAS as requisições API
- Mudar header quando user switcha de org
- Armazenar header no global app state

Exceções (sem `X-Organization-ID`):
- `POST /api/v1/token/`
- `POST /api/v1/token/refresh/`
- `POST /api/v1/auth/register/`
- `GET /api/v1/user/profile/`
- `GET /api/v1/user/organizations/`
- `GET /api/v1/user/default-organization/`

### 2. Permission Class: `IsOrgMember`

**Localização**: [organizations/permissions.py](../organizations/permissions.py)

**Validação executada**:
1. ✅ Header `X-Organization-ID` está presente
2. ✅ Usuario atual é membro da org
3. ✅ Membership.role é válido (MEMBER ou ADMIN)
4. ✅ Setta `request.active_organization` e `request.active_membership`

**Erros retornados**:
- Header ausente → `400 Bad Request`
- User não membro → `403 Forbidden`

```python
from organizations.permissions import IsOrgMember
from rest_framework.permissions import IsAuthenticated

class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOrgMember]
    # ... resto do viewset
```

### 3. ViewSet Filtering

**Sempre filtrar por `request.active_organization`**:

```python
class ProjectViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        active_org = getattr(self.request, 'active_organization', None)
        if active_org is None:
            raise ValueError("active_organization not set - permission check failed?")
        
        return Project.objects.select_related(
            "organization", "created_by"
        ).filter(organization=active_org)
```

Para modelos relacionados via ForeignKey (exemplo: Layer → Project → Organization):

```python
class LayerViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        active_org = getattr(self.request, 'active_organization', None)
        if active_org is None:
            raise ValueError("active_organization not set - permission check failed?")
        
        # Filtra layers onde project pertence à active_org
        return Layer.objects.select_related(
            "project", "datasource"
        ).filter(project__organization=active_org)
```

### 4. Enforcement em Create

**NUNCA confie em dados do cliente para definir organization**:

```python
def perform_create(self, serializer):
    # ✅ CORRETO - Force active_organization
    serializer.save(
        organization=self.request.active_organization,
        created_by=self.request.user
    )

# ❌ ERRADO - Confia no client!
def perform_create(self, serializer):
    serializer.save()  # Client poderia injetar org_id!

# ❌ ERRADO - request.data não é seguro!
def perform_create(self, serializer):
    org_id = self.request.data.get('organization_id')
    serializer.save(organization_id=org_id)  # VULNERÁVEL!
```

**Validação adicional** para resources com FK para org:

```python
class LayerViewSet(viewsets.ModelViewSet):
    def perform_create(self, serializer):
        active_org = self.request.active_organization
        project = serializer.validated_data.get("project")
        datasource = serializer.validated_data.get("datasource")

        # Validar que project ∈ active_org
        if project and project.organization_id != active_org.id:
            raise ValidationError(
                {"project": "Project must belong to active organization."}
            )

        # Validar que datasource ∈ active_org
        if datasource and datasource.organization_id != active_org.id:
            raise ValidationError(
                {"datasource": "Datasource must belong to active organization."}
            )

        serializer.save()

    No backend atual, o mesmo padrão de validação extra também é aplicado em `PermissionViewSet.perform_create` para `subject_user`, `subject_team` e `resource_id` da organização ativa.
```

---

## 📋 Padrão para Novos ViewSets

**Template base recomendado**:

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from organizations.permissions import IsOrgMember
from django.core.exceptions import ValidationError

class NewResourceViewSet(viewsets.ModelViewSet):
    serializer_class = NewResourceSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]  # ✅ SEMPRE
    
    def get_queryset(self):
        active_org = getattr(self.request, 'active_organization', None)
        if active_org is None:
            raise ValueError("active_organization not set - permission check failed?")
        
        return NewResource.objects.filter(
            organization=active_org  # ✅ Sempre filtrar
        )
    
    def perform_create(self, serializer):
        # ✅ Force active_organization
        serializer.save(organization=self.request.active_organization)

    # Opcional conforme o modelo:
    # def perform_update(self, serializer):
    #     if serializer.instance.organization_id != self.request.active_organization.id:
    #         raise ValidationError("Resource belongs to different organization")
    #     serializer.save()

> Observação: no código atual nem todos os ViewSets implementam `perform_update`. O isolamento principal é garantido por `get_queryset` + `IsOrgMember`.
```

---

## 🧪 Testes Obrigatórios

Toda feature org-scoped DEVE incluir testes de isolamento.

### Setup Base

```python
from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User
from organizations.models import Organization, Membership

class MultiTenantTestCase(TestCase):
    def setUp(self):
        # Org A + User A
        self.org_a = Organization.objects.create(
            name="Company A",
            slug="company-a",
            owner=self.create_user("owner_a@example.com")
        )
        self.user_a = self.create_user("user_a@example.com")
        Membership.objects.create(
            user=self.user_a,
            organization=self.org_a,
            role=Membership.Role.MEMBER
        )

        # Org B + User B
        self.org_b = Organization.objects.create(
            name="Company B",
            slug="company-b",
            owner=self.create_user("owner_b@example.com")
        )
        self.user_b = self.create_user("user_b@example.com")
        Membership.objects.create(
            user=self.user_b,
            organization=self.org_b,
            role=Membership.Role.MEMBER
        )

        self.client = APIClient()
    
    def create_user(self, email):
        user = User.objects.create_user(email=email, username=email.split('@')[0])
        return user
```

### Test Cases Obrigatórios

#### 1️⃣ Isolamento de Dados

```python
def test_organization_isolation(self):
    """User from Org A cannot see Org B data"""
    # Create projects em ambas orgs
    project_a = Project.objects.create(
        name="Project A",
        organization=self.org_a,
        created_by=self.user_a
    )
    project_b = Project.objects.create(
        name="Project B",
        organization=self.org_b,
        created_by=self.user_b
    )

    # User A acessa sua org
    self.client.force_authenticate(user=self.user_a)
    headers = {'HTTP_X_ORGANIZATION_ID': str(self.org_a.id)}
    response = self.client.get('/api/v1/projects/', **headers)
    
    # Só vê Project A
    project_ids = [p['id'] for p in response.data['results']]
    self.assertIn(str(project_a.id), project_ids)
    self.assertNotIn(str(project_b.id), project_ids)
```

#### 2️⃣ Header Obrigatório

```python
def test_missing_organization_header(self):
    """Request without X-Organization-ID returns 400"""
    self.client.force_authenticate(user=self.user_a)
    response = self.client.get('/api/v1/projects/')  # No header!
    self.assertEqual(response.status_code, 400)
    self.assertIn('X-Organization-ID', str(response.data))
```

#### 3️⃣ Validação de Membership

```python
def test_unauthorized_organization(self):
    """User not member of org returns 403"""
    self.client.force_authenticate(user=self.user_a)
    headers = {'HTTP_X_ORGANIZATION_ID': str(self.org_b.id)}
    response = self.client.get('/api/v1/projects/', **headers)
    self.assertEqual(response.status_code, 403)
    self.assertIn('not member', str(response.data).lower())
```

#### 4️⃣ Enforcement em Create

```python
def test_create_respects_active_organization(self):
    """Created resource forced to active_organization"""
    self.client.force_authenticate(user=self.user_a)
    headers = {'HTTP_X_ORGANIZATION_ID': str(self.org_a.id)}
    
    response = self.client.post(
        '/api/v1/projects/',
        {
            'name': 'New Project',
            'description': 'Test'
            # Note: NÃO enviamos organization_id!
        },
        **headers
    )
    
    self.assertEqual(response.status_code, 201)
    created_project = Project.objects.get(id=response.data['id'])
    
    # Project SEMPRE pertence à active_org
    self.assertEqual(created_project.organization_id, self.org_a.id)
```

#### 5️⃣ Validação de ForeignKeys

```python
def test_layer_must_belong_to_active_org(self):
    """Cannot create layer com project de outra org"""
    project_b = Project.objects.create(
        name="Project B",
        organization=self.org_b,
        created_by=self.user_b
    )
    datasource_a = Datasource.objects.create(
        name="Datasource A",
        organization=self.org_a,
        datasource_type=Datasource.Type.VECTOR,
        storage_url="s3://..."
    )
    
    self.client.force_authenticate(user=self.user_a)
    headers = {'HTTP_X_ORGANIZATION_ID': str(self.org_a.id)}
    
    response = self.client.post(
        '/api/v1/layers/',
        {
            'name': 'Layer A',
            'project': str(project_b.id),  # Project from Org B!
            'datasource': str(datasource_a.id)
        },
        **headers
    )
    
    # Deve ser rejeitado
    self.assertEqual(response.status_code, 400)
    self.assertIn('project', response.data)
```

#### 6️⃣ Cascade Deletion

```python
def test_cascade_deletion_on_org(self):
    """Deleting org deleta todos related resources"""
    project = Project.objects.create(
        name="Project A",
        organization=self.org_a,
        created_by=self.user_a
    )
    
    self.org_a.delete()
    
    # Project deve ter sido deletado
    self.assertFalse(Project.objects.filter(id=project.id).exists())
```

---

## ✅ Pre-Merge Security Checklist

**Antes de fazer PR com código org-scoped, verificar**:

### Code Review

- [ ] `get_queryset()` filtra por `request.active_organization`
- [ ] `perform_create()` usa `request.active_organization` (NUNCA cliente data)
- [ ] Se houver risco de mudança de ownership, considerar `perform_update()` com validação explícita
- [ ] Se houver regra extra de remoção, considerar `perform_destroy()` com validação explícita
- [ ] Permission classes incluem `IsOrgMember`
- [ ] Serializers NÃO permitem editar `organization` field
- [ ] ForeignKeys para org-scoped resources são validados

### Testing

- [ ] Teste de isolamento multi-tenant ✅
- [ ] Teste de header obrigatório ✅
- [ ] Teste de unauthorized org ✅
- [ ] Teste de enforcement em create ✅
- [ ] Teste de validação de ForeignKeys ✅
- [ ] Teste de bootstrap sem header (`/user/organizations`, `/user/profile`) ✅
- [ ] Cobertura de casos error (400/403/404)
- [ ] Testes para read (GET) - isolamento
- [ ] Testes para write (POST/PATCH) - enforcement

### Performance & Data

- [ ] Índices em `organization` field em novo modelo (`Meta.indexes`)
- [ ] `select_related()` utilizado para ForeignKeys
- [ ] `prefetch_related()` para reverse relationships
- [ ] Nenhuma query não-paginada em list endpoints
- [ ] Nenhum `.all()` ou `.first()` arbitrário

### Documentation

- [ ] Docstring na permission class (se nova)
- [ ] Docstring no ViewSet (se novo)
- [ ] Inline comments para lógica não-óbvia
- [ ] README atualizado se novo recurso público

---

## 🚨 Vulnerabilidades Comuns

### ❌ Vulnerabilidade #1: Confiança em Cliente

```python
# ❌ INSEGURO
def perform_create(self, serializer):
    org_id = self.request.data.get('organization_id')
    serializer.save(organization_id=org_id)
```

**Ataque**: User envia `organization_id` de outra org → Cria dado em org errada

**Solução**:
```python
# ✅ SEGURO
def perform_create(self, serializer):
    serializer.save(organization=self.request.active_organization)
```

---

### ❌ Vulnerabilidade #2: Falta de Filtro

```python
# ❌ INSEGURO
def get_queryset(self):
    return Project.objects.all()  # Toda org vê tudo!
```

**Ataque**: User de Org A consegue ver/editar projects de Org B acessando direto pelo ID

**Solução**:
```python
# ✅ SEGURO
def get_queryset(self):
    return Project.objects.filter(organization=self.request.active_organization)
```

---

### ❌ Vulnerabilidade #3: Validação de FK Faltante

```python
# ❌ INSEGURO
def perform_create(self, serializer):
    serializer.save(organization=self.request.active_organization)
    # Project pode ser de outra org!
```

**Ataque**: Layer criada com Project de outra org → Acesso a dados estranhos

**Solução**:
```python
# ✅ SEGURO
def perform_create(self, serializer):
    active_org = self.request.active_organization
    project = serializer.validated_data.get("project")
    
    if project.organization_id != active_org.id:
        raise ValidationError({"project": "Invalid project for organization"})
    
    serializer.save()
```

---

### ❌ Vulnerabilidade #4: Permission Class Faltando

```python
# ❌ INSEGURO
class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]  # Esqueceu IsOrgMember!
    
    def get_queryset(self):
        return Project.objects.all()  # Sem filtro
```

**Ataque**: Usuário sem validação de membership consegue acessar dados

**Solução**:
```python
# ✅ SEGURO
class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get_queryset(self):
        return Project.objects.filter(organization=self.request.active_organization)
```

---

## 🎓 Exemplos Completos

### Exemplo 1: Resource Simples (Organization-owned)

```python
# models.py
class Team(models.Model):
    name = models.CharField(max_length=255)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [models.Index(fields=["organization"])]

# views.py
class TeamViewSet(viewsets.ModelViewSet):
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        return Team.objects.filter(organization=self.request.active_organization)
    
    def perform_create(self, serializer):
        serializer.save(organization=self.request.active_organization)

# tests.py
def test_team_isolation(self):
    team_a = Team.objects.create(name="Team A", organization=self.org_a)
    team_b = Team.objects.create(name="Team B", organization=self.org_b)
    
    self.client.force_authenticate(user=self.user_a)
    headers = {'HTTP_X_ORGANIZATION_ID': str(self.org_a.id)}
    response = self.client.get('/api/v1/teams/', **headers)
    
    team_ids = [t['id'] for t in response.data['results']]
    self.assertIn(str(team_a.id), team_ids)
    self.assertNotIn(str(team_b.id), team_ids)
```

### Exemplo 2: Resource com FK (Parent-Org-Owned)

```python
# models.py
class Feature(models.Model):
    name = models.CharField(max_length=255)
    layer = models.ForeignKey(Layer, on_delete=models.CASCADE)
    geometry = gis_models.PointField()
    
    class Meta:
        indexes = [models.Index(fields=["layer"])]

# views.py
class FeatureViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get_queryset(self):
        # Layer → Project → Organization
        active_org = self.request.active_organization
        return Feature.objects.filter(
            layer__project__organization=active_org
        ).select_related("layer")
    
    def perform_create(self, serializer):
        active_org = self.request.active_organization
        layer = serializer.validated_data.get("layer")
        
        if layer.project.organization_id != active_org.id:
            raise ValidationError({"layer": "Layer's project must belong to org"})
        
        serializer.save()
```

---

## 📚 Referências

- **Permission class**: [organizations/permissions.py](../organizations/permissions.py)
- **Organization model**: [organizations/models.py](../organizations/models.py)
- **Testes exemplo**: [accounts/tests/test_api_isolation.py](../accounts/tests/test_api_isolation.py)
- **Arquitetura**: [architecture.md](./architecture.md)

---

**Status**: Production-Ready  
**Last updated**: March 2026
