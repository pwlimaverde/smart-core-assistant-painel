"""Hub central para os serviços e configurações da aplicação.

Este módulo fornece uma classe singleton `ServiceHub` responsável por carregar
e fornecer configurações a partir do ConfigProvider.
"""

from pathlib import Path
from typing import Optional, Type

from langchain_core.language_models.chat_models import BaseChatModel

from smart_core_assistant_painel.modules.services.config.provider import (
    ConfigProvider,
)

from .unifield_data_services.domain.interface.unified_data_service import (
    UnifiedDataService,
)


class ServiceHub:
    """[SYS-DAT-001] Hub central de serviços e configurações da aplicação.

    É responsável por prover configurações via ConfigProvider
    e por disponibilizar instâncias e integrações entre serviços.
    Implementa o padrão Singleton para garantir uma única instância.
    """

    _instance: Optional["ServiceHub"] = None
    _initialized: bool = False

    def __new__(cls) -> "ServiceHub":
        if cls._instance is None:
            cls._instance = super(ServiceHub, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not self._initialized:
            self.base_dir: Path = Path(__file__).resolve().parent.parent.parent
            self._unified_data_service: Optional[UnifiedDataService] = None
            self._initialized = True

    def reload_config(self) -> None:
        """Deprecated: Configurações agora são carregadas dinamicamente via ConfigProvider."""
        pass

    def set_unified_data_service(self, uds: UnifiedDataService) -> None:
        self._unified_data_service = uds

    @property
    def unified_data_service(self) -> UnifiedDataService:
        if self._unified_data_service is None:
            raise RuntimeError("UnifiedDataService não configurado.")
        return self._unified_data_service

    # === API Keys ===
    @property
    def HUGGINGFACE_API_KEY(self) -> str:
        return ConfigProvider.get().huggingface_api_key

    @property
    def GROQ_API_KEY(self) -> str:
        return ConfigProvider.get().groq_api_key

    @property
    def OPENAI_API_KEY(self) -> str:
        return ConfigProvider.get().openai_api_key

    # === LLM ===
    @property
    def LLM_CLASS(self) -> Type[BaseChatModel]:
        class_name = ConfigProvider.get().llm_class
        return self._resolve_llm_class(class_name)

    @property
    def MODEL(self) -> str:
        return ConfigProvider.get().model

    @property
    def LLM_TEMPERATURE(self) -> int:
        return ConfigProvider.get().llm_temperature

    # === Transcrição ===
    @property
    def TRANSCRIPTION_PROVIDER(self) -> str:
        return ConfigProvider.get().transcription_provider

    @property
    def TRANSCRIPTION_MODEL(self) -> str:
        return ConfigProvider.get().transcription_model

    # === Prompts ===
    @property
    def PROMPT_SYSTEM_DADOS_EMPRESA(self) -> str:
        return ConfigProvider.get().prompt_system_dados_empresa

    @property
    def PROMPT_SYSTEM_ANALISE_CONTEUDO(self) -> str:
        return ConfigProvider.get().prompt_system_analise_conteudo

    @property
    def PROMPT_HUMAN_ANALISE_CONTEUDO(self) -> str:
        return ConfigProvider.get().prompt_human_analise_conteudo

    @property
    def PROMPT_SYSTEM_MELHORIA_CONTEUDO(self) -> str:
        return ConfigProvider.get().prompt_system_melhoria_conteudo

    @property
    def PROMPT_HUMAN_MELHORIA_CONTEUDO(self) -> str:
        return ConfigProvider.get().prompt_human_melhoria_conteudo

    @property
    def PROMPT_HUMAN_ANALISE_PREVIA_MENSAGEM(self) -> str:
        return ConfigProvider.get().prompt_human_analise_previa_mensagem

    @property
    def PROMPT_SYSTEM_ANALISE_PREVIA_MENSAGEM(self) -> str:
        return ConfigProvider.get().prompt_system_analise_previa_mensagem

    @property
    def PROMPT_SYSTEM_ANALISE_MENSAGEM(self) -> str:
        return ConfigProvider.get().prompt_system_analise_mensagem

    # === Embeddings ===
    @property
    def CHUNK_OVERLAP(self) -> int:
        return ConfigProvider.get().chunk_overlap

    @property
    def CHUNK_SIZE(self) -> int:
        return ConfigProvider.get().chunk_size

    @property
    def EMBEDDINGS_MODEL(self) -> str:
        return ConfigProvider.get().embeddings_model

    @property
    def EMBEDDINGS_CLASS(self) -> str:
        return ConfigProvider.get().embeddings_class

    # === Utilitarios ===
    @property
    def TIME_CACHE(self) -> int:
        return ConfigProvider.get().time_cache

    @property
    def VALID_ENTITY_TYPES(self) -> str:
        return ConfigProvider.get().valid_entity_types

    # === Prompts Externalizados (Tasks recentes) ===
    @property
    def PROMPT_REGRAS_RESPOSTA(self) -> str:
        return ConfigProvider.get().prompt_regras_resposta

    @property
    def PROMPT_REGRAS_TRANSFERENCIA(self) -> str:
        return ConfigProvider.get().prompt_regras_transferencia

    @property
    def PROMPT_TEMPLATE_USER_RAG(self) -> str:
        return ConfigProvider.get().prompt_template_user_rag

    @property
    def PROMPT_INTENT_SYSTEM(self) -> str:
        return ConfigProvider.get().prompt_intent_system

    @property
    def PROMPT_INTENT_FOOTER(self) -> str:
        return ConfigProvider.get().prompt_intent_footer

    @property
    def MSG_FALLBACK_SEM_INFO(self) -> str:
        return ConfigProvider.get().msg_fallback_sem_info

    @property
    def MSG_FALLBACK_GERAL(self) -> str:
        return ConfigProvider.get().msg_fallback_geral

    @property
    def MSG_TRANSFERENCIA_GENERICA(self) -> str:
        return ConfigProvider.get().msg_transferencia_generica

    @property
    def SIMILARITY_THRESHOLD(self) -> float:
        return ConfigProvider.get().similarity_threshold

    @property
    def VECTOR_DISTANCE_THRESHOLD(self) -> float:
        return ConfigProvider.get().vector_distance_threshold

    def _resolve_llm_class(self, class_name: str) -> Type[BaseChatModel]:
        """Resolve a string do nome da classe para a classe real."""
        if class_name == "ChatGroq":
            from langchain_groq import ChatGroq

            return ChatGroq
        elif class_name == "ChatOpenAI":
            from langchain_openai import ChatOpenAI

            return ChatOpenAI
        elif class_name == "ChatOllama":
            from langchain_ollama import ChatOllama

            return ChatOllama
        else:
            # Fallback padrão
            from langchain_groq import ChatGroq

            return ChatGroq


SERVICEHUB = ServiceHub()
