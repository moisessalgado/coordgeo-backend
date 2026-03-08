# coordgeo

**Plataforma SaaS multi-tenant para gestão de dados geoespaciais com Django, GeoDjango e PostGIS.**

coordgeo é uma solução enterprise-ready para análise, visualização e colaboração de dados geoespaciais em tempo real, com suporte a múltiplas organizações, permissões granulares e integração com MapLibre GL.

## ✨ Features

- 🏢 **Multi-tenant SaaS**: Isolamento completo de dados entre organizações
- 🗺️ **Geospatial-first**: PostGIS, GeoDjango, PMTiles, MVT e suporte a múltiplas fontes de dados
- 🔐 **Segurança enterprise**: JWT authentication, RBAC, isolamento de contexto por organização
- 💡 **API REST moderna**: Django REST Framework com paginação, filtros e ordenação
- 🧪 **Testes automatizados**: Cobertura completa com foco em isolamento multi-tenant
- 🚀 **Production-ready**: Gunicorn, PostGIS, stack otimizado para geoespacial
- 📚 **Documentação clara**: Guia arquitetural detalhado para desenvolvimento

## 🚀 Quick Start

### Requisitos

- Python 3.10+
- PostgreSQL 13+ com PostGIS
- WSL2 (Windows) ou Linux/macOS

### Instalação

1. Clone o repositório:
```bash
git clone https://github.com/moisessalgado/coordgeo.git
cd coordgeo/coordgeo-backend
```

2. Crie um virtualenv:
```bash
python -m venv venv
source venv/bin/activate  # WSL/Linux/macOS
# ou
venv\Scripts\activate  # Windows
```

3. Instale dependências:
```bash
pip install -r requirements.txt
```

4. Configure o arquivo `.env`:
```bash
cp .env.example .env
# Edite .env com suas credenciais
# Windows (PowerShell)
copy .env.example .env
```

5. Execute as migrações:
```bash
python manage.py migrate
```

6. Inicie o servidor:
```bash
python manage.py runserver
```

## 📖 Documentação

Veja a documentação técnica em [`docs/`](docs/) para:
- Padrões de isolamento multi-tenant
- Contexto ativo de organização
- Regras de performance geoespacial
- Testes obrigatórios e security checklist

## 🧪 Testes

```bash
# Executar todos os testes
python manage.py test -v 2

# Ou usar o script
./venv/bin/python run_tests.py
```

## 🏗️ Arquitetura

**Stack técnico:**
- Backend: Django + Django REST Framework
- Banco: PostgreSQL + PostGIS
- Autenticação: JWT (djangorestframework-simplejwt)
- Frontend: MapLibre GL
- Geoespacial: GeoDjango, PMTiles, MVT
- Servidor: Gunicorn (production)

**Multi-tenancy:**
- `Organization` como unidade de isolamento
- `Membership` para controle de acesso
- Header `X-Organization-ID` para contexto ativo
- Permission class `IsOrgMember` para validação de contexto ativo

**Versionamento da API:**
- Prefixo canônico: `/api/v1/`
- Não há alias legado `/api/` no roteamento atual

## 🔧 Setup da Database (PostgreSQL + PostGIS)

### Instalar dependências do sistema

```bash
sudo apt install -y \
binutils \
libproj-dev \
gdal-bin \
libgdal-dev \
libgeos-dev \
libpq-dev \
postgresql \
postgresql-contrib \
postgis
```

### Criar database e usuário

```bash
sudo -u postgres psql
```

Dentro do psql:
```sql
CREATE DATABASE geodjango;
\c geodjango
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;

CREATE USER django WITH PASSWORD 'sua_senha_segura';
GRANT ALL PRIVILEGES ON DATABASE geodjango TO django;
GRANT CREATE ON SCHEMA public TO django;
GRANT CONNECT ON DATABASE geodjango TO django;
GRANT USAGE, CREATE ON SCHEMA public TO django;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO django;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO django;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO django;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO django;
```

## 📦 Gerar PMTiles com Tippecanoe

Para datasets geoespaciais grandes, use tippecanoe:

```bash
tippecanoe \
  -o output.pmtiles \
  -Z5 -z15 \
  --buffer=127 \
  --detect-shared-borders \
  --coalesce-densest-as-needed \
  --drop-densest-as-needed \
  --no-tile-size-limit \
  input.geojson
```

**Importante**: Use Gunicorn em produção para servir PMTiles, pois o servidor de desenvolvimento do Django não suporta HTTP Range headers necessários para streaming eficiente de tiles.

```bash
gunicorn config.wsgi:application --bind 127.0.0.1:8000
```

## 🔐 Segurança

- Todas as credenciais em variáveis de ambiente (`.env`)
- Isolamento de dados por organização
- JWT com `SIMPLE_JWT` explícito (`access=5m`, `refresh=1d`)
- RBAC (Role-Based Access Control)
- Testes de isolamento multi-tenant

Veja o checklist em [`docs/multi-tenancy.md`](docs/multi-tenancy.md) antes de fazer deploy.

## 🤝 Contribuindo

1. Crie uma feature branch: `git checkout -b feature/sua-feature`
2. Commit em português: `git commit -m "feat: descrição da feature"`
3. Push e abra um Pull Request
4. Garanta que os testes passem: `python manage.py test -v 2`

## 📝 Licença

MIT

## 👤 Autor

**Moises Salgado**  
GitHub: [@moisessalgado](https://github.com/moisessalgado)
