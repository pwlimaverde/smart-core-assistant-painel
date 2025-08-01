from dataclasses import dataclass
from typing import Any, Dict, Optional, Type

from langchain_core.language_models.chat_models import BaseChatModel
from py_return_success_or_error import ParametersReturnResult

from smart_core_assistant_painel.modules.ai_engine.utils.erros import (
    DocumentError,
    LlmError,
    WahaApiError,
)


@dataclass
class MessageParameters(ParametersReturnResult):
    session: str
    chat_id: str
    message: Optional[str]
    error: WahaApiError

    def __str__(self) -> str:
        return self.__repr__()


@dataclass
class LoadDocumentFileParameters(ParametersReturnResult):
    id: str
    path: str
    tag: str
    grupo: str
    error: DocumentError

    def __str__(self) -> str:
        return self.__repr__()


@dataclass
class LoadDocumentConteudoParameters(ParametersReturnResult):
    id: str
    conteudo: str
    tag: str
    grupo: str
    error: DocumentError

    def __str__(self) -> str:
        return self.__repr__()


class LlmParameters(ParametersReturnResult):
    __slots__ = [
        "__llm_class",
        "__model",
        "__extra_params",
        "prompt_system",
        "prompt_human",
        "context",
        "error",
    ]

    def __init__(
        self,
        llm_class: Type[BaseChatModel],
        model: str,
        error: LlmError,
        prompt_system: str,
        prompt_human: str,
        context: str,
        extra_params: Optional[Dict[str, Any]] = None,
    ):
        self.error = error
        self.__llm_class = llm_class
        self.__model = model
        self.__extra_params = extra_params
        self.prompt_system = prompt_system
        self.prompt_human = prompt_human
        self.context = context

    @property
    def create_llm(self) -> BaseChatModel:
        """Cria instância da LLM com os parâmetros configurados"""
        params = self.__get_params()
        return self.__llm_class(**params)

    def __get_params(self) -> Dict[str, Any]:
        """Retorna parâmetros como dict"""
        params = {"model": self.__model}

        if self.__extra_params:
            params.update(self.__extra_params)

        return params

    def __str__(self) -> str:
        return self.__repr__()


@dataclass
class AnalisePreviaMensagemParameters(ParametersReturnResult):
    historico_atendimento: dict[str, Any]
    valid_intent_types: str
    valid_entity_types: str
    llm_parameters: LlmParameters
    error: LlmError

    def __str__(self) -> str:
        return self.__repr__()
