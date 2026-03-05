# Fase 2 — Fixtures Compartilhados e Template de Migração

Data: 2026-03-05

## 1) Objetivo da Fase 2

Estabelecer infraestrutura de fixtures reutilizáveis e criar um template de migração através da conversão dos testes de `api/tests.py` para pytest.

## 2) Fixtures criados em `tests_pytest/conftest.py`

### 2.1) Fixtures de Modelos (Factories)

#### `user_factory(db)`
- **Propósito**: Criar instâncias de usuário para testes
- **Parâmetros**: `username`, `email`, `password` (default: `"testpass123"`)
- **Retorna**: Instância de `User`
- **Uso**:
  ```python
  user = user_factory(username="alice", email="alice@test.com")
  ```

#### `org_factory(db, user_factory)`
- **Propósito**: Criar instâncias de organização
- **Parâmetros**: `name`, `slug`, `owner`, `org_type`, `plan`, `description`
- **Retorna**: Instância de `Organization`
- **Uso**:
  ```python
  owner = user_factory(username="owner", email="owner@test.com")
  org = org_factory(name="My Org", slug="my-org", owner=owner)
  ```

#### `membership_factory(db)`
- **Propósito**: Criar memberships (relacionamento user-org)
- **Parâmetros**: `user`, `organization`, `role` (default: `Membership.Role.MEMBER`)
- **Retorna**: Instância de `Membership`
- **Uso**:
  ```python
  membership = membership_factory(user=user, organization=org, role="admin")
  ```

### 2.2) Fixtures de Autenticação

#### `jwt_token_factory()`
- **Propósito**: Gerar tokens JWT para autenticação
- **Parâmetros**: `user`
- **Retorna**: String do access token JWT
- **Uso**:
  ```python
  token = jwt_token_factory(user)
  ```

#### `org_headers_factory(jwt_token_factory)`
- **Propósito**: Gerar headers HTTP completos com autenticação e org scope
- **Parâmetros**: `user`, `org`
- **Retorna**: Dict com headers `HTTP_AUTHORIZATION` e `HTTP_X_ORGANIZATION_ID`
- **Uso**:
  ```python
  headers = org_headers_factory(user=user, org=org)
  response = api_client.get("/api/v1/users/", **headers)
  ```

### 2.3) Fixtures de Cliente

#### `api_client()`
- **Propósito**: Cliente DRF para testes de API
- **Retorna**: Instância de `rest_framework.test.APIClient`
- **Uso**:
  ```python
  response = api_client.get("/api/v1/users/", **headers)
  ```

## 3) Pytest Markers Registrados

Em `pytest.ini`, foram registrados os seguintes markers:

- **`@pytest.mark.unit`**: Testes unitários puros (funções, modelos, utilidades)
- **`@pytest.mark.api`**: Testes de endpoints de API REST
- **`@pytest.mark.integration`**: Testes de integração entre componentes
- **`@pytest.mark.slow`**: Testes que levam tempo significativo para executar

**Uso**:
```python
@pytest.mark.api
class TestAPIVersioningCompatibility:
    def test_token_endpoint_available_on_v1_only(self, api_client, setup_user_and_org):
        # ...
```

## 4) Template de Migração

### 4.1) Arquivo Criado: `tests_pytest/test_api_compatibility_pytest.py`

Migração completa de `api/tests.py` (Django TestCase) → pytest.

**Mudanças principais**:

#### Django TestCase (antes):
```python
class APIVersioningCompatibilityTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(...)
        self.organization = self.user.owned_organizations.create(...)
        Membership.objects.get_or_create(...)

    def test_token_endpoint_available_on_v1_only(self):
        payload = {...}
        response_v1 = self.client.post("/api/v1/token/", payload, format="json")
        self.assertEqual(response_v1.status_code, status.HTTP_200_OK)
        self.assertIn("access", response_v1.data)
```

#### Pytest (depois):
```python
@pytest.mark.api
class TestAPIVersioningCompatibility:
    @pytest.fixture
    def setup_user_and_org(self, user_factory, org_factory, membership_factory):
        user = user_factory(username="version-user", email="version-user@example.com")
        org = org_factory(name="Version Org", slug="version-org", owner=user)
        membership_factory(user=user, organization=org, role=Membership.Role.ADMIN)
        return {"user": user, "org": org}

    def test_token_endpoint_available_on_v1_only(self, api_client, setup_user_and_org):
        payload = {...}
        response_v1 = api_client.post("/api/v1/token/", payload, format="json")
        
        assert response_v1.status_code == status.HTTP_200_OK
        assert "access" in response_v1.data
```

**Padrão de fixtures locais**:
- Fixture `setup_user_and_org` como método da classe de teste
- Retorna dict com objetos necessários (`{"user": user, "org": org}`)
- Acesso via `setup_user_and_org["user"]` no teste

## 5) Validação da Fase 2

### 5.1) Suíte Pytest
```bash
$ pytest tests_pytest/ -v
============================= 4 passed, 6 warnings in 4.78s ==============================
```

**Status**: ✅ 4 testes passando (2 originais + 2 migrados de api/tests.py)

### 5.2) Suíte Django
```bash
$ python manage.py test api.tests accounts.tests organizations.tests projects.tests data.tests permissions.tests --keepdb
Ran 24 tests in 31.815s
OK
```

**Status**: ✅ Suite Django permanece funcional (compatibilidade mantida)

### 5.3) Remoção de Warnings
- Warning `Unknown pytest.mark.api` foi eliminado com registro de markers
- Warnings restantes são cosméticos (staticfiles, JWT key length)

## 6) Impacto

### 6.1) Fixtures Reutilizáveis
- 6 fixtures compartilhados disponíveis em `conftest.py`
- Eliminam duplicação de código de setup em testes futuros
- Padrão de factory facilita criação de dados de teste

### 6.2) Template Estabelecido
- `test_api_compatibility_pytest.py` serve como referência para futuras migrações
- Demonstra padrão de fixture local (método de classe)
- Mostra uso de markers e assertions pytest

### 6.3) Infraestrutura de Testing
- Markers registrados permitem execução seletiva: `pytest -m api`
- Ambas suítes (pytest e Django) funcionais lado a lado
- Caminho claro para migração incremental

## 7) Próximos Passos (Fase 3)

- Migrar `accounts/tests/test_api_isolation.py` (4 testes)
- Migrar `organizations/tests/test_api_isolation.py` (7 testes)
- Criar fixtures adicionais conforme necessidade (project_factory, datasource_factory, etc.)
- Refinar padrões de teste baseado em experiência com migração de testes de isolamento multi-tenant

## 8) Arquivos Modificados na Fase 2

- **Criados**:
  - `tests_pytest/test_api_compatibility_pytest.py` (2 testes migrados)
  
- **Modificados**:
  - `tests_pytest/conftest.py` (6 fixtures adicionados)
  - `pytest.ini` (4 markers registrados)

**Total de testes em pytest**: 4 (2 piloto + 2 migrados)  
**Total de testes em Django**: 32 (mantidos para compatibilidade)
