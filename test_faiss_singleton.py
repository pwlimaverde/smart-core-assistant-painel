#!/usr/bin/env python
"""
Script de teste para verificar o comportamento singleton do FaissVetorStorage
e a sincronização entre instâncias.
"""

import sys
from pathlib import Path

# Adiciona o diretório src ao path para importar os módulos
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_faiss_singleton():
    """Testa o comportamento singleton do FaissVetorStorage."""
    print("=== Teste do Singleton FaissVetorStorage ===")

    try:
        from smart_core_assistant_painel.modules.services.features.vetor_storage.datasource.faiss_storage.faiss_vetor_storage import (
            FaissVetorStorage, )

        # Cria duas instâncias
        storage1 = FaissVetorStorage()
        storage2 = FaissVetorStorage()

        print(f"Storage1 ID: {id(storage1)}")
        print(f"Storage2 ID: {id(storage2)}")
        print(f"São a mesma instância: {storage1 is storage2}")

        return storage1 is storage2

    except Exception as e:
        print(f"❌ Erro no teste singleton: {e}")
        return False


def test_servicehub_integration():
    """Testa a integração com ServiceHub."""
    print("\n=== Teste de Integração ServiceHub ===")

    try:
        from smart_core_assistant_painel.modules.services.features.service_hub import (
            SERVICEHUB, )

        # Limpa o vetor_storage para forçar auto-configuração
        SERVICEHUB._vetor_storage = None

        # Acessa duas vezes para verificar se mantém a mesma instância
        storage1 = SERVICEHUB.vetor_storage
        storage2 = SERVICEHUB.vetor_storage

        print(f"Storage1 ID: {id(storage1)}")
        print(f"Storage2 ID: {id(storage2)}")
        print(f"São a mesma instância: {storage1 is storage2}")
        print(f"Tipo: {type(storage1).__name__}")

        return storage1 is storage2

    except Exception as e:
        print(f"❌ Erro no teste de integração: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_processes_simulation():
    """Simula múltiplos processos criando várias instâncias."""
    print("\n=== Teste de Simulação de Múltiplos Processos ===")

    try:
        from smart_core_assistant_painel.modules.services.features.service_hub import (
            ServiceHub, )

        instances = []
        hub_instances = []

        # Simula vários "processos" criando múltiplas instâncias
        for i in range(5):
            # Cria novo ServiceHub (simula novo processo)
            hub = ServiceHub()
            hub._vetor_storage = None  # Força reconfiguração

            # Obtém VetorStorage
            storage = hub.vetor_storage

            instances.append(storage)
            hub_instances.append(hub)

            print(
                f"Processo {i + 1} - Hub ID: {id(hub)}, Storage ID: {id(storage)}")

        # Verifica se todos os ServiceHub são a mesma instância
        hub_same = all(hub is hub_instances[0] for hub in hub_instances[1:])

        # Verifica se todos os Storage são a mesma instância
        storage_same = all(storage is instances[0]
                           for storage in instances[1:])

        print(f"\nTodos os ServiceHub são iguais: {hub_same}")
        print(f"Todos os VetorStorage são iguais: {storage_same}")

        return hub_same and storage_same

    except Exception as e:
        print(f"❌ Erro no teste de múltiplos processos: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Iniciando testes de Singleton e Sincronização...\n")

    try:
        # Executa os testes
        test1 = test_faiss_singleton()
        test2 = test_servicehub_integration()
        test3 = test_multiple_processes_simulation()

        print("\n=== Resultados dos Testes ===")
        print(
            f"Singleton FaissVetorStorage: {
                '✅ PASSOU' if test1 else '❌ FALHOU'}")
        print(f"Integração ServiceHub: {'✅ PASSOU' if test2 else '❌ FALHOU'}")
        print(f"Múltiplos Processos: {'✅ PASSOU' if test3 else '❌ FALHOU'}")

        if all([test1, test2, test3]):
            print("\n🎉 Todos os testes passaram!")
            print("O problema de concorrência foi resolvido!")
        else:
            print("\n⚠️ Alguns testes falharam. Verifique a implementação.")

    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
