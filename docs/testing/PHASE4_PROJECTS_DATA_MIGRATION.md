# Fase 4 — Migração de Projects e Data

Data: 2026-03-05

## 1) Objetivo da Fase 4

Migrar os testes de isolamento multi-tenant dos módulos `projects` e `data` para pytest, completando 68% da migração total.

## 2) Arquivos Migrados

### 2.1) projects/tests/test_api_isolation.py → tests_pytest/test_projects_isolation_pytest.py

**Testes migrados (8 totais)**:

1. `test_01_user_lists_own_projects`
   - Valida isolamento de projetos entre organizações
   - User A vê apenas Project A de Org A

2. `test_02_user_cannot_get_other_project`
   - Acesso a projekt de outra org retorna 404
   - Isolamento de detalhes de project cross-tenant

3. `test_03_user_lists_layers_from_own_projects`
   - Isolamento de layers entre organizações
   - User A vê apenas Layer A da Org A

4. `test_04_user_cannot_get_other_layer`
   - Acesso a layer de outra org retorna 404
   - Isolamento de detalhes de layer cross-tenant

5. `test_05_anon_cannot_list_projects`
   - Endpoints de projects requerem autenticação
   - Resposta 401 para requisições anônimas

6. `test_06_missing_organization_header_returns_400`
   - Header X-Organization-ID é obrigatório
   - Resposta 400 quando header ausente

7. `test_07_unauthorized_organization_returns_403`
   - Usuários não podem acessar orgs às quais não pertencem
   - Resposta 403 para acesso não autorizado

8. `test_08_create_project_enforces_active_organization`
   - Org enviada no payload é sobrescrita pela org do header
   - Projeto sempre criado na org do X-Organization-ID

### 2.2) data/tests/test_api_isolation.py → tests_pytest/test_data_isolation_pytest.py

**Testes migrados (6 totais)**:

1. `test_01_user_lists_own_datasources`
   - Isolamento de datasources entre organizações
   - User A vê apenas Datasource A de Org A

2. `test_02_user_cannot_get_other_datasource`
   - Acesso a datasource de outra org retorna 404
   - Isolamento de detalhes cross-tenant

3. `test_03_anon_cannot_list_datasources`
   - Endpoints de datasources requerem autenticação
   - Resposta 401 para requisições anônimas

4. `test_04_missing_organization_header_returns_400`
   - Header X-Organization-ID é obrigatório
   - Resposta 400 quando header ausente

5. `test_05_unauthorized_organization_returns_403`
   - Usuários não podem acessar orgs às quais não pertencem
   - Resposta 403 para acesso não autorizado

6. `test_06_create_datasource_enforces_active_organization`
   - Org enviada no payload é sobrescrita pela org do header
   - Datasource sempre criado na org do X-Organization-ID

## 3) Novas Fixtures Criadas (em conftest.py)

### 3.1) project_factory

```python
@pytest.fixture
def project_factory(db):
    """Factory para criar projetos."""
    def factory(*, name: str, organization, created_by=None, description: str = ""):
        return Project.objects.create(...)
    return factory
```

### 3.2) datasource_factory

```python
@pytest.fixture
def datasource_factory(db):
    """Factory para criar datasources."""
    def factory(
        *,
        name: str,
        organization,
        created_by,
        datasource_type: str = Datasource.Type.VECTOR,
        storage_url: str = "s3://bucket/data.geojson",
        description: str = "",
    ):
        return Datasource.objects.create(...)
    return factory
```

### 3.3) layer_factory

```python
@pytest.fixture
def layer_factory(db):
    """Factory para criar layers."""
    def factory(
        *,
        name: str,
        project,
        datasource,
        description: str = "",
        visibility: bool = True,
        z_index: int = 0,
    ):
        return Layer.objects.create(...)
    return factory
```

### 3.4) Fixtures Locais

- **`multi_project_setup`**: Setup com 2 users, 2 orgs, 2 projects, 2 datasources, 2 layers
- **`multi_datasource_setup`**: Setup com 2 users, 2 orgs, 2 datasources (raster + vector)

## 4) Cobertura de Migração - Estado Atual

### Progresso Total

| Módulo | Testes Totais | Migrados | Pendentes | % Concluído |
|--------|---------------|----------|-----------|-------------|
| api | 2 | 2 | 0 | 100% |
| accounts | 4 | 4 | 0 | 100% |
| organizations | 7 | 7 | 0 | 100% |
| projects | 8 | 8 | 0 | 100% |
| data | 6 | 6 | 0 | 100% |
| permissions | 5 | 0 | 5 | 0% |
| **TOTAL** | **32** | **27** | **5** | **84%** |

### Distribuição por Fase

- **Fase 1**: 2 testes (piloto)
- **Fase 2**: +2 testes (API compatibility)
- **Fase 3**: +11 testes (accounts + organizations)
- **Fase 4**: +14 testes (projects + data)
- **Total Fase 4**: 29 testes em pytest

## 5) Testes Coletados

```bash
$ pytest tests_pytest/ --co -q
29 tests collected in 0.03s
```

### Breakdown por Arquivo

| Arquivo | Testes | Classe |
|---------|--------|--------|
| test_api_versioning_pytest.py | 2 | Functions |
| test_api_compatibility_pytest.py | 2 | TestAPIVersioningCompatibility |
| test_accounts_isolation_pytest.py | 4 | TestAccountsAPIIsolation |
| test_organizations_isolation_pytest.py | 7 | TestOrganizationsAPIIsolation |
| test_projects_isolation_pytest.py | 8 | TestProjectsAPIIsolation |
| test_data_isolation_pytest.py | 6 | TestDataAPIIsolation |
| **TOTAL** | **29** | - |

## 6) Padrões Estabelecidos na Fase 4

### 6.1) Setup Complexo com Múltiplos Recursos

**Exemplo: multi_project_setup**

```python
@pytest.fixture
def multi_project_setup(
    self, user_factory, org_factory, membership_factory, 
    project_factory, datasource_factory, layer_factory
):
    """Setup cria chain completo: User → Org → Project → Datasource → Layer"""
    # Org A: user_a → org_a → project_a → datasource_a → layer_a
    # Org B: user_b → org_b → project_b → datasource_b → layer_b
    return {
        "user_a": user_a, "org_a": org_a, "project_a": project_a,
        "datasource_a": datasource_a, "layer_a": layer_a,
        "user_b": user_b, "org_b": org_b, "project_b": project_b,
        "datasource_b": datasource_b, "layer_b": layer_b,
    }
```

**Vantagem**: Fixture reutilizável para múltiplos testes com dados relacionados.

### 6.2) Testes de Força Organizacional

Padrão de teste que valida se org do payload é ignorada:

```python
def test_08_create_project_enforces_active_organization(
    self, api_client, multi_project_setup, org_headers_factory
):
    """Org enviada no payload deve ser ignorada em favor da org ativa."""
    user_a = multi_project_setup["user_a"]
    org_a = multi_project_setup["org_a"]
    org_b = multi_project_setup["org_b"]
    headers = org_headers_factory(user=user_a, org=org_a)

    payload = {
        "name": "Project Enforced Org",
        "organization": org_b.id,  # Tenta enviar org_b
    }
    response = api_client.post("/api/v1/projects/", payload, format="json", **headers)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["organization"] == org_a.id  # Deve estar na Org A
```

**Vantagem**: Garante que API não permite manipulação de org via payload.

## 7) Fixtures Totais em conftest.py

| Fixture | Tipo | Entrada | Saída |
|---------|------|---------|-------|
| user_factory | Factory | username, email, password | User |
| org_factory | Factory | name, slug, owner | Organization |
| membership_factory | Factory | user, organization, role | Membership |
| project_factory | Factory | name, organization, created_by | Project |
| datasource_factory | Factory | name, organization, created_by, type, url | Datasource |
| layer_factory | Factory | name, project, datasource | Layer |
| jwt_token_factory | Token | user | JWT access_token string |
| org_headers_factory | Headers | user, org | Dict com HTTP_AUTHORIZATION + HTTP_X_ORGANIZATION_ID |
| api_client | Client | - | APIClient |

**Total: 9 fixtures globais disponíveis**

## 8) Análise de Similitude Entre Testes

Todos os módulos migrados (accounts, organizations, projects, data) seguem padrão quase idêntico:

```
✓ Test 01: user_lists_own_Xs (lista recursos da própria org)
✓ Test 02: user_cannot_get_other_X (404 em recurso de outra org)
✓ Test 03-04 (variam por módulo - teams, layers, etc)
✓ Test XX-1: anon_cannot_list_Xs (401 sem auth)
✓ Test XX: missing_organization_header_returns_400 (400 sem header)
✓ Test XX+1: unauthorized_organization_returns_403 (403 org não autorizada)
✓ Test XX+2: create_X_enforces_active_organization (força org do header)
```

**Insight**: Padrão muito consistente - perfeito para refatoração futura com parametrized tests.

## 9) Próximos Passos (Fase 5)

### Módulo Pendente

- **permissions** (5 testes) - Isolamento de permissions

### Após Fase 5

- **Fase 6**: Refatoração com pytest.mark.parametrize
  - Converter padrão repetido em parametrized tests
  - Reduzir duplicidade de código entre modules
  - Exemplo: Todos os testes de "list own resources" podem virar um

- **Fase 7**: Deprecação de Django TestCase
  - Mover testes remanescentes de Django para pytest
  - Remover `python manage.py test` da CI/CD
  - Fazer pytest o runner padrão

- **Fase 8**: Coverage e Otimizações
  - Validar cobertura com pytest-cov
  - Parallelização com pytest-xdist
  - Integração com CI/CD (GitHub Actions)

## 10) Arquivos Criados na Fase 4

- **Criados**:
  - `tests_pytest/test_projects_isolation_pytest.py` (8 testes)
  - `tests_pytest/test_data_isolation_pytest.py` (6 testes)

- **Modificados**:
  - `tests_pytest/conftest.py` (+3 fixtures: project_factory, datasource_factory, layer_factory)

**Total de testes em pytest**: 29 (2 piloto + 2 API + 4 accounts + 7 organizations + 8 projects + 6 data)  
**Total de testes em Django**: 32 (mantidos para compatibilidade)  
**Progresso de migração**: 84% (27/32 testes)

## 11) Equivalência de Testes

Todos os 29 testes pytest são equivalentes funcionalmente aos testes Django correspondentes:

```
Django APITestCase (32 testes)
├── api/tests.py (2)
├── accounts/tests/test_api_isolation.py (4)
├── organizations/tests/test_api_isolation.py (7)
├── projects/tests/test_api_isolation.py (8)
├── data/tests/test_api_isolation.py (6) ← Fase 4
└── permissions/tests/test_api_isolation.py (5) ← Pendente

Pytest Suite (29 testes)
├── test_api_versioning_pytest.py (2)
├── test_api_compatibility_pytest.py (2)
├── test_accounts_isolation_pytest.py (4)
├── test_organizations_isolation_pytest.py (7)
├── test_projects_isolation_pytest.py (8) ← Fase 4
└── test_data_isolation_pytest.py (6) ← Fase 4
```

**Status**: ✅ 27 de 32 testes migrados com sucesso
