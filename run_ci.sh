#!/bin/bash
# Script para rodar a Integração Contínua (Testes + SonarQube)

set -e

echo "🚀 A iniciar o Pipeline de Integração Contínua (CI)..."

# 1. Levanta o SonarQube em background
echo "🐳 A levantar o SonarQube (porta 9000)..."
docker compose -f docker-compose.ci.yml up -d

# 2. Levanta a base de dados do docker-compose base para os testes
echo "🗄️ A levantar a Base de Dados de Teste..."
docker compose up -d db

echo "⏳ A aguardar a inicialização da base de dados..."
sleep 5

# 3. Executa os testes isolados num contentor efémero com o entrypoint bash
echo "🧪 A executar os 20 testes com pytest e a gerar estatísticas (coverage)..."
docker compose run --rm --entrypoint bash web -c "pip install pytest pytest-django pytest-cov && pytest crud/tests.py --ds=core.settings --cov=. --cov-report=xml"

echo "✅ Testes concluídos com sucesso! Relatório 'coverage.xml' gerado."

# 4. Envia a análise para o SonarQube automaticamente
echo "=========================================================="
echo "📊 FASE DE ANÁLISE DE QUALIDADE DE CÓDIGO (SONARQUBE)    "
echo "=========================================================="
echo "A enviar o código e as estatísticas de teste para o SonarQube..."

docker run --rm --network host \
  -e SONAR_HOST_URL='http://177.44.248.75:9000' \
  -e SONAR_TOKEN='sqp_6034f27c012bbc9620ed5e1d6eacfb11b8bb3905' \
  -v "$(pwd):/usr/src" \
  sonarsource/sonar-scanner-cli

echo "🧹 Limpando o banco de testes..."
docker compose stop db

echo "🎉 Pipeline CI finalizado! O relatório de qualidade já está disponível no SonarQube."