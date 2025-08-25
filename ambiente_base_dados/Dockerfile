# Dockerfile para PostgreSQL com extensões personalizadas
# Baseado na imagem TimescaleDB que já inclui pgvector e outras extensões úteis

FROM timescale/timescaledb-ha:pg16

# Definir variáveis de ambiente padrão
ENV POSTGRES_DB=smart_core_db
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres123

# Instalar extensões adicionais se necessário
RUN apt-get update && apt-get install -y \
    postgresql-16-pgvector \
    && rm -rf /var/lib/apt/lists/*

# Copiar scripts de inicialização se existirem
COPY initdb/*.sql /docker-entrypoint-initdb.d/ 2>/dev/null || true

# Expor porta padrão do PostgreSQL
EXPOSE 5432

# O resto é gerenciado pelo entrypoint da imagem base