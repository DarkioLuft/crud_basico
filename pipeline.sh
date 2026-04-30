#!/bin/bash
# Pipeline Semi-Automatizado de Deploy (CI/CD)

# set -e garante que o script pare imediatamente se qualquer comando falhar (como o run_ci.sh)
set -e

COMMAND=$1

case "$COMMAND" in
    "deploy-homolog")
        echo "=========================================================="
        echo "🚀 Iniciando Deploy em HOMOLOGAÇÃO"
        echo "=========================================================="
        
        echo "1️⃣  Atualizando o código-fonte (Git Pull)..."
        git pull origin main || echo "Git pull ignorado."

        echo "2️⃣  Executando testes automatizados e SonarQube (CI)..."
        # Se o run_ci.sh falhar, o set -e fará com que o pipeline.sh aborte aqui mesmo
        bash ./run_ci.sh

        echo "3️⃣  Construindo e subindo o ambiente de Homologação..."
        # O build cria a imagem crud_basico:homolog que será usada depois na produção
        docker compose -f docker-compose.homolog.yml --env-file .env.homolog up -d --build
        
        echo "✅ HOMOLOGAÇÃO ONLINE! Acesse: http://SEU_IP:8001"
        ;;
        
    "deploy-prod")
        echo "=========================================================="
        echo "🚀 Iniciando Deploy em PRODUÇÃO"
        echo "=========================================================="
        
        echo "1️⃣  Promovendo a imagem de Homologação para Produção..."
        docker tag crud_basico:homolog crud_basico:prod

        echo "2️⃣  Subindo o ambiente de Produção..."
        docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
        
        echo "✅ PRODUÇÃO ONLINE! Acesse: http://SEU_IP:8000"
        ;;
        
    *)
        echo "⚠️  Comando inválido."
        echo "Uso correto:"
        echo "  ./pipeline.sh deploy-homolog   -> Roda CI, Testes e sobe ambiente 8001"
        echo "  ./pipeline.sh deploy-prod      -> Promove a imagem e sobe ambiente 8000"
        ;;
esac