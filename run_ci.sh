#!/bin/bash
# Script para rodar a Integração Contínua (Testes + Mess Detector + SonarQube)

set -e

echo "🚀 A iniciar o Pipeline de Integração Contínua (CI)..."

# 1. Levanta o SonarQube em background
echo "🐳 A levantar o SonarQube (porta 9000)..."
docker compose -f docker-compose.ci.yml up -d

echo "Preset do SonarQube"
# chmod +x setup_sonar.sh
# ./setup_sonar.sh

# 2. Levanta a base de dados do docker-compose base para os testes
echo "🗄️ A levantar a Base de Dados de Teste..."
docker compose up -d db

echo "⏳ A aguardar a inicialização da base de dados..."
sleep 5

# 3. Executa os testes + o Mess Detector (Pylint) num contentor efémero
#
#    IMPORTANTE: usamos "-v $(pwd):/app" para montar o código-fonte do host
#    dentro do contentor. Sem isso, os relatórios (coverage.xml,
#    pylint-report.txt, test-report.xml) são gerados na camada interna do
#    contentor e são perdidos quando ele é removido (--rm), nunca chegando
#    ao host para o sonar-scanner ler na fase seguinte.
echo "🧪 A executar os 20 testes com pytest e a gerar estatísticas (coverage)..."
docker compose run --rm -v "$(pwd):/app" --entrypoint bash web -c "
    pip install --quiet pytest pytest-django pytest-cov pylint pylint-django &&
    pytest crud/tests.py --ds=core.settings --cov=. --cov-report=xml --junitxml=test-report.xml -v &&
    echo '🧹 A executar o Mess Detector (Pylint) sobre crud/ e core/...' &&
    (pylint --rcfile=.pylintrc --output-format=parseable crud core | tee pylint-report.txt) || true
"

echo "✅ Testes concluídos! Relatórios gerados: coverage.xml, test-report.xml, pylint-report.txt"

# 4. Envia a análise para o SonarQube automaticamente
#    (cobertura de testes + estatísticas de execução + achados do Mess Detector)
echo "=========================================================="
echo "📊 FASE DE ANÁLISE DE QUALIDADE DE CÓDIGO (SONARQUBE)    "
echo "=========================================================="
echo "A enviar o código, os testes e o relatório do Mess Detector para o SonarQube..."

docker run --rm --network host \
  -e SONAR_HOST_URL='http://177.44.248.75:9000' \
  -e SONAR_TOKEN="$SONAR_TOKEN" \
  -v "$(pwd):/usr/src" \
  sonarsource/sonar-scanner-cli

echo "🧹 Limpando o banco de testes..."
docker compose stop db

echo "🎉 Pipeline CI finalizado! O relatório de qualidade (incluindo o Mess Detector) já está disponível no SonarQube."