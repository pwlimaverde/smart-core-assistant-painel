from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RuntimeConfig:
    """Configuração de runtime - imutável e thread-safe.

    Esta classe contém todas as configurações necessárias para a execução
    dos serviços de IA e lógica de negócios, resolvidas dinamicamente
    por requisição (tenant + core).
    """

    # === API Keys ===
    groq_api_key: str = ""
    openai_api_key: str = ""
    huggingface_api_key: str = ""

    # === LLM ===
    llm_class: str = "ChatGroq"
    model: str = "openai/gpt-oss-20b"
    llm_temperature: int = 0

    # === Transcrição de Áudio ===
    transcription_provider: str = "openai"
    transcription_model: str = "whisper-1"

    # === Prompts do Sistema ===
    prompt_system_analise_mensagem: str = ""
    prompt_system_analise_previa_mensagem: str = ""
    prompt_human_analise_previa_mensagem: str = ""
    prompt_system_melhoria_conteudo: str = ""
    prompt_human_melhoria_conteudo: str = ""
    prompt_system_analise_conteudo: str = ""
    prompt_human_analise_conteudo: str = ""
    prompt_intent_system: str = ""
    prompt_intent_footer: str = ""
    prompt_template_user_rag: str = ""
    prompt_regras_resposta: str = ""
    prompt_regras_transferencia: str = ""

    # === Prompts do Tenant ===
    prompt_system_dados_empresa: str = ""

    # === Mensagens ===
    msg_fallback_sem_info: str = ""
    msg_fallback_geral: str = ""
    msg_transferencia_generica: str = ""

    # === Embeddings ===
    embeddings_class: str = "OpenAIEmbeddings"
    embeddings_model: str = ""
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # === Thresholds ===
    similarity_threshold: float = 0.4
    vector_distance_threshold: float = 0.5
    time_cache: int = 20

    # === Utilitários ===
    valid_entity_types: str = ""


# ContextVar para armazenar config por requisição/task
_current_config: ContextVar[Optional[RuntimeConfig]] = ContextVar(
    "current_config", default=None
)


def set_config(config: RuntimeConfig) -> None:
    """Define a configuração para o contexto atual."""
    _current_config.set(config)


def get_config() -> RuntimeConfig:
    """Obtém a configuração do contexto atual.

    Levanta RuntimeError se não houver config definida.
    """
    config = _current_config.get()
    if config is None:
        raise RuntimeError(
            "Configuração não definida. "
            "Certifique-se de que o TenantConfigMiddleware foi executado "
            "ou que set_config() foi chamado manualmente."
        )
    return config


def get_config_or_default() -> RuntimeConfig:
    """Obtém config ou retorna default (para scripts/testes onde o middleware não roda)."""
    config = _current_config.get()
    return config if config else RuntimeConfig()
