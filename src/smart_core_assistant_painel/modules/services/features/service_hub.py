"""Hub central para os serviços e configurações da aplicação.

Este módulo fornece uma classe singleton `ServiceHub` responsável por carregar
e fornecer configurações a partir de variáveis de ambiente e por disponibilizar
instâncias de serviços e integrações em toda a aplicação.

Classes:
    ServiceHub: O singleton central para gerenciamento de serviços e configurações.
"""
import os
from pathlib import Path
from typing import Optional, Type

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel

from .vetor_storage.domain.interface.vetor_storage import VetorStorage
from .whatsapp_services.domain.interface.whatsapp_service import (
    WhatsAppService,
)


class ServiceHub:
    """Hub central de serviços e configurações da aplicação.

    É responsável por carregar e prover configurações via variáveis de ambiente
    e por disponibilizar instâncias e integrações entre serviços.
    Implementa o padrão Singleton para garantir uma única instância.
    """

    _instance: Optional["ServiceHub"] = None
    _initialized: bool = False

    def __new__(cls) -> "ServiceHub":
        """Cria uma nova instância de ServiceHub se ainda não existir.

        Returns:
            ServiceHub: A instância singleton da classe.
        """
        if cls._instance is None:
            cls._instance = super(ServiceHub, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Inicializa a instância do ServiceHub.

        Carrega todas as configurações a partir de variáveis de ambiente
        apenas uma vez.
        """
        if not self._initialized:
            self.base_dir: Path = Path(__file__).resolve().parent.parent.parent
            self._time_cache: Optional[int] = None
            self._chunk_overlap: Optional[int] = None
            self._chunk_size: Optional[int] = None
            self._embeddings_model: Optional[str] = None
            self._embeddings_class: Optional[Type[Embeddings]] = None
            self._prompt_human_melhoria_conteudo: Optional[str] = None
            self._prompt_system_melhoria_conteudo: Optional[str] = None
            self._prompt_human_analise_conteudo: Optional[str] = None
            self._prompt_system_analise_conteudo: Optional[str] = None
            self._temperature: Optional[int] = None
            self._model: Optional[str] = None
            self._llm_class: Optional[Type[BaseChatModel]] = None
            self._whatsapp_api_base_url: Optional[str] = None
            self._vetor_storage: Optional[VetorStorage] = None
            self._whatsapp_service: Optional[WhatsAppService] = None
            self._prompt_system_analise_previa_mensagem: Optional[str] = None
            self._prompt_human_analise_previa_mensagem: Optional[str] = None
            self._valid_entity_types: Optional[str] = None
            self._valid_intent_types: Optional[str] = None
            self._huggingface_api_key: Optional[str] = None

            self._load_config()
            self._initialized = True

    def _load_config(self) -> None:
        """Carrega as configurações iniciais a partir de variáveis de ambiente."""
        self._time_cache = int(os.environ.get("TIME_CACHE", "20"))
        self._chunk_overlap = int(os.environ.get("CHUNK_OVERLAP", "200"))
        self._chunk_size = int(os.environ.get("CHUNK_SIZE", "1000"))
        self._embeddings_model = os.environ.get("EMBEDDINGS_MODEL")
        self._temperature = int(os.environ.get("TEMPERATURE", "0"))
        self._model = os.environ.get("MODEL", "llama3.1")
        self._whatsapp_api_base_url = os.environ.get("WHATSAPP_API_BASE_URL")

        vetor_storage_type = os.environ.get("VETOR_STORAGE_TYPE")
        if vetor_storage_type is not None and self._vetor_storage is None:
            raise RuntimeError(
                "Falha ao auto-configurar VetorStorage. "
                "Use set_vetor_storage() para definir a instância manualmente."
            )

        whatsapp_service_type = os.environ.get("WHATSAPP_SERVICE_TYPE")
        if whatsapp_service_type is not None and self._whatsapp_service is None:
            raise RuntimeError(
                "Falha ao auto-configurar WhatsAppService. "
                "Use set_whatsapp_service() para definir a instância manualmente."
            )

    def set_vetor_storage(self, vetor_storage: VetorStorage) -> None:
        """Define a implementação de VetorStorage a ser utilizada.

        Args:
            vetor_storage (VetorStorage): Uma instância de uma classe que
                implementa a interface VetorStorage.
        """
        self._vetor_storage = vetor_storage

    def set_whatsapp_service(self, whatsapp_service: WhatsAppService) -> None:
        """Define a implementação de WhatsAppService a ser utilizada.

        Args:
            whatsapp_service (WhatsAppService): Uma instância de uma classe que
                implementa a interface WhatsAppService.
        """
        self._whatsapp_service = whatsapp_service

    @property
    def TIME_CACHE(self) -> int:
        """Retorna o tempo de cache em segundos."""
        if self._time_cache is None:
            self._time_cache = int(os.environ.get("TIME_CACHE", "20"))
        return self._time_cache if self._time_cache is not None else 20

    @property
    def vetor_storage(self) -> VetorStorage:
        """Retorna a instância configurada do VetorStorage.

        Raises:
            RuntimeError: Se o serviço não tiver sido configurado.
        """
        if self._vetor_storage is None:
            raise RuntimeError(
                "VetorStorage não configurado. "
                "Use set_vetor_storage() para definir a instância manualmente."
            )
        return self._vetor_storage

    @property
    def whatsapp_service(self) -> WhatsAppService:
        """Retorna a instância configurada do WhatsAppService.

        Raises:
            RuntimeError: Se o serviço não tiver sido configurado.
        """
        if self._whatsapp_service is None:
            raise RuntimeError(
                "WhatsAppService não configurado. "
                "Use set_whatsapp_service() para definir a instância manualmente."
            )
        return self._whatsapp_service

    @property
    def CHUNK_OVERLAP(self) -> int:
        """Retorna o tamanho da sobreposição de chunks para divisão de texto."""
        if self._chunk_overlap is None:
            self._chunk_overlap = int(os.environ.get("CHUNK_OVERLAP", "200"))
        return self._chunk_overlap if self._chunk_overlap is not None else 200

    @property
    def CHUNK_SIZE(self) -> int:
        """Retorna o tamanho do chunk para divisão de texto."""
        if self._chunk_size is None:
            self._chunk_size = int(os.environ.get("CHUNK_SIZE", "1000"))
        return self._chunk_size if self._chunk_size is not None else 1000

    @property
    def EMBEDDINGS_MODEL(self) -> str:
        """Retorna o nome do modelo de embeddings."""
        if self._embeddings_model is None:
            self._embeddings_model = os.environ.get("EMBEDDINGS_MODEL")
        return self._embeddings_model if self._embeddings_model is not None else ""

    @property
    def HUGGINGFACE_API_KEY(self) -> str:
        """Retorna a chave de API da Hugging Face para embeddings.

        Verifica 'HUGGINGFACE_API_KEY' primeiro, depois recorre a
        'HUGGINGFACEHUB_API_KEY' para compatibilidade.
        """
        if self._huggingface_api_key is None:
            self._huggingface_api_key = os.environ.get("HUGGINGFACE_API_KEY")
            if not self._huggingface_api_key:
                self._huggingface_api_key = os.environ.get(
                    "HUGGINGFACEHUB_API_KEY"
                )
        return self._huggingface_api_key if self._huggingface_api_key else ""

    @property
    def PROMPT_HUMAN_MELHORIA_CONTEUDO(self) -> str:
        """Retorna o prompt humano para melhoria de conteúdo."""
        if self._prompt_human_melhoria_conteudo is None:
            self._prompt_human_melhoria_conteudo = os.environ.get(
                "PROMPT_HUMAN_MELHORIA_CONTEUDO"
            )
        return (
            self._prompt_human_melhoria_conteudo
            if self._prompt_human_melhoria_conteudo is not None
            else ""
        )

    @property
    def PROMPT_SYSTEM_MELHORIA_CONTEUDO(self) -> str:
        """Retorna o prompt de sistema para melhoria de conteúdo."""
        if self._prompt_system_melhoria_conteudo is None:
            self._prompt_system_melhoria_conteudo = os.environ.get(
                "PROMPT_SYSTEM_MELHORIA_CONTEUDO"
            )
        return (
            self._prompt_system_melhoria_conteudo
            if self._prompt_system_melhoria_conteudo is not None
            else ""
        )

    @property
    def PROMPT_HUMAN_ANALISE_CONTEUDO(self) -> str:
        """Retorna o prompt humano para análise de conteúdo."""
        if self._prompt_human_analise_conteudo is None:
            self._prompt_human_analise_conteudo = os.environ.get(
                "PROMPT_HUMAN_ANALISE_CONTEUDO"
            )
        return (
            self._prompt_human_analise_conteudo
            if self._prompt_human_analise_conteudo is not None
            else ""
        )

    @property
    def PROMPT_SYSTEM_ANALISE_CONTEUDO(self) -> str:
        """Retorna o prompt de sistema para análise de conteúdo."""
        if self._prompt_system_analise_conteudo is None:
            self._prompt_system_analise_conteudo = os.environ.get(
                "PROMPT_SYSTEM_ANALISE_CONTEUDO"
            )
        return (
            self._prompt_system_analise_conteudo
            if self._prompt_system_analise_conteudo is not None
            else ""
        )

    @property
    def TEMPERATURE(self) -> int:
        """Retorna a temperatura para o modelo de linguagem."""
        if self._temperature is None:
            self._temperature = int(os.environ.get("TEMPERATURE", "0"))
        return self._temperature if self._temperature is not None else 0

    @property
    def MODEL(self) -> str:
        """Retorna o nome do modelo de linguagem."""
        if self._model is None:
            self._model = os.environ.get("MODEL", "llama3.1")
        return self._model if self._model is not None else "llama3.1"

    @property
    def WHATSAPP_API_BASE_URL(self) -> str:
        """Retorna a URL base para a API do WhatsApp."""
        if self._whatsapp_api_base_url is None:
            self._whatsapp_api_base_url = os.environ.get("WHATSAPP_API_BASE_URL")
        return (
            self._whatsapp_api_base_url
            if self._whatsapp_api_base_url is not None
            else ""
        )

    @property
    def WHATSAPP_API_SEND_TEXT_URL(self) -> str:
        """Retorna a URL completa para o endpoint de envio de texto."""
        base = self.WHATSAPP_API_BASE_URL
        return f"{base}/v1/utils/send_text" if base else ""

    @property
    def WHATSAPP_API_START_TYPING_URL(self) -> str:
        """Retorna a URL completa para o endpoint de iniciar digitação."""
        base = self.WHATSAPP_API_BASE_URL
        return f"{base}/v1/utils/start_typing" if base else ""

    @property
    def WHATSAPP_API_STOP_TYPING_URL(self) -> str:
        """Retorna a URL completa para o endpoint de parar digitação."""
        base = self.WHATSAPP_API_BASE_URL
        return f"{base}/v1/utils/stop_typing" if base else ""

    @property
    def LLM_CLASS(self) -> Type[BaseChatModel]:
        """Retorna a classe do LLM. Resolve e armazena em cache se não estiver definida."""
        if self._llm_class is None:
            self._llm_class = self._get_llm_class()
        return self._llm_class

    @property
    def EMBEDDINGS_CLASS(self) -> Type[Embeddings]:
        """Retorna a classe de embeddings. Resolve e armazena em cache se não estiver definida."""
        if self._embeddings_class is None:
            self._embeddings_class = self._get_embeddings_class()
        return self._embeddings_class

    @property
    def PROMPT_SYSTEM_ANALISE_PREVIA_MENSAGEM(self) -> str:
        """Retorna o prompt de sistema para análise prévia de mensagem."""
        if self._prompt_system_analise_previa_mensagem is None:
            self._prompt_system_analise_previa_mensagem = os.environ.get(
                "PROMPT_SYSTEM_ANALISE_PREVIA_MENSAGEM"
            )
        return (
            self._prompt_system_analise_previa_mensagem
            if self._prompt_system_analise_previa_mensagem is not None
            else ""
        )

    @property
    def PROMPT_HUMAN_ANALISE_PREVIA_MENSAGEM(self) -> str:
        """Retorna o prompt humano para análise prévia de mensagem."""
        if self._prompt_human_analise_previa_mensagem is None:
            self._prompt_human_analise_previa_mensagem = os.environ.get(
                "PROMPT_HUMAN_ANALISE_PREVIA_MENSAGEM"
            )
        return (
            self._prompt_human_analise_previa_mensagem
            if self._prompt_human_analise_previa_mensagem is not None
            else ""
        )

    @property
    def VALID_INTENT_TYPES(self) -> str:
        """Retorna uma string JSON com intenções válidas, ou vazia se não definida."""
        if self._valid_intent_types is None:
            self._valid_intent_types = os.environ.get("VALID_INTENT_TYPES")
        return (
            self._valid_intent_types
            if self._valid_intent_types is not None
            else ""
        )

    @property
    def VALID_ENTITY_TYPES(self) -> str:
        """Retorna uma string JSON com entidades válidas, ou vazia se não definida."""
        if self._valid_entity_types is None:
            self._valid_entity_types = os.environ.get("VALID_ENTITY_TYPES")
        return (
            self._valid_entity_types
            if self._valid_entity_types is not None
            else ""
        )

    def _get_llm_class(self) -> Type[BaseChatModel]:
        """Retorna a classe do LLM com base na variável de ambiente.

        Raises:
            ValueError: Se a classe LLM especificada não for reconhecida.
        """
        llm_type = os.environ.get("LLM_CLASS", "ChatOllama")
        if llm_type == "ChatGroq":
            from langchain_groq import ChatGroq

            return ChatGroq
        elif llm_type == "ChatOpenAI":
            from langchain_openai import ChatOpenAI

            return ChatOpenAI
        elif llm_type == "ChatOllama":
            from langchain_ollama import ChatOllama

            return ChatOllama
        else:
            raise ValueError(
                f"Classe LLM '{llm_type}' não reconhecida. "
                "Defina a variável de ambiente 'LLM_CLASS' como 'ChatGroq', "
                "'ChatOpenAI' ou 'ChatOllama'."
            )

    def _get_embeddings_class(self) -> Type[Embeddings]:
        """Retorna a classe de embeddings com base na variável de ambiente.

        Mapeia nomes legados para classes compatíveis atuais de versões
        recentes do LangChain e pacotes parceiros. As importações são locais
        para evitar erros de importação quando a classe não é utilizada.

        Raises:
            ValueError: Se a classe de embeddings especificada não for reconhecida.
        """
        embeddings_class = os.environ.get(
            "EMBEDDINGS_CLASS", "HuggingFaceInferenceAPIEmbeddings"
        )

        if embeddings_class in (
            "HuggingFaceInferenceEmbeddings",
            "HuggingFaceInferenceAPIEmbeddings",
        ):
            from langchain_community.embeddings import (
                HuggingFaceInferenceAPIEmbeddings,
            )

            return HuggingFaceInferenceAPIEmbeddings
        elif embeddings_class == "HuggingFaceEndpointEmbeddings":
            from langchain_huggingface.embeddings import (
                HuggingFaceEndpointEmbeddings,
            )

            return HuggingFaceEndpointEmbeddings
        elif embeddings_class == "HuggingFaceEmbeddings":
            from langchain_huggingface import HuggingFaceEmbeddings

            return HuggingFaceEmbeddings
        elif embeddings_class == "OllamaEmbeddings":
            from langchain_ollama import OllamaEmbeddings

            return OllamaEmbeddings
        else:
            raise ValueError(
                (
                    f"Classe de embeddings '{embeddings_class}' não reconhecida. "
                    "Defina 'EMBEDDINGS_CLASS' como uma das seguintes: "
                    "'HuggingFaceInferenceAPIEmbeddings', "
                    "'HuggingFaceEndpointEmbeddings', "
                    "'HuggingFaceEmbeddings' ou 'OllamaEmbeddings'."
                )
            )


SERVICEHUB = ServiceHub()
