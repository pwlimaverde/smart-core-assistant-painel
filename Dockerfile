# Usar Python 3.13 Slim como base
FROM python:3.13-slim

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /bin/uv

# Configurar diretório de trabalho
WORKDIR /app

# Copiar arquivos de dependência
COPY pyproject.toml uv.lock ./

# Instalar dependências
RUN uv sync --frozen --no-install-project --no-dev

# Copiar código fonte
COPY src ./src
COPY scripts ./scripts
COPY README.md ./

# Instalar o projeto
RUN uv sync --frozen --no-dev
RUN uv pip install --python /app/.venv/bin/python loguru django-stubs-ext

# Adicionar .venv ao PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expor porta padrão (pode ser sobrescrita pelo compose)
EXPOSE 8000

# Comando padrão
CMD ["python", "-m", "smart_core_assistant_painel.main", "runserver", "0.0.0.0:8000"]
