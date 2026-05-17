#!/bin/bash
# ============================================
# Resolve a última tag git e atualiza SMARTCORE_IMAGE_TAG
# nos arquivos .env.prod e .env do servidor.
#
# Uso: bash docker/scripts/resolve-image-tag.sh
# Deve ser executado na raiz do repositório.
# ============================================

set -e

# Busca tags atualizadas do remote
git fetch --tags --force 2>/dev/null

# Resolve a última tag semver (remove prefixo 'v')
TAG=$(git describe --tags --abbrev=0 2>/dev/null | sed 's/^v//')

if [ -z "$TAG" ]; then
    echo "[resolve-image-tag] Nenhuma tag encontrada. Usando 'latest'."
    TAG="latest"
fi

# Atualiza .env.prod
if [ -f .env.prod ]; then
    sed -i '/^SMARTCORE_IMAGE_TAG=/d' .env.prod
    echo "SMARTCORE_IMAGE_TAG=$TAG" >> .env.prod
fi

# Atualiza .env (cópia de trabalho)
if [ -f .env ]; then
    sed -i '/^SMARTCORE_IMAGE_TAG=/d' .env
    echo "SMARTCORE_IMAGE_TAG=$TAG" >> .env
fi

echo "[resolve-image-tag] SMARTCORE_IMAGE_TAG=$TAG"
