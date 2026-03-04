# 📚 Documentação coordgeo

Bem-vindo à documentação técnica do **coordgeo** - plataforma SaaS multi-tenant para gestão de dados geoespaciais.

Este guia cobre a arquitetura, recursos implementados, padrões de segurança e guia de API.

## 📖 Índice

### 1️⃣ [Visão Geral da Arquitetura](./architecture.md)
Compreenda a estrutura de camadas da plataforma:
- Diagrama de fluxo de requests
- Componentes principais (API, ViewSets, ORM, PostGIS)
- Fluxo de autenticação JWT
- Decisões arquiteturais

### 2️⃣ [Isolamento Multi-Tenant](./multi-tenancy.md)
Como garantimos isolamento completo entre organizações:
- Modelo de dados com `Organization` como raiz
- Permission class `IsOrgMember` para validação
- Padrões de filtering em ViewSets
- Enforcement de segurança em `perform_create()`
- Testes de isolamento obrigatórios
- Checklist pré-merge

### 3️⃣ [Guia de API REST](./api-guide.md)
Referência completa dos endpoints disponíveis:
- `/api/users/` - Gestão de usuários
- `/api/organizations/` - Gestão de organizações
- `/api/memberships/` - Memberships em orgs
- `/api/teams/` - Times dentro de orgs
- `/api/projects/` - Projetos geoespaciais
- `/api/layers/` - Camadas dentro de projetos
- `/api/datasources/` - Fontes de dados compartilhadas
- `/api/permissions/` - Permissões granulares

### 4️⃣ [Requisitos Funcionais e de Segurança](./requirements.md) *(em progresso)*
Status de implementação de requisitos.

---

## 📊 Diagramas Visuais

- **[Modelo de Dados ER](./diagrams/data-model.png)** - Diagrama automático de relacionamentos entre modelos (gerado com django-extensions)
- **[Modelo de Dados Mermaid](./architecture.md#-modelo-de-dados)** - Visualização interativa em Mermaid

---

## ⚡ Quick Navigation

**Implementando uma nova feature?**
→ Leia [Isolamento Multi-Tenant](./multi-tenancy.md) para padrões de segurança

**Integrando com a API?**
→ Consulte [Guia de API REST](./api-guide.md)

**Entendendo a estrutura?**
→ Comece na [Visão Geral da Arquitetura](./architecture.md)

---

## 📊 Stack Tecnológico

| Camada | Tecnologia |
|--------|-----------|
| **Frontend** | MapLibre GL JS, HTML5 |
| **Backend** | Django 4.2+ , Django REST Framework |
| **Database** | PostgreSQL 13+ + PostGIS |
| **Geospatial** | GeoDjango, PostGIS, PMTiles, MVT |
| **Auth** | JWT (djangorestframework-simplejwt) |
| **Testing** | Django TestCase, pytest |

---

## 🔐 Pilares de Segurança

✅ **Isolamento de dados** - Organization como boundary  
✅ **Autenticação JWT** - Email-based custom User model  
✅ **RBAC** - Roles (MEMBER/ADMIN) por membership  
✅ **Header validation** - X-Organization-ID obrigatório  
✅ **Context enforcement** - isOrgMember permission class  
✅ **Query filtering** - Todos ViewSets filtram por org  
✅ **Spatial indexes** - Performance em geometrias  
✅ **Testes de isolamento** - Coverage multi-tenant  

---

## 🚀 Começando

### Requisitos
- Python 3.10+
- PostgreSQL 13+ com PostGIS
- WSL2 (Windows) ou Linux/macOS

### Instalação Rápida

```bash
# Clone e setup
git clone https://github.com/moisessalgado/coordgeo.git
cd coordgeo
python -m venv venv
source venv/bin/activate  # WSL/Linux/macOS

# Instale deps
pip install -r requirements.txt

# Configure banco
cp .env.example .env
# Edite .env com credenciais PostgreSQL

# Run migrations
./venv/bin/python manage.py migrate

# Teste
./venv/bin/python manage.py test -v 2
```

### Servidor local

```bash
./venv/bin/python manage.py runserver
# Acesse: http://localhost:8000
```

---

## 📁 Estrutura de Pastas

```
coordgeo/
├── docs/                     # 📄 Esta documentação
├── accounts/                 # 👤 Custom User model, auth
├── organizations/            # 🏢 Org, Membership, Teams
├── projects/                 # 🗺️ Projects, Layers (geospatial)
├── data/                     # 📊 Datasources
├── permissions/              # 🔒 Granular permissions
├── core/                     # 🔧 Utilidades compartilhadas
├── api/                      # 🔌 Router DRF
├── config/                   # ⚙️ Settings, URLs, WSGI
└── static/                   # 📦 PMTiles, assets
```

---

## 🤝 Contribuindo

Ao adicionar novos features:

1. **Sempre filtre by `request.active_organization`** em ViewSets
2. **Use `request.active_organization` em `perform_create()`** - NUNCA confie no client
3. **Inclua `IsOrgMember`** nas permission_classes
4. **Escreva testes de isolamento** (veja [Multi-tenancy](./multi-tenancy.md#-testes-obrigatórios))
5. **Valide header e membership** via permission class

Veja [Security Checklist](./multi-tenancy.md#-pre-merge-security-checklist) antes de fazer PR.

---

## 📞 Referências Rápidas

- **Permissões**: [organizations/permissions.py](../organizations/permissions.py)
- **Models principais**: [organizations/models.py](../organizations/models.py), [projects/models.py](../projects/models.py), [data/models.py](../data/models.py)
- **API Router**: [api/urls.py](../api/urls.py)
- **Testes**: [accounts/tests/test_api_isolation.py](../accounts/tests/test_api_isolation.py)

---

**Last updated**: March 2025  
**Status**: Production-Ready
