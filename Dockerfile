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

# Install system dependencies and uv in a single layer
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    vim \
    nano \
    htop \
    procps \
    libpq-dev \
    postgresql-client \
    jq \
    && rm -rf /var/lib/apt/lists/* \
    && pip install uv

# Copy dependency files and README (required by pyproject.toml)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies using uv in a single layer
RUN uv sync --frozen --dev && \
    uv pip install psycopg[binary]==3.2.3

# Copy project files
COPY . .

# Create Firebase config directory and generate credentials from environment variable
ARG FIREBASE_KEY_JSON_CONTENT
RUN mkdir -p /app/src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/ && \
    if [ -n "$FIREBASE_KEY_JSON_CONTENT" ]; then \
        printf '%s\n' "$FIREBASE_KEY_JSON_CONTENT" | jq '.' > /app/src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json; \
    else \
        echo "Warning: FIREBASE_KEY_JSON_CONTENT not provided. Make sure to mount the firebase_key.json file."; \
    fi

# Create necessary directories
RUN mkdir -p /app/src/smart_core_assistant_painel/app/ui/db/sqlite && \
    mkdir -p /app/src/smart_core_assistant_painel/app/ui/media && \
    mkdir -p /app/src/smart_core_assistant_painel/app/ui/staticfiles

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