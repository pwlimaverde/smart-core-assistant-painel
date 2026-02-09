"""
Script para extrair prompts e configurações do Firebase Remote Config.

Este script carrega as variáveis de ambiente configuradas no sistema
e extrai apenas as relacionadas a prompts e mensagens da LLM,
salvando em um arquivo JSON para análise.

Uso:
    uv run python scripts/extrair_prompts_remote_config.py
"""

import json
import os
import sys
from pathlib import Path

# Adiciona o diretório src ao path para importar módulos do projeto
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


# Lista de variáveis de ambiente que o sistema usa (baseado no features_compose.py)
CONFIG_MAPPING = {
    # Api_Keys
    "GROQ_API_KEY": "API Key do Groq",
    "OPENAI_API_KEY": "API Key da OpenAI",
    "HUGGINGFACE_API_KEY": "API Key do HuggingFace",
    # LLM
    "LLM_CLASS": "Classe do LLM (ChatGroq, ChatOpenAI, ChatOllama)",
    "MODEL": "Nome do modelo de LLM",
    "LLM_TEMPERATURE": "Temperatura do LLM",
    # Prompts - Sistema (não editáveis pelo cliente)
    "PROMPT_SYSTEM_ANALISE_CONTEUDO": "Prompt para análise de conteúdo RAG",
    "PROMPT_HUMAN_ANALISE_CONTEUDO": "Prompt humano para análise de conteúdo",
    "PROMPT_SYSTEM_MELHORIA_CONTEUDO": "Prompt para melhoria de conteúdo",
    "PROMPT_HUMAN_MELHORIA_CONTEUDO": "Prompt humano para melhoria de conteúdo",
    "PROMPT_HUMAN_ANALISE_PREVIA_MENSAGEM": "Prompt humano para análise prévia",
    "PROMPT_SYSTEM_ANALISE_PREVIA_MENSAGEM": "Prompt sistema para análise prévia",
    # Prompts - Empresa (editáveis pelo cliente)
    "PROMPT_SYSTEM_ANALISE_MENSAGEM": "Prompt para geração de resposta",
    "PROMPT_SYSTEM_DADOS_EMPRESA": "Dados e contexto da empresa",
    "PROMPT_REGRAS_RESPOSTA": "Regras de tom e estilo de resposta",
    "PROMPT_REGRAS_TRANSFERENCIA": "Regras de transferência para humano",
    "PROMPT_TEMPLATE_USER_RAG": "Template de usuário com RAG",
    "PROMPT_INTENT_SYSTEM": "Prompt sistema para intenções",
    "PROMPT_INTENT_FOOTER": "Rodapé do prompt de intenções",
    # Mensagens
    "MSG_FALLBACK_SEM_INFO": "Mensagem quando não há informações",
    "MSG_FALLBACK_GERAL": "Mensagem fallback genérica",
    "MSG_TRANSFERENCIA_GENERICA": "Mensagem ao transferir atendimento",
    # Embeddings
    "CHUNK_OVERLAP": "Overlap de chunks",
    "CHUNK_SIZE": "Tamanho de chunks",
    "EMBEDDINGS_MODEL": "Modelo de embeddings",
    "EMBEDDINGS_CLASS": "Classe de embeddings",
    # Utilitarios
    "VALID_ENTITY_TYPES": "Tipos de entidades válidas",
    "TIME_CACHE": "Tempo de cache",
    "SIMILARITY_THRESHOLD": "Limiar de similaridade",
    "VECTOR_DISTANCE_THRESHOLD": "Limiar de distância vetorial",
}


def load_remote_config() -> None:
    """Carrega as variáveis do Firebase Remote Config."""
    try:
        from smart_core_assistant_painel.modules.services.features.features_compose import (
            FeaturesCompose,
        )

        # Chama o método estático que carrega o Remote Config
        FeaturesCompose.set_environ_remote()
        print("✅ Remote Config carregado com sucesso!")
    except Exception as e:
        print(f"⚠️ Erro ao carregar Remote Config: {e}")
        print("Continuando com variáveis de ambiente atuais...")


def extract_prompts() -> dict:
    """Extrai todas as variáveis de ambiente relacionadas a prompts."""
    prompts = {}

    for key in CONFIG_MAPPING.keys():
        value = os.environ.get(key, "")
        if value:
            prompts[key] = value

    return prompts


def categorize_prompts(prompts: dict) -> dict:
    """Categoriza os prompts por tipo para edição pelo cliente."""
    categories = {
        "editaveis_pelo_cliente": {
            "dados_empresa": {},
            "mensagens": {},
        },
        "gerenciados_pelo_sistema": {
            "prompts_tecnicos": {},
            "configuracoes": {},
        },
    }

    # Prompts editáveis pelo cliente
    cliente_prompts = [
        "PROMPT_SYSTEM_DADOS_EMPRESA",
        "PROMPT_REGRAS_RESPOSTA",
        "PROMPT_REGRAS_TRANSFERENCIA",
        "PROMPT_SYSTEM_ANALISE_MENSAGEM",
    ]

    cliente_mensagens = [
        "MSG_FALLBACK_SEM_INFO",
        "MSG_FALLBACK_GERAL",
        "MSG_TRANSFERENCIA_GENERICA",
    ]

    for key, value in prompts.items():
        if key in cliente_prompts:
            categories["editaveis_pelo_cliente"]["dados_empresa"][key] = {
                "descricao": CONFIG_MAPPING.get(key, ""),
                "valor": value,
            }
        elif key in cliente_mensagens:
            categories["editaveis_pelo_cliente"]["mensagens"][key] = {
                "descricao": CONFIG_MAPPING.get(key, ""),
                "valor": value,
            }
        elif key.startswith("PROMPT_"):
            categories["gerenciados_pelo_sistema"]["prompts_tecnicos"][key] = {
                "descricao": CONFIG_MAPPING.get(key, ""),
                "valor": value,
            }
        else:
            categories["gerenciados_pelo_sistema"]["configuracoes"][key] = {
                "descricao": CONFIG_MAPPING.get(key, ""),
                "valor": value,
            }

    return categories


def main() -> None:
    """Função principal."""
    print("=" * 60)
    print("Extrator de Prompts do Remote Config")
    print("=" * 60)

    # Carrega o Remote Config
    load_remote_config()

    # Extrai os prompts
    prompts = extract_prompts()

    if not prompts:
        print("❌ Nenhum prompt encontrado nas variáveis de ambiente.")
        return

    print(f"\n📊 {len(prompts)} variáveis encontradas:")
    for key in sorted(prompts.keys()):
        value_preview = (
            prompts[key][:50] + "..."
            if len(prompts[key]) > 50
            else prompts[key]
        )
        print(f"  - {key}: {value_preview}")

    # Categoriza os prompts
    categorized = categorize_prompts(prompts)

    # Conta por categoria
    editaveis = len(
        categorized["editaveis_pelo_cliente"]["dados_empresa"]
    ) + len(categorized["editaveis_pelo_cliente"]["mensagens"])
    sistema = len(
        categorized["gerenciados_pelo_sistema"]["prompts_tecnicos"]
    ) + len(categorized["gerenciados_pelo_sistema"]["configuracoes"])

    # Prepara o output
    output = {
        "resumo": {
            "total_variaveis": len(prompts),
            "editaveis_pelo_cliente": editaveis,
            "gerenciados_pelo_sistema": sistema,
        },
        "categorizado": categorized,
    }

    # Salva em JSON
    output_path = (
        Path(__file__).parent.parent
        / "docs_dev"
        / "prompts_remote_config.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Arquivo salvo em: {output_path}")
    print("\n📁 Resumo:")
    print(f"  - Editáveis pelo cliente: {editaveis}")
    print(f"  - Gerenciados pelo sistema: {sistema}")


if __name__ == "__main__":
    main()
