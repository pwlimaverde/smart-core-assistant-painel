"""Interface do serviço de dados unificado (UnifiedDataService).

Este pacote contém a definição da interface genérica que padroniza
operações de criação e manipulação de dados em diferentes provedores
externos (ex.: NotionGuideV2), permitindo acoplamento via adapters.
"""

from .unified_data_service import UnifiedDataService

__all__ = [
    "UnifiedDataService",
]
