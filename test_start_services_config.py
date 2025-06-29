#!/usr/bin/env python
"""
Script de teste para verificar se o VetorStorage é configurado corretamente
no start_services ao invés de usar auto-configuração.
"""

import sys
from pathlib import Path

# Adiciona o diretório src ao path para importar os módulos
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_start_services_vetor_storage():
    """Testa se o VetorStorage é configurado no start_services."""
    print("=== Teste de Configuração no start_services ===")

    try:
        from smart_core_assistant_painel.modules.services.features.service_hub import (
            SERVICEHUB, )
        from smart_core_assistant_painel.modules.services.start_services import (
            start_services, )

        # Limpa configuração existente para simular estado inicial
        SERVICEHUB._vetor_storage = None
        print(f"Estado inicial - VetorStorage: {SERVICEHUB._vetor_storage}")

        # Executa start_services
        print("Executando start_services...")
        start_services()

        # Verifica se foi configurado
        vetor_storage = SERVICEHUB._vetor_storage
        print(
            f"Após start_services - VetorStorage: {
                type(vetor_storage).__name__ if vetor_storage else 'None'}")

        # Testa acesso via propriedade
        vetor_storage_via_property = SERVICEHUB.vetor_storage
        print(
            f"Via propriedade - VetorStorage: {type(vetor_storage_via_property).__name__}")

        if vetor_storage is not None and vetor_storage is vetor_storage_via_property:
            print("✅ VetorStorage configurado corretamente no start_services!")
            return True
        else:
            print("❌ VetorStorage não foi configurado corretamente.")
            return False

    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fallback_behavior():
    """Testa o comportamento de fallback caso não seja configurado no start_services."""
    print("\n=== Teste de Comportamento Fallback ===")

    try:
        from smart_core_assistant_painel.modules.services.features.service_hub import (
            ServiceHub, )

        # Cria nova instância para simular processo sem start_services
        hub = ServiceHub()
        hub._vetor_storage = None  # Simula não configurado

        print("Acessando VetorStorage sem configuração prévia...")
        vetor_storage = hub.vetor_storage

        print(f"VetorStorage fallback: {type(vetor_storage).__name__}")

        if vetor_storage is not None:
            print("✅ Fallback funcionando corretamente!")
            return True
        else:
            print("❌ Fallback não funcionou.")
            return False

    except Exception as e:
        print(f"❌ Erro no teste de fallback: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_singleton_consistency():
    """Testa se o singleton mantém consistência."""
    print("\n=== Teste de Consistência Singleton ===")

    try:
        from smart_core_assistant_painel.modules.services.features.service_hub import (
            SERVICEHUB, ServiceHub, )

        # Testa se são a mesma instância
        hub1 = SERVICEHUB
        hub2 = ServiceHub()

        print(f"SERVICEHUB ID: {id(hub1)}")
        print(f"ServiceHub() ID: {id(hub2)}")
        print(f"São a mesma instância: {hub1 is hub2}")

        # Testa se VetorStorage é o mesmo
        vs1 = hub1.vetor_storage
        vs2 = hub2.vetor_storage

        print(f"VetorStorage1 ID: {id(vs1)}")
        print(f"VetorStorage2 ID: {id(vs2)}")
        print(f"VetorStorages são iguais: {vs1 is vs2}")

        if hub1 is hub2 and vs1 is vs2:
            print("✅ Singleton mantém consistência!")
            return True
        else:
            print("❌ Problema de consistência no singleton.")
            return False

    except Exception as e:
        print(f"❌ Erro no teste de singleton: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Testando configuração do VetorStorage no start_services...\n")

    try:
        # Executa os testes
        test1 = test_start_services_vetor_storage()
        test2 = test_fallback_behavior()
        test3 = test_singleton_consistency()

        print("\n=== Resultados dos Testes ===")
        print(
            f"Configuração start_services: {
                '✅ PASSOU' if test1 else '❌ FALHOU'}")
        print(f"Comportamento fallback: {'✅ PASSOU' if test2 else '❌ FALHOU'}")
        print(f"Consistência singleton: {'✅ PASSOU' if test3 else '❌ FALHOU'}")

        if all([test1, test2, test3]):
            print("\n🎉 Todos os testes passaram!")
            print("VetorStorage será configurado no start_services e fallback funciona!")
        else:
            print("\n⚠️ Alguns testes falharam. Verifique a implementação.")

    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
