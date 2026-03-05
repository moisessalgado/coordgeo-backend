# Fase 0 — Inventário e Baseline de Testes (pré-migração para Pytest)

Data: 2026-03-05

## 1) Runner atual e stack de testes

- Runner principal atual: `python manage.py test` (Django Test Runner / unittest)
- Script auxiliar existente: `run_tests.py` (usa Django runner com `keepdb=True`)
- Framework de teste predominante no código: `rest_framework.test.APITestCase`
- Pytest **não** está presente em `requirements.txt` no estado atual

## 2) Arquivos de teste mapeados no backend

1. `api/tests.py`
2. `accounts/tests/test_api_isolation.py`
3. `organizations/tests/test_api_isolation.py`
4. `projects/tests/test_api_isolation.py`
5. `data/tests/test_api_isolation.py`
6. `permissions/tests/test_api_isolation.py`
7. `core/tests.py` (placeholder, sem cenários reais)
8. `test_endpoints.py` (script utilitário com funções, fora do padrão de discovery do unittest)

## 3) Inventário de casos (estático)

### Casos descobertos pelo runner Django (`manage.py test`)

- `api/tests.py`: 2 testes
- `accounts/tests/test_api_isolation.py`: 4 testes
- `organizations/tests/test_api_isolation.py`: 7 testes
- `projects/tests/test_api_isolation.py`: 8 testes
- `data/tests/test_api_isolation.py`: 6 testes
- `permissions/tests/test_api_isolation.py`: 5 testes

**Total descoberto pelo runner Django: 32 testes**

### Casos adicionais fora do discovery padrão

- `test_endpoints.py`: 4 funções `test_*` (executadas como script utilitário)

**Total de funções `test_*` no repositório: 36**

## 4) Classificação por tipo (alto nível)

- API / isolamento multi-tenant: maioria absoluta da suíte (`APITestCase`)
- Compatibilidade de versionamento de API: presente (`api/tests.py`)
- Testes de endpoint utilitários (script): presentes (`test_endpoints.py`)
- Unit tests puros: praticamente inexistentes
- Integração de ponta a ponta automatizada: hoje concentrada no script `scripts/smoke_api_integration.py`

## 5) Lacunas identificadas para migração completa

1. Suite está dividida entre testes descobertos por runner e scripts utilitários.
2. Há duplicidade de propósito entre `test_endpoints.py` e cenários de API já cobertos em `api/tests.py`.
3. Não há camada padronizada de fixtures/factories reutilizáveis.
4. `core/tests.py` está vazio (placeholder).

## 6) Baseline de execução (status funcional)

- Execução do runner Django confirma discovery de **32 testes**.
- Status funcional observado: suíte está passando no ambiente local.
- Observações recorrentes no ambiente:
  - warning de diretório estático ausente (`staticfiles.W004`)
  - warning de chave JWT curta para HMAC SHA-256

## 7) Critérios de sucesso para migração (definidos na Fase 0)

- Paridade de cenários: 32 testes descobertos devem existir em Pytest com mesmo comportamento.
- Scripts utilitários (`test_endpoints.py` e smoke) devem virar testes de integração/compatibilidade ou permanecer apenas como utilitários documentados.
- Adoção de fixtures compartilhadas para usuário/org/membership/token/header.
- CI rodando `pytest` como runner principal ao final da migração.

## 8) Próximo passo (Fase 1)

- Adicionar `pytest` e `pytest-django` sem quebrar `manage.py test`.
- Criar configuração mínima (`pytest.ini` ou equivalente) e um teste-piloto espelhando um caso atual de API.
- Definir convenções de markers (`unit`, `api`, `integration`, `slow`).
