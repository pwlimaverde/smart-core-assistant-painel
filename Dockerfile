# Dockerfile para produção
FROM python:3.13-slim

# Definir variáveis de ambiente
ENV PYTHONPATH=/app/src
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=core.settings

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    libpq-dev \
    postgresql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv para gerenciamento de dependências
RUN pip install uv

# Definir diretório de trabalho
WORKDIR /app

# Copiar arquivos de configuração de dependências
COPY pyproject.toml uv.lock ./

# Instalar dependências (apenas produção)
RUN uv sync --frozen

# Instalar psycopg[binary] separadamente
RUN uv add psycopg[binary]

# Copiar código fonte
COPY src/ ./src/

# Copiar chave do Firebase se existir (condicional)
COPY src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json /app/src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json 2>/dev/null || echo "Firebase key not found, skipping..."

# Copiar e tornar scripts executáveis
COPY scripts/docker-entrypoint.sh /usr/local/bin/
COPY scripts/docker-entrypoint-qcluster.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint-qcluster.sh

# Criar diretórios necessários
RUN mkdir -p /app/src/smart_core_assistant_painel/app/ui/db
RUN mkdir -p /app/src/smart_core_assistant_painel/app/ui/media

# Criar usuário não-root para segurança
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expor porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/admin/ || exit 1

# Entrypoint e comando padrão
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["uv", "run", "python", "src/smart_core_assistant_painel/app/ui/manage.py", "runserver", "0.0.0.0:8000"]