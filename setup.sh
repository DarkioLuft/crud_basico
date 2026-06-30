#!/bin/bash
# ================================================================
# setup_vm.sh — Prepara a VM zerada (Ubuntu 24.04) para o projeto
# ================================================================
# Instala: Docker, Docker Compose, GitHub Actions Runner
# Clona o repositório e gera os arquivos .env
#
# Uso:  sudo bash setup_vm.sh
# ================================================================

set -e

# ── Cores para output ──────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✅]${NC} $1"; }
warn() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
info() { echo -e "${CYAN}[ℹ️]${NC} $1"; }

echo "========================================================"
echo "🚀 Setup da VM — CRUD de Receitas (GCS Task 2)"
echo "========================================================"

# ── Identifica o usuário alvo ──────────────────────────────────
TARGET_USER="univates"
if ! id "$TARGET_USER" &>/dev/null; then
    TARGET_USER="${SUDO_USER:-$USER}"
fi
TARGET_HOME=$(eval echo "~$TARGET_USER")
info "Usuário alvo: $TARGET_USER ($TARGET_HOME)"

# ── 1. Atualização do SO ──────────────────────────────────────
info "Atualizando pacotes do sistema..."
export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a
apt-get update && apt-get upgrade -y -q

# ── 2. Dependências básicas ───────────────────────────────────
info "Instalando utilitários..."
apt-get install -y -q \
    ca-certificates curl gnupg lsb-release git wget jq

# ── 3. Docker Engine + Compose ─────────────────────────────────
if command -v docker &>/dev/null; then
    warn "Docker já instalado: $(docker --version)"
else
    info "Instalando Docker..."
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc

    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
        tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update
    apt-get install -y -q \
        docker-ce docker-ce-cli containerd.io \
        docker-buildx-plugin docker-compose-plugin

    systemctl enable docker
    systemctl start docker
    log "Docker instalado com sucesso!"
fi

usermod -aG docker "$TARGET_USER"

# ── 4. Clone do repositório ───────────────────────────────────
TARGET_DIR="$TARGET_HOME/crud_basico"

if [ -d "$TARGET_DIR" ]; then
    warn "Diretório $TARGET_DIR já existe. Atualizando..."
    cd "$TARGET_DIR" && git pull origin main || true
else
    info "Clonando repositório..."
    git clone https://github.com/DarkioLuft/crud_basico.git "$TARGET_DIR"
fi

cd "$TARGET_DIR"

# ── 5. Gerar arquivos .env ────────────────────────────────────
info "Gerando arquivos de configuração (.env)..."

cat > "$TARGET_DIR/.env" << 'EOF'
DEBUG=True
SECRET_KEY=chave-secreta-ci-testes
ALLOWED_HOSTS=*
DB_NAME=crud_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
WEB_PORT=8000
EOF

cat > "$TARGET_DIR/.env.homolog" << 'EOF'
DEBUG=True
SECRET_KEY=chave-secreta-homologacao
ALLOWED_HOSTS=*
DB_NAME=homolog_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db_homolog
DB_PORT=5432
WEB_PORT=8001
EOF

cat > "$TARGET_DIR/.env.prod" << 'EOF'
DEBUG=False
SECRET_KEY=chave-secreta-producao-super-segura
ALLOWED_HOSTS=*
DB_NAME=prod_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db_prod
DB_PORT=5432
WEB_PORT=8000
EOF

log "Arquivos .env gerados!"

# ── 6. Permissões ─────────────────────────────────────────────
chmod +x "$TARGET_DIR/entrypoint.sh"
chmod +x "$TARGET_DIR/pipeline.sh" 2>/dev/null || true
chown -R "$TARGET_USER:$TARGET_USER" "$TARGET_DIR"

# ── 7. GitHub Actions Self-Hosted Runner ──────────────────────
RUNNER_DIR="$TARGET_HOME/actions-runner"

if [ -d "$RUNNER_DIR" ] && [ -f "$RUNNER_DIR/run.sh" ]; then
    warn "GitHub Actions Runner já instalado em $RUNNER_DIR"
else
    info "Instalando GitHub Actions Self-Hosted Runner..."

    mkdir -p "$RUNNER_DIR"
    cd "$RUNNER_DIR"

    # Baixa a última versão do runner para Linux x64
    RUNNER_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | jq -r '.tag_name' | sed 's/v//')
    curl -o actions-runner-linux-x64.tar.gz -L \
        "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"

    tar xzf actions-runner-linux-x64.tar.gz
    rm actions-runner-linux-x64.tar.gz

    chown -R "$TARGET_USER:$TARGET_USER" "$RUNNER_DIR"

    log "Runner baixado (v$RUNNER_VERSION)!"
fi

# ── 8. Resumo final ───────────────────────────────────────────
echo ""
echo "========================================================"
echo -e "${GREEN}🎉 SETUP DA VM CONCLUÍDO COM SUCESSO!${NC}"
echo "========================================================"
echo ""
echo "📋 PRÓXIMOS PASSOS (executar como $TARGET_USER):"
echo ""
echo "  1. Recarregue as permissões do Docker:"
echo "     su - $TARGET_USER"
echo ""
echo "  2. Configure o GitHub Runner (executar UMA vez):"
echo "     cd ~/actions-runner"
echo "     ./config.sh --url https://github.com/DarkioLuft/crud_basico \\"
echo "                 --token <SEU_TOKEN_AQUI>"
echo ""
echo "     Para obter o token, acesse:"
echo "     GitHub → Repositório → Settings → Actions → Runners → New self-hosted runner"
echo ""
echo "  3. Instale o runner como serviço (roda em background):"
echo "     sudo ./svc.sh install $TARGET_USER"
echo "     sudo ./svc.sh start"
echo ""
echo "  4. Teste subindo Homologação manualmente:"
echo "     cd ~/crud_basico"
echo "     docker compose -f docker-compose.homolog.yml --env-file .env.homolog up -d --build"
echo ""
echo "========================================================"