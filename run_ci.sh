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

# 3. Executa os testes isolados num contentor efémero
# Instalamos o pytest e pytest-cov on-the-fly para não "sujar" a imagem de produção
echo "🧪 A executar os 20 testes com pytest e a gerar estatísticas (coverage)..."
docker compose run --rm web bash -c "pip install pytest pytest-django pytest-cov && pytest crud/tests.py --ds=core.settings --cov=. --cov-report=xml"

echo "✅ Testes concluídos com sucesso! Relatório 'coverage.xml' gerado."

# 4. Instruções para o Sonar Scanner
echo "=========================================================="
echo "📊 FASE DE ANÁLISE DE QUALIDADE DE CÓDIGO (SONARQUBE)    "
echo "=========================================================="
echo "O servidor do SonarQube está a iniciar. Pode demorar 1-2 minutos."
echo "1. Aceda a http://SEU_IP:9000 no navegador."
echo "2. Inicie sessão com admin / admin (e altere a palavra-passe)."
echo "3. Crie um projeto manual e gere um Token de acesso."
echo "4. Para enviar a análise, execute o seguinte comando no terminal:"
echo ""
echo "docker run --rm --network host -e SONAR_HOST_URL='http://localhost:9000' -e SONAR_TOKEN='COLOQUE_O_SEU_TOKEN_AQUI' -v \"\$(pwd):/usr/src\" sonarsource/sonar-scanner-cli"
echo "=========================================================="