#!/usr/bin/env bash
# Salir inmediatamente si ocurre un error
set -o errexit

# Instalar dependencias
pip install -r requirements.txt

# Compilar Tailwind antes de recolectar los archivos estáticos
npm ci
npm run build:css

# Recolectar archivos estáticos para WhiteNoise
python manage.py collectstatic --no-input

# Aplicar migraciones a la base de datos
python manage.py migrate
