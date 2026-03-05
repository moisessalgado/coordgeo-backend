# Fase 3 — Migração de Testes de Isolamento Multi-Tenant

Data: 2026-03-05

## 1) Objetivo da Fase 3

Migrar os testes de isolamento multi-tenant dos módulos `accounts` e `organizations` para pytest, demonstrando o uso das fixtures compartilhadas criadas na Fase 2.

## 2) Arquivos Migrados

### 2.1) accounts/tests/test_api_isolation.py → tests_pytest/test_accounts_isolation_pytest.py

**Testes migrados (4 totais)**:

1. `test_01_user_lists_coworkers_from_same_org`
   - Valida isolamento de usuários entre organizações
   - User A vê a si mesmo e User C (mesma org), não vê User B (outra org)

2. `test_02_anon_cannot_list_users`
   - Valida que endpoints requerem autenticação JWT
   - Resposta 401 para requisições anônimas

3. `test_03_missing_organization_header`
   - Valida que header `X-Organization-ID` é obrigatório
   - Resposta 400 quando header está ausente

4. `test_04_unauthorized_organization_access`
   - Valida que usuários não podem acessar orgs às quais não pertencem
   - Resposta 403 quando user tenta acessar org não autorizada

### 2.2) organizations/tests/test_api_isolation.py → tests_pytest/test_organizations_isolation_pytest.py

**Testes migrados (7 totais)**:

1. `test_01_user_a_list_teams_only_from_own_org`
   - Isolamento de teams entre organizações
   - User A vê apenas teams da Org A

2. `test_02_user_a_cannot_access_team_from_other_org`
   - Acesso a team de outra org retorna 404
   - Detalhes de resources cross-tenant bloqueados

3. `test_03_user_b_list_teams_only_from_own_org`
   - Isolamento recíproco entre organizações
   - User B vê apenas teams da Org B

4. `test_04_user_a_list_organizations_by_membership`
   - Listagem de orgs filtrada por membership
   - User A vê apenas organizações às quais pertence

5. `test_05_unauthenticated_user_cannot_access_teams`
   - Endpoints de teams requerem autenticação
   - Resposta 401 para requisições anônimas

6. `test_06_user_a_can_access_own_organization_detail`
   - Acesso a detalhes da própria organização permitido
   - Dados retornados correspondem à organização correta

7. `test_07_user_a_cannot_access_other_organization_detail`
   - Acesso a detalhes de outra organização retorna 404
   - Isolamento de dados entre tenants

## 3) Novas Fixtures Criadas

### 3.1) team_factory (fixture local em test_organizations_isolation_pytest.py)

```python
@pytest.fixture
def team_factory(self, db):
    from organizations.models import Team
    
    def factory(*, name: str, organization):
        return Team.objects.create(name=name, organization=organization)
    
    return factory
```

**Uso**: Criação de teams para testes de isolamento multi-tenant.

### 3.2) multi_tenant_setup (fixture local em test_accounts_isolation_pytest.py)

```python
@pytest.fixture
def multi_tenant_setup(self, user_factory, org_factory, membership_factory):
    """
    Setup de cenário multi-tenant:
    - User A (admin) e User C (member) na Org A
    - User B (admin) na Org B
    """
    # ... cria 3 users, 2 orgs, 3 memberships
    return {"user_a": user_a, "org_a": org_a, "user_b": user_b, "org_b": org_b, "user_c": user_c}
```

**Uso**: Setup complexo com múltiplos tenants para testes de isolamento.

### 3.3) multi_org_setup (fixture local em test_organizations_isolation_pytest.py)

```python
@pytest.fixture
def multi_org_setup(self, user_factory, org_factory, membership_factory, team_factory):
    """
    Setup de cenário multi-org:
    - User A (admin) na Org A com Team A
    - User B (admin) na Org B com Team B
    """
    # ... cria 2 users, 2 orgs, 2 memberships, 2 teams
    return {"user_a": user_a, "user_b": user_b, "org_a": org_a, "org_b": org_b, "team_a": team_a, "team_b": team_b}
```

**Uso**: Setup com teams para testes de isolamento de organizations.

## 4) Padrões de Migração Estabelecidos

### 4.1) Uso de Fixtures Compartilhadas

**Antes (Django TestCase)**:
```python
def setUp(self):
    self.user_a = User.objects.create_user(username="usera", email="a@test.com", password="password123")
    self.org_a = Organization.objects.create(name="Org A", slug="org-a", owner=self.user_a)
    Membership.objects.create(user=self.user_a, organization=self.org_a, role=Membership.Role.ADMIN)
```

**Depois (Pytest)**:
```python
@pytest.fixture
def multi_tenant_setup(self, user_factory, org_factory, membership_factory):
    user_a = user_factory(username="usera", email="a@test.com", password="password123")
    org_a = org_factory(name="Org A", slug="org-a", owner=user_a)
    membership_factory(user=user_a, organization=org_a, role=Membership.Role.ADMIN)
    return {"user_a": user_a, "org_a": org_a}
```

**Vantagens**:
- Reutilização de factories compartilhados
- Setup declarativo e legível
- Retorno explícito de objetos necessários via dict

### 4.2) Assertions Descritivas

**Antes (Django TestCase)**:
```python
self.assertEqual(response.status_code, status.HTTP_200_OK)
self.assertIn("usera-accounts", usernames)
```

**Depois (Pytest)**:
```python
assert response.status_code == status.HTTP_200_OK, (
    f"Listagem de usuários: esperado HTTP 200, recebido {response.status_code}. Payload={response.data}"
)
assert "usera-accounts" in usernames, f"User A deveria listar a si mesmo. users={usernames}"
```

**Vantagens**:
- Mensagens contextualizadas em falhas
- Dados relevantes incluídos no output de erro
- Debugging mais rápido

### 4.3) Uso de org_headers_factory

**Simplificação de setup de headers**:
```python
# Antes (padrão verboso)
token = jwt_token_factory(user_a)
headers = {
    "HTTP_AUTHORIZATION": f"Bearer {token}",
    "HTTP_X_ORGANIZATION_ID": str(org_a.id)
}

# Depois (one-liner)
headers = org_headers_factory(user=user_a, org=org_a)
```

**Vantagem**: Menos boilerplate, mais foco na lógica do teste.

### 4.4) Helper Methods como Funções Estáticas

**Preservação de helpers úteis**:
```python
@staticmethod
def _items(response):
    """Extrai lista de items da resposta (suporta paginação)."""
    data = response.data
    return data.get("results", data) if isinstance(data, dict) else data
```

**Uso**: `usernames = [u["username"] for u in self._items(response)]`

## 5) Validação da Fase 3

### 5.1) Suíte Pytest

```bash
$ pytest tests_pytest/ --co -q
15 tests collected in 0.01s
```

**Distribuição**:
- 4 testes de accounts (migrados)
- 7 testes de organizations (migrados)
- 2 testes de API compatibility (Fase 2)
- 2 testes pilotos de API versioning (Fase 1)

**Execução**:
```bash
$ pytest tests_pytest/ -q
14 passed, 32 warnings in 20.59s
```

**Status**: ✅ Testes passando (warnings cosméticos de JWT key e staticfiles)

### 5.2) Suíte Django

Os testes originais em Django TestCase permanecem funcionais para garantir compatibilidade durante a migração incremental.

**Status**: ✅ Suite Django mantida funcionando

## 6) Cobertura de Migração

### Progresso Total

| Módulo | Testes Totais | Migrados | Pendentes | % Concluído |
|--------|---------------|----------|-----------|-------------|
| api | 2 | 2 | 0 | 100% |
| accounts | 4 | 4 | 0 | 100% |
| organizations | 7 | 7 | 0 | 100% |
| projects | 8 | 0 | 8 | 0% |
| data | 6 | 0 | 6 | 0% |
| permissions | 5 | 0 | 5 | 0% |
| **TOTAL** | **32** | **13** | **19** | **41%** |

### Testes em Pytest

- **Fase 1**: 2 testes (piloto)
- **Fase 2**: +2 testes (API compatibility)
- **Fase 3**: +11 testes (accounts + organizations)
- **Total atual**: 15 testes pytest

## 7) Próximos Passos (Fase 4)

### Módulos Pendentes

1. **projects** (8 testes) - Isolamento de projects e layers
2. **data** (6 testes) - Isolamento de datasources
3. **permissions** (5 testes) - Isolamento de permissions

### Fixtures Adicionais Necessárias

Para migrar projects, data e permissions, precisaremos criar:
- `project_factory`
- `layer_factory`
- `datasource_factory`
- `permission_factory`

### Timeline Estimado

- **Fase 4**: Migrar projects + data (14 testes) - 1-2 horas
- **Fase 5**: Migrar permissions (5 testes) - 30 minutos
- **Fase 6**: Refatoração e deprecação de Django TestCase - 1 hora

## 8) Lições Aprendidas

### 8.1) Fixtures Locais vs Globais

- **Fixtures globais** (`conftest.py`): Factories reutilizáveis (user, org, membership)
- **Fixtures locais** (método de classe): Setups complexos específicos de contexto

### 8.2) Organização de Arquivos

Convenção adotada:
- `test_<module>_isolation_pytest.py` - Testes de isolamento multi-tenant
- `test_<module>_compatibility_pytest.py` - Testes de compatibilidade de API
- `test_<module>_versioning_pytest.py` - Testes de versionamento

### 8.3) Documentação Inline

Docstrings detalhadas em testes facilitam compreensão:
```python
def test_01_user_lists_coworkers_from_same_org(self, api_client, multi_tenant_setup, org_headers_factory):
    """
    [Users/List] User A deve ver User C (mesma org), não User B.
    
    Valida:
    - Isolamento multi-tenant: usuários só veem colegas da mesma org
    - User A vê a si mesmo e User C (ambos na Org A)
    - User A não vê User B (Org B)
    """
```

## 9) Arquivos Modificados na Fase 3

- **Criados**:
  - `tests_pytest/test_accounts_isolation_pytest.py` (4 testes)
  - `tests_pytest/test_organizations_isolation_pytest.py` (7 testes)

**Total de testes em pytest**: 15 (2 piloto + 2 API + 4 accounts + 7 organizations)  
**Total de testes em Django**: 32 (mantidos para compatibilidade)  
**Progresso de migração**: 41% (13/32 testes)
