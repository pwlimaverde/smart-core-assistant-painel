"""
Compatibilidade de import para testes antigos que esperam o pacote
`langchain_pydantic`.

Este pacote reexporta classes e funções apontando para a nova
implementação em `analise_previa_langchain`.
"""
from .analise_previa_mensagem_langchain import AnalisePreviaMensagemLangchain
from .analise_previa_mensagem_langchain_datasource import (
    AnalisePreviaMensagemLangchainDatasource,
    create_dynamic_pydantic_model,
)

__all__ = [
    "AnalisePreviaMensagemLangchain",
    "AnalisePreviaMensagemLangchainDatasource",
    "create_dynamic_pydantic_model",
]