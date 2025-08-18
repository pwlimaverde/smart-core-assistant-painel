# Use Python 3.13 slim image for development
FROM python:3.13-slim

# Set environment variables for development
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/src \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Set work directory
WORKDIR /app

# Install system dependencies including development tools and PostgreSQL client
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    vim \
    nano \
    htop \
    procps \
    dos2unix \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency management
RUN pip install uv

# Copy dependency files and README (required by pyproject.toml)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies using uv (including dev dependencies)
RUN uv sync --frozen --dev

# Install psycopg manually as a workaround
RUN uv pip install psycopg[binary]==3.2.3

# Copy project files
COPY . .

# Firebase credentials are provided at runtime via volume mount and GOOGLE_APPLICATION_CREDENTIALS; no build-time copy

# Copy and make entrypoint scripts executable
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
COPY docker-entrypoint-qcluster.sh /usr/local/bin/docker-entrypoint-qcluster.sh
RUN dos2unix /usr/local/bin/docker-entrypoint.sh /usr/local/bin/docker-entrypoint-qcluster.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh /usr/local/bin/docker-entrypoint-qcluster.sh

# Create necessary directories
RUN mkdir -p /app/src/smart_core_assistant_painel/app/ui/db/sqlite \
    && mkdir -p /app/src/smart_core_assistant_painel/app/ui/media \
    && mkdir -p /app/src/smart_core_assistant_painel/app/ui/staticfiles

# For development, we'll run as root for simplicity
# In production, consider using a non-root user

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/admin/ || exit 1

# Set entrypoint
# ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]  # Temporariamente desabilitado

# Default command - agora usa manage.py diretamente após inicialização
CMD ["uv", "run", "python", "src/smart_core_assistant_painel/app/ui/manage.py", "runserver", "0.0.0.0:8000"]