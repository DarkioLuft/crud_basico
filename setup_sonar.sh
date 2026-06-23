#!/bin/bash
# ============================================================
# setup_sonar.sh
# Automatiza o "primeiro login" do SonarQube:
#   1) Espera o servidor ficar UP
#   2) Troca a senha padrão admin/admin (exigido pelo Sonar)
#   3) Gera um token de uso único para o run_ci.sh
#   4) Grava o token em .env.sonar (NÃO versionar este arquivo)
#
# Uso:
#   ./setup_sonar.sh
#
# Variáveis opcionais (pode exportar antes de chamar o script):
#   SONAR_URL            (default: http://localhost:9000)
#   SONAR_NEW_PASSWORD   (default: gerada automaticamente)
#   SONAR_TOKEN_NAME      (default: ci-token)
# ============================================================
set -e

SONAR_URL="${SONAR_URL:-http://localhost:9000}"
SONAR_DEFAULT_USER="admin"
SONAR_DEFAULT_PASS="admin"
SONAR_NEW_PASSWORD="${SONAR_NEW_PASSWORD:-$(openssl rand -base64 18 | tr -dc 'A-Za-z0-9' | head -c 20)}"
SONAR_TOKEN_NAME="${SONAR_TOKEN_NAME:-ci-token}"
ENV_FILE="$(dirname "$0")/.env.sonar"

echo "⏳ Aguardando o SonarQube subir em $SONAR_URL ..."
until curl -s -o /dev/null -w "%{http_code}" "$SONAR_URL/api/system/status" | grep -q "200"; do
    sleep 3
done
until curl -s "$SONAR_URL/api/system/status" | grep -q '"status":"UP"'; do
    echo "   ...ainda inicializando o banco interno do Sonar"
    sleep 5
done
echo "✅ SonarQube está UP."

# ------------------------------------------------------------
# Passo 1: tenta logar com a senha padrão. Se conseguir, é o
# primeiro boot -> troca a senha. Se já não for mais admin/admin
# (porque o script já rodou antes), apenas seguimos com a senha
# salva no .env.sonar existente.
# ------------------------------------------------------------
LOGIN_CHECK=$(curl -s -o /dev/null -w "%{http_code}" -u "$SONAR_DEFAULT_USER:$SONAR_DEFAULT_PASS" \
    "$SONAR_URL/api/authentication/validate")

if [ "$LOGIN_CHECK" = "200" ]; then
    echo "🔑 Primeiro login detectado (admin/admin). Trocando a senha..."
    curl -s -f -u "$SONAR_DEFAULT_USER:$SONAR_DEFAULT_PASS" \
        -X POST "$SONAR_URL/api/users/change_password" \
        --data-urlencode "login=$SONAR_DEFAULT_USER" \
        --data-urlencode "previousPassword=$SONAR_DEFAULT_PASS" \
        --data-urlencode "password=$SONAR_NEW_PASSWORD" > /dev/null
    echo "✅ Senha do admin trocada."
    CURRENT_PASS="$SONAR_NEW_PASSWORD"
elif [ -f "$ENV_FILE" ]; then
    echo "ℹ️  admin/admin já não funciona mais — reutilizando senha salva em .env.sonar"
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    CURRENT_PASS="$SONAR_ADMIN_PASSWORD"
else
    echo "❌ Não foi possível logar com admin/admin e não há .env.sonar prévio."
    echo "   Rode com SONAR_NEW_PASSWORD=<senha-ja-definida> ./setup_sonar.sh"
    exit 1
fi

# ------------------------------------------------------------
# Passo 2: gera (ou regenera) o token de CI
# ------------------------------------------------------------
echo "🪪 Revogando token antigo (se existir) e gerando um novo..."
curl -s -u "$SONAR_DEFAULT_USER:$CURRENT_PASS" \
    -X POST "$SONAR_URL/api/user_tokens/revoke" \
    --data-urlencode "name=$SONAR_TOKEN_NAME" > /dev/null || true

RESPONSE=$(curl -s -f -u "$SONAR_DEFAULT_USER:$CURRENT_PASS" \
    -X POST "$SONAR_URL/api/user_tokens/generate" \
    --data-urlencode "name=$SONAR_TOKEN_NAME")

SONAR_TOKEN=$(echo "$RESPONSE" | grep -o '"token":"[^"]*' | cut -d'"' -f4)

if [ -z "$SONAR_TOKEN" ]; then
    echo "❌ Falha ao gerar o token. Resposta da API: $RESPONSE"
    exit 1
fi

# ------------------------------------------------------------
# Passo 3: persiste tudo em .env.sonar (gitignored)
# ------------------------------------------------------------
cat > "$ENV_FILE" <<EOF
SONAR_ADMIN_PASSWORD=$CURRENT_PASS
SONAR_TOKEN=$SONAR_TOKEN
EOF

echo "✅ Token gerado e salvo em $ENV_FILE"
echo "   (esse arquivo precisa estar no .gitignore!)"