"""Configuração global para testes pytest com Django."""

import os
import sys
import django
from pathlib import Path
import types
from typing import Any




def pytest_configure() -> None:
    """Configura o Django para os testes.

    - Garante que a raiz do projeto e o diretório src estejam no sys.path.
    - Respeita DJANGO_SETTINGS_MODULE se já estiver definido (pytest.ini/ambiente).
    - Usa settings_test como padrão para alinhar com execução no Docker.
    """
    # Garante que a raiz do projeto e o diretório src estejam no sys.path
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    ui_dir = src_dir / "smart_core_assistant_painel" / "app" / "ui"
    for p in (str(repo_root), str(src_dir), str(ui_dir)):
        if p not in sys.path:
            sys.path.insert(0, p)

    # Define o DJANGO_SETTINGS_MODULE respeitando o que já vier do ambiente
    settings_module = os.environ.get(
        "DJANGO_SETTINGS_MODULE",
        "smart_core_assistant_painel.app.ui.core.settings_test",
    )
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

    django.setup()


# ====================
# Silenciar Loguru nos testes
# ====================
import pytest
from typing import Iterator
from loguru import logger


@pytest.fixture(autouse=True, scope="session")
def silence_loguru_for_tests() -> Iterator[None]:
    """Remove os sinks padrão do Loguru durante toda a sessão de testes.

    Objetivo: evitar que mensagens de erro/aviso apareçam no output do pytest
    quando os testes passam (p.ex., simulações de falha esperada). Mantemos
    a geração de logs para possíveis inspeções internas, mas sem imprimir
    nada no stdout/stderr.
    """
    # Remove todos os sinks configurados (inclusive o padrão em stderr)
    try:
        logger.remove()
    except Exception:
        # Falha ao remover não deve bloquear a suíte de testes
        pass

    # Adiciona um "sink" nulo que descarta todas as mensagens.
    class _NullSink:
        def write(self, message: str) -> None:  # pragma: no cover - trivial
            return

    logger.add(_NullSink())
    yield
    # Ao final não reconfiguramos para evitar ruído em teardown; ambiente de
    # testes terminará logo após a sessão.


# ====================
# Supressão de warnings específicos
# ====================
import warnings

# Suprime o DeprecationWarning específico do numpy.core._multiarray_umath em faiss/loader.py
warnings.filterwarnings(
    "ignore",
    message=r".*numpy\.core\._multiarray_umath.*",
    category=DeprecationWarning
)

# Suprime warnings específicos do FAISS
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    module="faiss.*"
)

# Suprime outros warnings relacionados ao FAISS
warnings.filterwarnings(
    "ignore",
    message=r".*SwigPyPacked.*",
    category=DeprecationWarning
)

warnings.filterwarnings(
    "ignore",
    message=r".*SwigPyObject.*",
    category=DeprecationWarning
)

warnings.filterwarnings(
    "ignore",
    message=r".*swigvarlink.*",
    category=DeprecationWarning
)