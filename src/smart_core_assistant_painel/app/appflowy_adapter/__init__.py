"""
Adapter de integração com o AppFlowy.

Este módulo centraliza e expõe a API pública do app `appflowy_adapter`,
responsável por fornecer endpoints mínimos para sincronização do Grid
de Atendimentos com o cliente AppFlowy Desktop.
"""

from .apps import AppFlowyAdapterConfig

__all__ = [
    "AppFlowyAdapterConfig",
]