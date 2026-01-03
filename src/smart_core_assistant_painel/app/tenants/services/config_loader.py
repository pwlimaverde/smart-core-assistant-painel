import json
import time
from typing import Dict, Optional

from smart_core_assistant_painel.modules.services.config.context import (
    RuntimeConfig,
    set_config,
)
from smart_core_assistant_painel.app.settings_manager.models import (
    CoreSettings,
)
from smart_core_assistant_painel.app.tenants.models import Tenant, TenantConfig


class ConfigLoader:
    """Carrega configs do banco (Core e Tenant) e injeta no RuntimeConfig da requisição.

    Responsável por:
    1. Carregar configurações globais (CoreSettings) com cache.
    2. Carregar configurações do Tenant (TenantConfig) sem cache de aplicação (uso request).
    3. Fundir as configurações (Tenant override Core).
    4. Criar e injetar o objeto RuntimeConfig no ContextVar.
    """

    _core_cache: Optional[Dict[str, str]] = None
    _cache_timestamp: float = 0
    CACHE_TTL = 300  # 5 minutos

    @classmethod
    def load_for_request(cls, tenant: Optional[Tenant] = None) -> None:
        """Carrega configs e define no ContextVar para a requisição/task atual."""
        # 1. Carregar configs globais (com cache)
        core = cls._get_core_settings()

        # 2. Carregar configs do tenant (se houver)
        tenant_cfg = cls._get_tenant_config(tenant) if tenant else {}

        # 3. Mesclar e criar RuntimeConfig

        # Helper para resolver valores numéricos
        def get_int(key: str, default: int) -> int:
            val = core.get(key)
            if val and val.isdigit():
                return int(val)
            return default

        def get_float(key: str, default: float) -> float:
            val = core.get(key)
            if val:
                try:
                    return float(val)
                except ValueError:
                    pass
            return default

        # API Keys: Tenant tem prioridade sobre Core se configurado
        groq_api_key = tenant_cfg.get("groq_api_key") or core.get(
            "groq_api_key", ""
        )
        openai_api_key = tenant_cfg.get("openai_api_key") or core.get(
            "openai_api_key", ""
        )
        huggingface_api_key = tenant_cfg.get(
            "huggingface_api_key"
        ) or core.get("huggingface_api_key", "")

        config = RuntimeConfig(
            # === API Keys (tenant sobrescreve core) ===
            groq_api_key=groq_api_key,
            openai_api_key=openai_api_key,
            huggingface_api_key=huggingface_api_key,
            # === LLM ===
            llm_class=tenant_cfg.get("llm_class")
            or core.get("llm_class", "ChatGroq"),
            model=tenant_cfg.get("model")
            or core.get("model", "llama-3.1-70b-versatile"),
            llm_temperature=int(core.get("llm_temperature", "0")),
            # === Prompts do Sistema ===
            prompt_system_analise_previa_mensagem=core.get(
                "prompt_system_analise_previa_mensagem", ""
            ),
            prompt_human_analise_previa_mensagem=core.get(
                "prompt_human_analise_previa_mensagem", ""
            ),
            prompt_system_analise_conteudo=core.get(
                "prompt_system_analise_conteudo", ""
            ),
            prompt_human_analise_conteudo=core.get(
                "prompt_human_analise_conteudo", ""
            ),
            prompt_system_melhoria_conteudo=core.get(
                "prompt_system_melhoria_conteudo", ""
            ),
            prompt_human_melhoria_conteudo=core.get(
                "prompt_human_melhoria_conteudo", ""
            ),
            prompt_intent_system=core.get("prompt_intent_system", ""),
            prompt_intent_footer=core.get("prompt_intent_footer", ""),
            prompt_template_user_rag=core.get("prompt_template_user_rag", ""),
            # === Prompts do Tenant ===
            # Mapeamento: dados_empresa (tenant) → prompt_system_dados_empresa
            prompt_system_dados_empresa=tenant_cfg.get("dados_empresa", ""),
            # Mapeamento: persona_bot (tenant) → prompt_system_analise_mensagem
            # Se o tenant tem persona_bot, ele sobrescreve o padrão do sistema
            prompt_system_analise_mensagem=tenant_cfg.get("persona_bot")
            or core.get("prompt_system_analise_mensagem", ""),
            prompt_regras_resposta=core.get("prompt_regras_resposta", ""),
            prompt_regras_transferencia=core.get(
                "prompt_regras_transferencia", ""
            ),
            # === Mensagens ===
            msg_fallback_sem_info=tenant_cfg.get("msg_sem_info")
            or core.get("msg_fallback_sem_info", ""),
            msg_fallback_geral=tenant_cfg.get("msg_fallback")
            or core.get("msg_fallback_geral", ""),
            msg_transferencia_generica=tenant_cfg.get("msg_transferencia")
            or core.get("msg_transferencia_generica", ""),
            # === Embeddings ===
            embeddings_class=core.get("embeddings_class", "OpenAIEmbeddings"),
            embeddings_model=core.get("embeddings_model", ""),
            chunk_size=get_int("chunk_size", 1000),
            chunk_overlap=get_int("chunk_overlap", 200),
            # === Thresholds ===
            similarity_threshold=get_float("similarity_threshold", 0.4),
            vector_distance_threshold=get_float(
                "vector_distance_threshold", 0.5
            ),
            time_cache=get_int("time_cache", 20),
            # === Utilitários ===
            valid_entity_types=tenant_cfg.get("entity_types")
            or core.get("valid_entity_types", ""),
        )

        # 4. Injetar no contexto
        set_config(config)

    @classmethod
    def _get_core_settings(cls) -> Dict[str, str]:
        """Retorna configs do Core com cache em memória."""
        now = time.time()

        if cls._core_cache is not None and (
            now - cls._cache_timestamp < cls.CACHE_TTL
        ):
            return cls._core_cache

        settings_dict = {}
        # Assume o banco já está populado via script/load initial
        for obj in CoreSettings.objects.all():
            try:
                settings_dict[obj.key] = obj.get_value()
            except Exception:
                settings_dict[obj.key] = obj.value

        cls._core_cache = settings_dict
        cls._cache_timestamp = now
        return cls._core_cache

    @classmethod
    def _get_tenant_config(cls, tenant: Tenant) -> Dict[str, str]:
        """Retorna configs do tenant normalizadas."""
        try:
            cfg = tenant.config
            # Converter entity_types (dict) para string JSON se existir
            entity_types_str = ""
            if cfg.entity_types:
                entity_types_str = json.dumps(
                    cfg.entity_types, ensure_ascii=False
                )

            tenant_data: Dict[str, str] = {
                # Prompts do tenant
                "dados_empresa": cfg.dados_empresa,
                "persona_bot": cfg.persona_bot,
                # Mensagens
                "msg_sem_info": cfg.msg_sem_info,
                "msg_fallback": cfg.msg_fallback,
                "msg_transferencia": cfg.msg_transferencia,
                # LLM (campos explícitos, sobrescrevem Core se preenchidos)
                "llm_class": cfg.llm_class if cfg.llm_class else "",
                "model": cfg.model if cfg.model else "",
                # Entidades
                "entity_types": entity_types_str,
            }

            # API Keys do tenant (descriptografadas, sobrescrevem Core)
            groq_key = cfg.get_api_key("groq_api_key")
            if groq_key:
                tenant_data["groq_api_key"] = groq_key

            openai_key = cfg.get_api_key("openai_api_key")
            if openai_key:
                tenant_data["openai_api_key"] = openai_key

            huggingface_key = cfg.get_api_key("huggingface_api_key")
            if huggingface_key:
                tenant_data["huggingface_api_key"] = huggingface_key

            return tenant_data

        except (TenantConfig.DoesNotExist, AttributeError):
            return {}
        except Exception:
            return {}
