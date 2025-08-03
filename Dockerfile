# Use Python 3.13 slim image for smaller size
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency management
RUN pip install uv

# Copy dependency files and README (required by pyproject.toml)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies using uv
RUN uv sync --frozen

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p /app/src/smart_core_assistant_painel/app/ui/db/sqlite \
    && mkdir -p /app/src/smart_core_assistant_painel/app/ui/media \
    && mkdir -p /app/src/smart_core_assistant_painel/app/ui/staticfiles

# Collect static files
RUN cd /app/src/smart_core_assistant_painel/app/ui && \
    python manage.py collectstatic --noinput

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/admin/ || exit 1

# Default command
CMD ["python", "src/smart_core_assistant_painel/main.py", "runserver", "0.0.0.0:8000"]