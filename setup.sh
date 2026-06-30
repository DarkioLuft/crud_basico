#!/bin/bash
# ================================================================
# setup_vm.sh — Prepara a VM zerada (Ubuntu 24.04) para o projeto
# ================================================================
# Instala Docker, clona o repo, gera os .env, instala o Runner
# e configura tudo automaticamente.
#
# Uso:  sudo bash setup_vm.sh
# ================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✅]${NC} $1"; }
warn() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
info() { echo -e "${CYAN}[ℹ️]${NC} $1"; }
erro() { echo -e "${RED}[❌]${NC} $1"; }

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

# ══════════════════════════════════════════════════════
# FASE 1: SISTEMA E DOCKER
# ══════════════════════════════════════════════════════

info "1/6 — Atualizando pacotes do sistema..."
export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a
apt-get update -qq && apt-get upgrade -y -qq

info "2/6 — Instalando utilitários..."
apt-get install -y -qq \
    ca-certificates curl gnupg lsb-release git wget jq > /dev/null 2>&1

if command -v docker &>/dev/null; then
    warn "Docker já instalado: $(docker --version)"
else
    info "3/6 — Instalando Docker..."
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc

    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
        tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update -qq
    apt-get install -y -qq \
        docker-ce docker-ce-cli containerd.io \
        docker-buildx-plugin docker-compose-plugin > /dev/null 2>&1

    systemctl enable docker
    systemctl start docker
    log "Docker instalado com sucesso!"
fi

usermod -aG docker "$TARGET_USER"
log "3/6 — Docker OK"

# ══════════════════════════════════════════════════════
# FASE 2: CLONE E CONFIGURAÇÃO
# ══════════════════════════════════════════════════════

TARGET_DIR="$TARGET_HOME/crud_basico"

if [ -d "$TARGET_DIR" ]; then
    warn "Diretório $TARGET_DIR já existe. Atualizando..."
    cd "$TARGET_DIR" && git pull origin main || true
else
    info "4/6 — Clonando repositório..."
    git clone https://github.com/DarkioLuft/crud_basico.git "$TARGET_DIR"
fi

cd "$TARGET_DIR"

info "5/6 — Gerando arquivos .env..."

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
SESSION_COOKIE_NAME=sessionid_homolog
CSRF_COOKIE_NAME=csrftoken_homolog
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
SESSION_COOKIE_NAME=sessionid_prod
CSRF_COOKIE_NAME=csrftoken_prod
EOF

chmod +x "$TARGET_DIR/entrypoint.sh" 2>/dev/null || true
chmod +x "$TARGET_DIR/pipeline.sh" 2>/dev/null || true
chown -R "$TARGET_USER:$TARGET_USER" "$TARGET_DIR"

log "5/6 — Repositório e .env prontos"

# ══════════════════════════════════════════════════════
# FASE 3: GITHUB ACTIONS RUNNER (INTERATIVO)
# ══════════════════════════════════════════════════════

RUNNER_DIR="$TARGET_HOME/actions-runner"

info "6/6 — Configurando GitHub Actions Runner..."

if [ -d "$RUNNER_DIR" ] && [ -f "$RUNNER_DIR/run.sh" ]; then
    warn "Runner já baixado em $RUNNER_DIR"
else
    mkdir -p "$RUNNER_DIR"
    cd "$RUNNER_DIR"

    RUNNER_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | jq -r '.tag_name' | sed 's/v//')
    info "Baixando runner v$RUNNER_VERSION..."
    curl -sL -o actions-runner-linux-x64.tar.gz \
        "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
    tar xzf actions-runner-linux-x64.tar.gz
    rm actions-runner-linux-x64.tar.gz
    chown -R "$TARGET_USER:$TARGET_USER" "$RUNNER_DIR"
    log "Runner baixado!"
fi

cd "$RUNNER_DIR"

echo ""
echo "========================================================"
echo -e "${BOLD}🔑 AÇÃO NECESSÁRIA: Cole o token do GitHub Actions${NC}"
echo "========================================================"
echo ""
echo "  1. Abra no navegador:"
echo -e "     ${CYAN}https://github.com/DarkioLuft/crud_basico/settings/actions/runners/new${NC}"
echo ""
echo "  2. Copie o token que aparece no campo './config.sh --token ...'"
echo ""
echo -e "  ${YELLOW}(O token expira em ~1 hora)${NC}"
echo ""

# ── Leitura do token ───────────────────────────────────
while true; do
    read -rp "  Cole o token aqui: " RUNNER_TOKEN
    RUNNER_TOKEN=$(echo "$RUNNER_TOKEN" | xargs)

    if [ -z "$RUNNER_TOKEN" ]; then
        erro "Token vazio. Tente novamente."
        continue
    fi

    if [ ${#RUNNER_TOKEN} -lt 10 ]; then
        erro "Token muito curto. Verifique e cole novamente."
        continue
    fi

    break
done

echo ""
info "Configurando o runner..."

# Remove configuração anterior se existir
if [ -f "$RUNNER_DIR/.runner" ]; then
    warn "Removendo configuração anterior do runner..."
    sudo -u "$TARGET_USER" "$RUNNER_DIR/config.sh" remove --token "$RUNNER_TOKEN" 2>/dev/null || true
fi

# Configura o runner como o usuário alvo
sudo -u "$TARGET_USER" "$RUNNER_DIR/config.sh" \
    --url "https://github.com/DarkioLuft/crud_basico" \
    --token "$RUNNER_TOKEN" \
    --name "vm-univates" \
    --labels "self-hosted,Linux,X64" \
    --work "_work" \
    --unattended \
    --replace

if [ $? -ne 0 ]; then
    erro "Falha ao configurar o runner. Verifique o token e tente novamente."
    exit 1
fi

log "Runner configurado!"

# ── Instalar e iniciar como serviço ────────────────────
info "Instalando runner como serviço do sistema..."

"$RUNNER_DIR/svc.sh" stop 2>/dev/null || true
"$RUNNER_DIR/svc.sh" uninstall 2>/dev/null || true

"$RUNNER_DIR/svc.sh" install "$TARGET_USER"
"$RUNNER_DIR/svc.sh" start

sleep 3

echo ""
echo "========================================================"
echo -e "${GREEN}🎉 SETUP COMPLETO!${NC}"
echo "========================================================"
echo ""

echo -e "${CYAN}── Status do Runner ──${NC}"
"$RUNNER_DIR/svc.sh" status
echo ""

echo -e "${CYAN}── Status do Docker ──${NC}"
docker --version
echo ""

echo -e "${CYAN}── Containers rodando ──${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "(nenhum)"
echo ""

echo "========================================================"
echo -e "${BOLD}📋 PRÓXIMOS PASSOS:${NC}"
echo ""
echo "  1. Verifique o runner no GitHub:"
echo -e "     ${CYAN}Settings → Actions → Runners → deve estar 'Idle'${NC}"
echo ""
echo "  2. Suba Homologação via GitHub Actions:"
echo -e "     ${CYAN}Actions → CI/CD Pipeline → Run workflow → homolog${NC}"
echo ""
echo "  3. Suba Produção via GitHub Actions:"
echo -e "     ${CYAN}Actions → CI/CD Pipeline → Run workflow → prod${NC}"
echo "========================================================"