"""
Script de Diagnóstico e Correção das Configurações do CoreSettings.

Este script:
1. Lista todas as properties do ServiceHub que precisam de configuração
2. Compara com o RuntimeConfig (campos definidos)
3. Verifica o que está no CoreSettings (banco de dados)
4. Exibe diagnóstico completo de lacunas
5. Opcionalmente cria as entradas faltantes no CoreSettings

Uso:
    uv run python scripts/diagnostico_config.py
    uv run python scripts/diagnostico_config.py --fix  # Para criar entradas faltantes
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório src ao path para importar módulos do projeto
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Configurar Django antes de qualquer import Django
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.ui.core.settings",
)

import django

django.setup()


# Mapeamento COMPLETO: Nome no ServiceHub -> Nome no CoreSettings/RuntimeConfig
# Baseado no código original do Firebase Remote Config
SERVICE_HUB_TO_CORE_SETTINGS = {
    # === API Keys ===
    "HUGGINGFACE_API_KEY": {
        "core_key": "huggingface_api_key",
        "tipo": "api_key",
        "encrypted": True,
    },
    # Notas: GROQ_API_KEY e OPENAI_API_KEY já estão no core
    # === LLM ===
    "LLM_CLASS": {
        "core_key": "llm_class",
        "tipo": "llm",
        "encrypted": False,
        "default": "ChatGroq",
    },
    "MODEL": {
        "core_key": "model",
        "tipo": "llm",
        "encrypted": False,
        "default": "llama-3.1-70b-versatile",
    },
    "LLM_TEMPERATURE": {
        "core_key": "llm_temperature",
        "tipo": "llm",
        "encrypted": False,
        "default": "0",
    },
    # === Prompts do Sistema (Globais - CoreSettings) ===
    "PROMPT_SYSTEM_ANALISE_CONTEUDO": {
        "core_key": "prompt_system_analise_conteudo",
        "tipo": "prompt_sistema",
        "encrypted": False,
    },
    "PROMPT_HUMAN_ANALISE_CONTEUDO": {
        "core_key": "prompt_human_analise_conteudo",
        "tipo": "prompt_sistema",
        "encrypted": False,
    },
    "PROMPT_SYSTEM_MELHORIA_CONTEUDO": {
        "core_key": "prompt_system_melhoria_conteudo",
        "tipo": "prompt_sistema",
        "encrypted": False,
    },
    "PROMPT_HUMAN_MELHORIA_CONTEUDO": {
        "core_key": "prompt_human_melhoria_conteudo",
        "tipo": "prompt_sistema",
        "encrypted": False,
    },
    "PROMPT_HUMAN_ANALISE_PREVIA_MENSAGEM": {
        "core_key": "prompt_human_analise_previa_mensagem",
        "tipo": "prompt_sistema",
        "encrypted": False,
    },
    "PROMPT_SYSTEM_ANALISE_PREVIA_MENSAGEM": {
        "core_key": "prompt_system_analise_previa_mensagem",
        "tipo": "prompt_sistema",
        "encrypted": False,
    },
    "PROMPT_SYSTEM_ANALISE_MENSAGEM": {
        "core_key": "prompt_system_analise_mensagem",
        "tipo": "prompt_sistema",
        "encrypted": False,
    },
    "PROMPT_INTENT_SYSTEM": {
        "core_key": "prompt_intent_system",
        "tipo": "prompt_sistema",
        "encrypted": False,
    },
    "PROMPT_INTENT_FOOTER": {
        "core_key": "prompt_intent_footer",
        "tipo": "prompt_sistema",
        "encrypted": False,
    },
    "PROMPT_TEMPLATE_USER_RAG": {
        "core_key": "prompt_template_user_rag",
        "tipo": "prompt_sistema",
        "encrypted": False,
    },
    # === Prompts do Tenant (Editáveis pelo Cliente - TenantConfig) ===
    # Estes NÃO ficam no CoreSettings, ficam no TenantConfig
    "PROMPT_SYSTEM_DADOS_EMPRESA": {
        "tenant_key": "dados_empresa",
        "tipo": "prompt_tenant",
    },
    "PROMPT_REGRAS_RESPOSTA": {
        "tenant_key": "regras_resposta",
        "tipo": "prompt_tenant",
    },
    "PROMPT_REGRAS_TRANSFERENCIA": {
        "tenant_key": "regras_transferencia",
        "tipo": "prompt_tenant",
    },
    # === Mensagens (Mix: valores padrão no Core, override no Tenant) ===
    "MSG_FALLBACK_SEM_INFO": {
        "core_key": "msg_fallback_sem_info",
        "tenant_key": "msg_sem_info",
        "tipo": "mensagem",
        "encrypted": False,
    },
    "MSG_FALLBACK_GERAL": {
        "core_key": "msg_fallback_geral",
        "tenant_key": "msg_fallback",
        "tipo": "mensagem",
        "encrypted": False,
    },
    "MSG_TRANSFERENCIA_GENERICA": {
        "core_key": "msg_transferencia_generica",
        "tenant_key": "msg_transferencia",
        "tipo": "mensagem",
        "encrypted": False,
    },
    # === Embeddings ===
    "CHUNK_OVERLAP": {
        "core_key": "chunk_overlap",
        "tipo": "embedding",
        "encrypted": False,
        "default": "200",
    },
    "CHUNK_SIZE": {
        "core_key": "chunk_size",
        "tipo": "embedding",
        "encrypted": False,
        "default": "1000",
    },
    "EMBEDDINGS_MODEL": {
        "core_key": "embeddings_model",
        "tipo": "embedding",
        "encrypted": False,
    },
    "EMBEDDINGS_CLASS": {
        "core_key": "embeddings_class",
        "tipo": "embedding",
        "encrypted": False,
        "default": "OpenAIEmbeddings",
    },
    # === Utilitários ===
    "VALID_ENTITY_TYPES": {
        "core_key": "valid_entity_types",
        "tenant_key": "entity_types",  # Agora é configuração do Tenant!
        "tipo": "util_tenant",
        "encrypted": False,
        "nota": "JSON com tipos de entidade - editável pelo cliente",
    },
    "TIME_CACHE": {
        "core_key": "time_cache",
        "tipo": "util",
        "encrypted": False,
        "default": "20",
    },
    "SIMILARITY_THRESHOLD": {
        "core_key": "similarity_threshold",
        "tipo": "threshold",
        "encrypted": False,
        "default": "0.4",
    },
    "VECTOR_DISTANCE_THRESHOLD": {
        "core_key": "vector_distance_threshold",
        "tipo": "threshold",
        "encrypted": False,
        "default": "0.5",
    },
}


def get_core_settings() -> dict[str, str]:
    """Busca todas as configurações do CoreSettings no banco."""
    from smart_core_assistant_painel.app.settings_manager.models import (
        CoreSettings,
    )

    settings = {}
    for obj in CoreSettings.objects.all():
        try:
            settings[obj.key] = obj.get_value()
        except Exception:
            settings[obj.key] = obj.value
    return settings


def get_runtime_config_fields() -> set[str]:
    """Retorna os campos definidos no RuntimeConfig."""
    from smart_core_assistant_painel.modules.services.config.context import (
        RuntimeConfig,
    )
    from dataclasses import fields

    return {f.name for f in fields(RuntimeConfig)}


def diagnose() -> dict:
    """Executa o diagnóstico completo."""
    core_settings = get_core_settings()
    runtime_fields = get_runtime_config_fields()

    result = {
        "core_settings_existentes": [],
        "core_settings_faltantes": [],
        "runtime_config_nao_mapeados": [],
        "tenant_config_campos": [],
        "detalhes": {},
    }

    for hub_name, config in SERVICE_HUB_TO_CORE_SETTINGS.items():
        core_key = config.get("core_key")
        tenant_key = config.get("tenant_key")
        tipo = config.get("tipo", "")

        detail = {
            "hub_name": hub_name,
            "core_key": core_key,
            "tenant_key": tenant_key,
            "tipo": tipo,
            "core_exists": False,
            "core_value": None,
            "runtime_exists": False,
            "default": config.get("default"),
        }

        # Verificar CoreSettings
        if core_key:
            if core_key in core_settings:
                detail["core_exists"] = True
                value = core_settings[core_key]
                detail["core_value"] = (
                    value[:50] + "..." if len(str(value)) > 50 else value
                )
                result["core_settings_existentes"].append(core_key)
            else:
                result["core_settings_faltantes"].append(core_key)

            # Verificar RuntimeConfig
            if core_key in runtime_fields:
                detail["runtime_exists"] = True
            else:
                result["runtime_config_nao_mapeados"].append(core_key)

        # Verificar campos do Tenant
        if tenant_key:
            result["tenant_config_campos"].append(tenant_key)

        result["detalhes"][hub_name] = detail

    return result


def print_diagnosis(result: dict) -> None:
    """Imprime o diagnóstico de forma organizada."""
    print("\n" + "=" * 70)
    print("DIAGNOSTICO DE CONFIGURACOES")
    print("=" * 70)

    # Resumo
    print(
        f"\n[OK] CoreSettings existentes: {len(result['core_settings_existentes'])}"
    )
    print(
        f"[FALTA] CoreSettings faltantes: {len(result['core_settings_faltantes'])}"
    )
    print(
        f"[WARN] RuntimeConfig nao mapeados: {len(result['runtime_config_nao_mapeados'])}"
    )
    print(
        f"[TENANT] Campos TenantConfig: {len(result['tenant_config_campos'])}"
    )

    # Detalhes dos faltantes
    if result["core_settings_faltantes"]:
        print("\n" + "-" * 70)
        print(
            "[FALTA] CORE SETTINGS FALTANTES (precisam ser criados no banco):"
        )
        print("-" * 70)
        for key in result["core_settings_faltantes"]:
            # Buscar o hub_name correspondente
            for hub_name, detail in result["detalhes"].items():
                if detail.get("core_key") == key:
                    default = detail.get("default", "(sem default)")
                    print(f"  - {key:<45} (default: {default})")
                    break

    # RuntimeConfig não mapeados
    if result["runtime_config_nao_mapeados"]:
        print("\n" + "-" * 70)
        print("[WARN] CAMPOS NAO MAPEADOS NO RUNTIME CONFIG:")
        print("-" * 70)
        for key in result["runtime_config_nao_mapeados"]:
            print(f"  - {key}")

    # Detalhes por tipo
    print("\n" + "-" * 70)
    print("DETALHES POR TIPO:")
    print("-" * 70)

    by_type: dict[str, list] = {}
    for hub_name, detail in result["detalhes"].items():
        tipo = detail.get("tipo", "outro")
        if tipo not in by_type:
            by_type[tipo] = []
        by_type[tipo].append((hub_name, detail))

    for tipo, items in sorted(by_type.items()):
        print(f"\n[{tipo.upper()}]")
        for hub_name, detail in items:
            core_status = "OK" if detail["core_exists"] else "FALTA"
            runtime_status = "OK" if detail["runtime_exists"] else "WARN"
            core_key = detail.get("core_key", "-")
            tenant_key = detail.get("tenant_key", "-")

            if detail.get("core_key"):
                print(
                    f"  {hub_name:<40} Core:{core_status} Runtime:{runtime_status} -> {core_key}"
                )
            else:
                print(f"  {hub_name:<40} (TenantConfig: {tenant_key})")


def fix_missing_core_settings(result: dict) -> None:
    """Cria as entradas faltantes no CoreSettings."""
    from smart_core_assistant_painel.app.settings_manager.models import (
        CoreSettings,
    )

    print("\n" + "=" * 70)
    print("CORRECAO: Criando entradas faltantes no CoreSettings")
    print("=" * 70)

    created = 0
    for key in result["core_settings_faltantes"]:
        # Buscar o hub_name correspondente para pegar o default
        for hub_name, detail in result["detalhes"].items():
            if detail.get("core_key") == key:
                # Usar string vazia se não houver default (None)
                default = detail.get("default")
                if default is None:
                    default = ""
                encrypted = SERVICE_HUB_TO_CORE_SETTINGS.get(hub_name, {}).get(
                    "encrypted", False
                )

                # Criar entrada
                CoreSettings.objects.get_or_create(
                    key=key,
                    defaults={
                        "value": default,
                        "encrypted": encrypted,
                        "description": f"Configuração para {hub_name}",
                    },
                )
                print(
                    f"  [OK] Criado: {key} = '{default}' (encrypted: {encrypted})"
                )
                created += 1
                break

    print(f"\n[OK] Total de entradas criadas: {created}")


def main() -> None:
    """Função principal."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Diagnóstico de configurações"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Criar entradas faltantes no CoreSettings",
    )
    args = parser.parse_args()

    # Executar diagnóstico
    result = diagnose()
    print_diagnosis(result)

    # Corrigir se solicitado
    if args.fix and result["core_settings_faltantes"]:
        fix_missing_core_settings(result)
        print(
            "\n[DICA] Execute com --fix para criar as entradas faltantes automaticamente."
        )


if __name__ == "__main__":
    main()
