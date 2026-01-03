from .context import get_config, RuntimeConfig


class ConfigProvider:
    """Provê acesso às configurações de forma desacoplada do Django.

    Os módulos (ai_engine, services) usam esta classe ao invés de
    acessar variáveis de ambiente ou modelos Django diretamente.
    """

    @staticmethod
    def get() -> RuntimeConfig:
        """Retorna a configuração atual do contexto."""
        return get_config()

    # === Atalhos para configs frequentes ===

    @staticmethod
    def groq_api_key() -> str:
        return get_config().groq_api_key

    @staticmethod
    def openai_api_key() -> str:
        return get_config().openai_api_key

    @staticmethod
    def huggingface_api_key() -> str:
        return get_config().huggingface_api_key

    @staticmethod
    def model() -> str:
        return get_config().model

    @staticmethod
    def llm_class() -> str:
        return get_config().llm_class

    @staticmethod
    def prompt(name: str) -> str:
        """Retorna prompt pelo nome.

        Args:
            name: Nome do atributo na RuntimeConfig (ex: 'prompt_system_analise_mensagem')
        """
        config = get_config()
        # Garante que acessa apenas atributos existentes
        if not hasattr(config, name):
            raise AttributeError(
                f"Prompt/Configuração '{name}' não existe em RuntimeConfig."
            )
        return getattr(config, name, "")
