import os
from pathlib import Path
from typing import Optional, Type

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama


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
        self.PASTA_FAISS_DB: Path = Path(
            __file__).parent.parent.parent / 'app/db/banco_faiss'

        self._whatsapp_api_base_url: Optional[str] = None
        self._whatsapp_api_send_text_url: Optional[str] = None
        self._whatsapp_api_start_typing_url: Optional[str] = None
        self._whatsapp_api_stop_typing_url: Optional[str] = None
        self._llm_class: Optional[Type[BaseChatModel]] = None
        self._model: Optional[str] = None
        self._temperature: Optional[int] = None
        self._prompt_system_analise_conteudo: Optional[str] = None
        self._prompt_human_analise_conteudo: Optional[str] = None
        self._prompt_system_melhoria_conteudo: Optional[str] = None
        self._prompt_human_melhoria_conteudo: Optional[str] = None
        self._chunk_overlap: Optional[int] = None
        self._chunk_size: Optional[int] = None
        self._faiss_model: Optional[str] = None

    @property
    def CHUNK_OVERLAP(self) -> int:
        if self._chunk_overlap is None:
            self._chunk_overlap = int(os.environ.get('CHUNK_OVERLAP', '200'))
        return self._chunk_overlap if self._chunk_overlap is not None else ""

    @property
    def CHUNK_SIZE(self) -> int:
        if self._chunk_size is None:
            self._chunk_size = int(os.environ.get('CHUNK_SIZE', '20'))
        return self._chunk_size if self._chunk_size is not None else ""

    @property
    def FAISS_MODEL(self) -> str:
        if self._faiss_model is None:
            self._faiss_model = os.environ.get(
                'FAISS_MODEL')
        return self._faiss_model if self._faiss_model is not None else ""

    @property
    def PROMPT_HUMAN_MELHORIA_CONTEUDO(self) -> str:
        if self._prompt_human_melhoria_conteudo is None:
            self._prompt_human_melhoria_conteudo = os.environ.get(
                'PROMPT_HUMAN_MELHORIA_CONTEUDO')
        return self._prompt_human_melhoria_conteudo if self._prompt_human_melhoria_conteudo is not None else ""

    @property
    def PROMPT_SYSTEM_MELHORIA_CONTEUDO(self) -> str:
        if self._prompt_system_melhoria_conteudo is None:
            self._prompt_system_melhoria_conteudo = os.environ.get(
                'PROMPT_SYSTEM_MELHORIA_CONTEUDO')
        return self._prompt_system_melhoria_conteudo if self._prompt_system_melhoria_conteudo is not None else ""

    @property
    def PROMPT_HUMAN_ANALISE_CONTEUDO(self) -> str:
        if self._prompt_human_analise_conteudo is None:
            self._prompt_human_analise_conteudo = os.environ.get(
                'PROMPT_HUMAN_ANALISE_CONTEUDO')
        return self._prompt_human_analise_conteudo if self._prompt_human_analise_conteudo is not None else ""

    @property
    def PROMPT_SYSTEM_ANALISE_CONTEUDO(self) -> str:
        if self._prompt_system_analise_conteudo is None:
            self._prompt_system_analise_conteudo = os.environ.get(
                'PROMPT_SYSTEM_ANALISE_CONTEUDO')
        return self._prompt_system_analise_conteudo if self._prompt_system_analise_conteudo is not None else ""

    @property
    def TEMPERATURE(self) -> int:
        if self._temperature is None:
            self._temperature = int(os.environ.get('TEMPERATURE', '0'))
        return self._temperature if self._temperature is not None else 0

    @property
    def MODEL(self) -> str:
        if self._model is None:
            self._model = os.environ.get(
                'MODEL')
        return self._model if self._model is not None else ""

    @property
    def WHATSAPP_API_BASE_URL(self) -> str:
        if self._whatsapp_api_base_url is None:
            self._whatsapp_api_base_url = os.environ.get(
                'WHATSAPP_API_BASE_URL')
        return self._whatsapp_api_base_url if self._whatsapp_api_base_url is not None else ""

    @property
    def WHATSAPP_API_SEND_TEXT_URL(self) -> str:
        if self._whatsapp_api_send_text_url is None:
            self._whatsapp_api_send_text_url = os.environ.get(
                'WHATSAPP_API_SEND_TEXT_URL')
        return self._whatsapp_api_send_text_url if self._whatsapp_api_send_text_url is not None else ""

    @property
    def WHATSAPP_API_START_TYPING_URL(self) -> str:
        if self._whatsapp_api_start_typing_url is None:
            self._whatsapp_api_start_typing_url = os.environ.get(
                'WHATSAPP_API_START_TYPING_URL')
        return self._whatsapp_api_start_typing_url if self._whatsapp_api_start_typing_url is not None else ""

    @property
    def WHATSAPP_API_STOP_TYPING_URL(self) -> str:
        if self._whatsapp_api_stop_typing_url is None:
            self._whatsapp_api_stop_typing_url = os.environ.get(
                'WHATSAPP_API_STOP_TYPING_URL')
        return self._whatsapp_api_stop_typing_url if self._whatsapp_api_stop_typing_url is not None else ""

    @property
    def LLM_CLASS(self) -> Type[BaseChatModel]:
        if self._llm_class is None:
            self._llm_class = self._get_llm_class()
        return self._llm_class if self._llm_class is not None else ChatOllama

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
