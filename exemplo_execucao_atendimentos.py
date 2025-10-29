"""
Exemplo de execução da construção completa de databases no Notion.

Este script demonstra como executar a construção de todas as databases
necessárias para a integração com o Notion, incluindo a nova funcionalidade
de atendimentos e mensagens.

Pré-requisitos:
1. Ter executado anteriormente: asyncio.run(run_construction_operacional())
2. Ter as variáveis de ambiente configuradas:
   - NOTION_TOKEN: Token de autenticação da API do Notion
   - NOTION_PAGE_ID: ID da página pai onde as databases serão criadas

Execução:
    python exemplo_execucao_atendimentos.py
"""

import asyncio
import os
import sys

# Adicionar o path do projeto
sys.path.append(os.path.dirname(__file__))

# Importar as funções necessárias
from src.smart_core_assistant_painel.app.notion_sync.scripts.script_constructor_notion import (
    run_construction_atendimentos,
    test_atendimentos_construction,
    run_full,
)


def main() -> None:
    """Função principal que demonstra diferentes formas de execução."""

    print("🚀 Exemplo de construção de databases no Notion")
    print("=" * 50)

    # Verificar variáveis de ambiente
    if not os.getenv("NOTION_TOKEN") or not os.getenv("NOTION_PAGE_ID"):
        print("❌ Configure as variáveis de ambiente:")
        print("   - NOTION_TOKEN")
        print("   - NOTION_PAGE_ID")
        return

    print("\nOpções de execução:")
    print("1. Apenas atendimentos (requer databases anteriores)")
    print("2. Testar construção de atendimentos")
    print("3. Execução completa (recomendado)")
    print("4. Sair")

    escolha = input("\nEscolha uma opção (1-4): ").strip()

    try:
        if escolha == "1":
            print("\n🎯 Executando apenas construção de atendimentos...")
            asyncio.run(run_construction_atendimentos())
            print("✅ Construção de atendimentos concluída!")

        elif escolha == "2":
            print("\n🧪 Testando construção de atendimentos...")
            test_atendimentos_construction()
            print("✅ Teste concluído!")

        elif escolha == "3":
            print("\n🚀 Executando construção completa...")
            run_full()
            print("✅ Construção completa concluída!")

        elif escolha == "4":
            print("\n👋 Encerrando...")
            return

        else:
            print("\n❌ Opção inválida!")
            return

    except KeyboardInterrupt:
        print("\n\n⏹️ Operação cancelada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante a execução: {e}")
        raise

    print("\n🎉 Operação concluída com sucesso!")
    print("📊 Acesse suas databases no Notion para verificar os resultados.")


if __name__ == "__main__":
    main()
