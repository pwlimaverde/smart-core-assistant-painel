"""Configuração global para testes pytest com Django."""

import os
import sys
from pathlib import Path

import django
import pytest
from typing import Any

# Ensure the src directory is in the path
repo_root = Path(__file__).resolve().parents[1]
src_dir = repo_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Adiciona um alias de pacote "ai_engine" apontando para o pacote real
# em src/smart_core_assistant_painel/modules/ai_engine para compatibilizar
# imports absolutos no código (ex.: "from ai_engine.features...") durante os testes.
try:
    ai_engine_dir = (
        src_dir
        / "smart_core_assistant_painel"
        / "modules"
        / "ai_engine"
    )
    if "ai_engine" not in sys.modules and ai_engine_dir.is_dir():
        import types

        alias_pkg = types.ModuleType("ai_engine")
        # Torna o alias um pacote para permitir imports de submódulos reais
        alias_pkg.__path__ = [str(ai_engine_dir)]  # type: ignore[attr-defined]
        sys.modules["ai_engine"] = alias_pkg
except Exception:
    # Caso falhe, os testes indicarão o problema; não interromper a coleta
    pass

# Set the Django settings module
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.core.settings_test"
)

# Initialize Django
django.setup()

# Configure pytest-django


@pytest.fixture(autouse=True)
def mock_clickup_department_provision(monkeypatch: Any) -> None:
    """
    Neutraliza provisionamento de Departamento no ClickUp durante testes.

    Comentário: os testes não devem acionar integrações externas. Este mock
    substitui o método de provisionamento por no-op, evitando criação de
    Folders/Spaces no ClickUp quando `Departamento` é criado em testes.
    """
    try:
        from smart_core_assistant_painel.app.clickup_sync.services.department_provision_service import (
            DepartmentProvisionService,
        )

        def _noop(self: Any, departamento: Any) -> None:
            return None

        monkeypatch.setattr(
            DepartmentProvisionService,
            "provision_on_department_create",
            _noop,
            raising=True,
        )
    except Exception:
        # Se o módulo não estiver disponível no contexto de testes,
        # não interrompe a execução; outros testes seguem normalmente.
        pass


@pytest.fixture(autouse=True)
def mock_django_q_async_task(monkeypatch: Any) -> None:
    """
    Substitui `django_q.tasks.async_task` por no-op em todos os testes.

    Comentário: evita disparo de tarefas assíncronas reais (ClickUp, Trello,
    Notion, etc.) durante a execução dos testes, garantindo isolamento e
    ausência de efeitos colaterais externos.
    """
    try:
        import django_q.tasks as dq  # type: ignore[import-not-found]

        def _noop(*args: Any, **kwargs: Any) -> None:
            return None

        monkeypatch.setattr(dq, "async_task", _noop, raising=True)
    except Exception:
        # Se o pacote não estiver presente no ambiente de testes, ignora.
        pass
