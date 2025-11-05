"""Configuração central de logging com Loguru.

Esta função adiciona um *sink* de arquivo com `enqueue=True` para
garantir escrita segura em ambientes com múltiplos processos
(ex.: `django-q`). O arquivo padrão é `log_errro_notion.txt` na raiz.

Comentário: manter comentários em Português, nomes em Inglês.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
import sys

from loguru import logger


def configure_logging(log_file: Optional[str] = None) -> None:
    """Configura o *file sink* do Loguru.

    Args:
        log_file: Caminho do arquivo de log. Caso `None`, usa o
            valor da variável de ambiente `LOG_FILE_PATH` ou
            `log_errro_notion.txt` na raiz do projeto.

    Returns:
        None

    """
    # Descobre arquivo alvo via env, com padrão estabelecido.
    target = (
        (log_file or os.getenv("LOG_FILE_PATH")) or "log_errro_notion.txt"
    )

    # Resolve caminho absoluto de forma portátil.
    path = Path(target).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    # Remove sinks antigos para evitar duplicidade em re-imports.
    logger.remove()

    # Adiciona console padrão.
    logger.add(
        sys.stderr, level="INFO", backtrace=True, diagnose=True
    )

    # Adiciona sink de arquivo com `enqueue=True` para multiprocessos.
    logger.add(
        str(path),
        level="DEBUG",
        rotation="10 MB",
        retention="10 days",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )