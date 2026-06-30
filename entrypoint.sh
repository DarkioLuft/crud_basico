#!/bin/bash
# ── Entrypoint do container Django ──────────────────────────────
# Executado toda vez que o container web sobe.
# Garante: banco pronto → migrations → seed (se vazio) → Gunicorn

set -e

echo "⏳ Aguardando o banco de dados ($DB_HOST:$DB_PORT) ficar pronto..."
while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 0.5
done
echo "✅ Banco de dados online!"

echo "📦 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "🔄 Aplicando migrations no banco de dados..."
python manage.py migrate --noinput

# Seed automático: popula dados iniciais apenas se o banco estiver vazio
# O comando é idempotente — se o user 'teste' já existir, não faz nada.
echo "🌱 Verificando dados iniciais..."
python manage.py seed_data --noinput

echo "🚀 Iniciando o Gunicorn..."
exec gunicorn core.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --access-logfile -