**README**

Setup do GeoDjango para manipulação de PMTiles usando Maplibre GL

Instale as libs geoespaciais:
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
postgis \
```
Entre no postgresql:
```bash
sudo -u postgres psql
```

Comandos usados na criação do banco geodjango:
```bash
CREATE DATABASE geodjango;
\c geodjango
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;

CREATE USER django WITH PASSWORD 'xangomocama5';
GRANT ALL PRIVILEGES ON DATABASE geodjango TO django;
GRANT CREATE ON SCHEMA public TO django;
GRANT CONNECT ON DATABASE geodjango TO django;
GRANT USAGE, CREATE ON SCHEMA public TO django;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO django;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO django;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO django;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO django;
```

Criação do projeto Django
```bash
django-admin startproject config .
python manage.py startapp core
```
Geração do PMTiles
```bash
tippecanoe \
  -o car_sc.pmtiles \
  -Z5 -z15 \
  --buffer=127 \
  --detect-shared-borders \
  --coalesce-densest-as-needed \
  --drop-densest-as-needed \
  --no-tile-size-limit \
  car_sc.geojson
  ```
Usando o Gunicorn para servir o PMTiles (Django runserver não suporta HTTP Range header para servir o pmtiles)
```bash
gunicorn config.wsgi:application --bind 127.0.0.1:8000
```

API REST usando o DRF
```bash
pip install djangorestframework
```
