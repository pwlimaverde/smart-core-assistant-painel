import os
from pathlib import Path
from typing import Optional, Type

from langchain_core.language_models.chat_models import BaseChatModel


class ServiceHub:
    """Classe singleton para gerenciar configurações do ambiente."""

    _instance: Optional['ServiceHub'] = None
    _initialized: bool = False

    def __new__(cls) -> 'ServiceHub':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not self._initialized:
            self._load_config()
            ServiceHub._initialized = True

    def _load_config(self) -> None:
        """Carrega as configurações das variáveis de ambiente."""
        # Constante para o caminho do arquivo de dados
        self.PASTA_DATASETS: Path = Path(
            __file__).parent.parent.parent / 'app/datasets'
        self._whatsapp_api_base_url: str
        self._whatsapp_api_send_text_url: str
        self._whatsapp_api_start_typing_url: str
        self._whatsapp_api_stop_typing_url: str
        self._llm_class: Type[BaseChatModel]
        self._model: str
        self._temperature: int
        self._prompt_system_analise_conteudo: str
        self._prompt_human_analise_conteudo: str

    @property
    def PROMPT_HUMAN_ANALISE_CONTEUDO(self) -> str:
        if self._prompt_human_analise_conteudo is None:
            self._prompt_human_analise_conteudo = os.environ.get(
                'PROMPT_HUMAN_ANALISE_CONTEUDO')
        return self._prompt_human_analise_conteudo

    @property
    def PROMPT_SYSTEM_ANALISE_CONTEUDO(self) -> str:
        if self._prompt_system_analise_conteudo is None:
            self._prompt_system_analise_conteudo = os.environ.get(
                'PROMPT_SYSTEM_ANALISE_CONTEUDO')
        return self._prompt_system_analise_conteudo

    @property
    def TEMPERATURE(self) -> int:
        if self._temperature is None:
            self._temperature = int(os.environ.get('TEMPERATURE', '0'))
        return self._temperature

    @property
    def MODEL(self) -> str:
        if self._model is None:
            self._model = os.environ.get(
                'MODEL')
        return self._model

    @property
    def WHATSAPP_API_BASE_URL(self) -> str:
        if self._whatsapp_api_base_url is None:
            self._whatsapp_api_base_url = os.environ.get(
                'WHATSAPP_API_BASE_URL')
        return self._whatsapp_api_base_url

    @property
    def WHATSAPP_API_SEND_TEXT_URL(self) -> str:
        if self._whatsapp_api_send_text_url is None:
            self._whatsapp_api_send_text_url = os.environ.get(
                'WHATSAPP_API_SEND_TEXT_URL')
        return self._whatsapp_api_send_text_url

    @property
    def WHATSAPP_API_START_TYPING_URL(self) -> str:
        if self._whatsapp_api_start_typing_url is None:
            self._whatsapp_api_start_typing_url = os.environ.get(
                'WHATSAPP_API_START_TYPING_URL')
        return self._whatsapp_api_start_typing_url

    @property
    def WHATSAPP_API_STOP_TYPING_URL(self) -> str:
        if self._whatsapp_api_stop_typing_url is None:
            self._whatsapp_api_stop_typing_url = os.environ.get(
                'WHATSAPP_API_STOP_TYPING_URL')
        return self._whatsapp_api_stop_typing_url

    @property
    def LLM_CLASS(self) -> Type[BaseChatModel]:
        if self._llm_class is None:
            self._llm_class = self._get_llm_class()
        return self._llm_class

    def _get_llm_class(self) -> Type[BaseChatModel]:
        """Retorna a classe LLM baseada na variável de ambiente."""
        llm_type = os.environ.get('LLM_CLASS', 'ChatOllama')
        if llm_type == 'ChatGroq':
            from langchain_groq import ChatGroq
            return ChatGroq
        elif llm_type == 'ChatOpenAI':
            from langchain_openai import ChatOpenAI
            return ChatOpenAI
        elif llm_type == 'ChatOllama':
            from langchain_ollama import ChatOllama
            return ChatOllama
        else:
            raise ValueError(
                f"LLM class '{llm_type}' not recognized. "
                "Please set 'LLM_CLASS' environment variable to 'ChatGroq', 'ChatOpenAI', or 'ChatOllama'."
            )


# Instância global da configuração
SERVICEHUB = ServiceHub()
