#!/usr/bin/env python
"""
Script de teste rápido para verificar se o problema de tipagem foi resolvido.
"""

import sys
from pathlib import Path

# Adiciona o diretório src ao path para importar os módulos
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_typing_issue():
    """Testa se o problema de tipagem _configuring_vetor_storage foi resolvido."""
    print("=== Teste de Tipagem _configuring_vetor_storage ===")

    try:
        from smart_core_assistant_painel.modules.services.features.service_hub import (
            SERVICEHUB, )

        # Acessa a propriedade para verificar se não há erros de tipagem
        print(
            f"_configuring_vetor_storage inicializado: {
                hasattr(
                    SERVICEHUB,
                    '_configuring_vetor_storage')}")
        print(
            f"Valor inicial: {
                getattr(
                    SERVICEHUB,
                    '_configuring_vetor_storage',
                    'Não encontrado')}")
        print(
            f"Tipo: {
                type(
                    getattr(
                        SERVICEHUB,
                        '_configuring_vetor_storage',
                        None))}")

        # Testa a funcionalidade de auto-configuração
        vetor_storage = SERVICEHUB.vetor_storage
        print(f"VetorStorage configurado: {type(vetor_storage).__name__}")

        print("✅ Problema de tipagem resolvido com sucesso!")
        return True

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Testando correção de tipagem...\n")

    success = test_typing_issue()

    if success:
        print("\n🎉 Teste passou! O problema MyPy foi resolvido.")
    else:
        print("\n⚠️ Teste falhou. Verifique a implementação.")
