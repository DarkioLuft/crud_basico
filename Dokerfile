# ---------------------------------------
# STAGE 1: Builder (Instala dependências)
# ---------------------------------------
FROM python:3.12-slim as builder

WORKDIR /app

# Impede o Python de gravar arquivos .pyc e força o log no terminal (sem buffer)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instala dependências do sistema necessárias para o psycopg2 (PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instala as bibliotecas Python como wheels (mais rápido e seguro)
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# ---------------------------------------
# STAGE 2: Runtime (Imagem Final Limpa)
# ---------------------------------------
FROM python:3.12-slim

WORKDIR /app

# Instala apenas a biblioteca de execução do PostgreSQL e netcat (para wait-for-it)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copia os wheels do builder e instala
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# Copia o código da aplicação
COPY . .

# Dá permissão de execução ao script de inicialização
RUN chmod +x /app/entrypoint.sh

# Expõe a porta que o Gunicorn vai escutar
EXPOSE 8000

# Define o entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]