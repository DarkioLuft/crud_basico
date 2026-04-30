#!/bin/bash
# Este script roda toda vez que o container web subir.

set -e

echo "⏳ Aguardando o banco de dados ($DB_HOST:$DB_PORT) ficar pronto..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.5
done
echo "✅ Banco de dados online!"

echo "📦 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "🔄 Aplicando migrations no banco de dados..."
python manage.py migrate --noinput

echo "🚀 Iniciando o Gunicorn..."
# Inicia a aplicação vinculando a porta 8000 e permitindo a leitura de logs de acesso
exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3 --access-logfile -