"""
Datasource simplificado para análise prévia de mensagens.

Este pacote expõe:
- AnalisePreviaLangchainDatasource: datasource simplificado baseado em
  LangChain com saída estruturada via Pydantic.
- build_analise_previa_model: construtor do modelo Pydantic dinâmico com
  descrições e exemplos derivados da configuração atual (intents/entities).
"""
from .datasource import AnalisePreviaLangchainDatasource
from .model_builder import build_analise_previa_model

__all__ = [
    "AnalisePreviaLangchainDatasource",
    "build_analise_previa_model",
]