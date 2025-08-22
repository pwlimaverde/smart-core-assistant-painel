# Dockerfile para Smart Core Assistant Painel - Ambiente Django
FROM python:3.13-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema necessárias para compilar wheels quando necessário
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Criar e preparar ambiente virtual fora do diretório do projeto para não ser sobrescrito pelo bind mount
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Instalar ferramentas base e uv dentro do venv
RUN pip install --upgrade pip setuptools wheel uv

# Aproveitar cache: copiar apenas arquivos de dependências primeiro
COPY pyproject.toml README.md uv.lock ./

# Instalar dependências sem copiar o código (evita invalidar cache por mudanças no código)
# Excluir dependências ML pesadas que não são necessárias para a execução básica
# Usar --no-deps para as bibliotecas que podem trazer dependências da NVIDIA
RUN uv sync --frozen --no-dev

# Copiar o restante do código (somente após instalar deps)
COPY . .

# Criar usuário não-root para segurança
RUN adduser --disabled-password --gecos '' app \
    && chown -R app:app /app
USER app

# Expor porta da aplicação
EXPOSE 8000

# Comando padrão (pode ser sobrescrito pelo docker-compose)
CMD ["python", "src/smart_core_assistant_painel/main.py", "runserver", "0.0.0.0:8000"]