#!/usr/bin/env python
"""
Script de teste para verificar o funcionamento do ServiceHub singleton
e a auto-configuração do VetorStorage.
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório src ao path para importar os módulos
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_singleton_behavior():
    """Testa o comportamento singleton do ServiceHub."""
    print("=== Teste do Singleton ServiceHub ===")

    # Importa após adicionar ao path
    from smart_core_assistant_painel.modules.services.features.service_hub import (
        SERVICEHUB, )

    # Testa se duas instâncias são a mesma
    hub1 = SERVICEHUB

    # Simula um novo import (como aconteceria em um processo worker)
    from smart_core_assistant_painel.modules.services.features.service_hub import (
        ServiceHub, )
    hub2 = ServiceHub()

    print(f"Hub1 ID: {id(hub1)}")
    print(f"Hub2 ID: {id(hub2)}")
    print(f"São a mesma instância: {hub1 is hub2}")

    return hub1 is hub2


def test_auto_configure_vetor_storage():
    """Testa a auto-configuração do VetorStorage."""
    print("\n=== Teste da Auto-configuração do VetorStorage ===")

    from smart_core_assistant_painel.modules.services.features.service_hub import (
        SERVICEHUB, )

    # Simula um processo worker onde o vetor_storage não foi configurado
    SERVICEHUB._vetor_storage = None

    try:
        # Tenta acessar vetor_storage (deve auto-configurar)
        vetor_storage = SERVICEHUB.vetor_storage
        print(f"VetorStorage auto-configurado: {type(vetor_storage).__name__}")
        print("✅ Auto-configuração funcionou!")
        return True
    except Exception as e:
        print(f"❌ Erro na auto-configuração: {e}")
        return False


def test_environment_variables():
    """Testa se as variáveis de ambiente são carregadas corretamente."""
    print("\n=== Teste de Variáveis de Ambiente ===")

    from smart_core_assistant_painel.modules.services.features.service_hub import (
        SERVICEHUB, )

    # Define uma variável de ambiente temporária
    os.environ['CHUNK_SIZE'] = '1500'
    os.environ['CHUNK_OVERLAP'] = '300'

    # Força recarregamento
    SERVICEHUB._chunk_size = None
    SERVICEHUB._chunk_overlap = None

    print(f"CHUNK_SIZE: {SERVICEHUB.CHUNK_SIZE}")
    print(f"CHUNK_OVERLAP: {SERVICEHUB.CHUNK_OVERLAP}")

    # Limpa as variáveis de teste
    del os.environ['CHUNK_SIZE']
    del os.environ['CHUNK_OVERLAP']

    return SERVICEHUB.CHUNK_SIZE == 1500 and SERVICEHUB.CHUNK_OVERLAP == 300


if __name__ == "__main__":
    print("Iniciando testes do ServiceHub...\n")

    try:
        # Executa os testes
        test1 = test_singleton_behavior()
        test2 = test_auto_configure_vetor_storage()
        test3 = test_environment_variables()

        print("\n=== Resultados dos Testes ===")
        print(f"Singleton: {'✅ PASSOU' if test1 else '❌ FALHOU'}")
        print(f"Auto-configuração: {'✅ PASSOU' if test2 else '❌ FALHOU'}")
        print(f"Variáveis de ambiente: {'✅ PASSOU' if test3 else '❌ FALHOU'}")

        if all([test1, test2, test3]):
            print("\n🎉 Todos os testes passaram!")
        else:
            print("\n⚠️ Alguns testes falharam. Verifique a configuração.")

    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
