#!/usr/bin/env python3
"""
Script de teste simples para validação da funcionalidade de transferência.
"""

import os
import sys
import django

# Configura o ambiente Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.ui.core.settings_test",
)
django.setup()


def main():
    print("🧪 TESTE SIMPLES DE TRANSFERÊNCIA")
    print("=" * 50)

    from smart_core_assistant_painel.app.ui.atendimentos.utils import (
        _processar_transferencia_atendimento,
    )
    from smart_core_assistant_painel.app.ui.operacional.models import (
        Departamento,
        FluxoAtendimento,
        EtapaFluxo,
    )
    from smart_core_assistant_painel.app.ui.atendimentos.models import (
        Atendimento,
    )
    from smart_core_assistant_painel.app.ui.clientes.models import (
        Contato,
    )

    # Limpar dados existentes
    print("🧹 Limpando dados existentes...")
    Departamento.objects.filter(nome="Comercial").delete()
    print("✓ Dados limpos")

    # Criar departamento
    depto = Departamento.objects.create(nome="Comercial", ativo=True)
    print(f"✓ Departamento criado: {depto.nome}")

    # Criar fluxo
    fluxo = FluxoAtendimento.objects.create(
        nome="fila atendimento", departamento=depto, ativo=True
    )
    print(f"✓ Fluxo criado: {fluxo.nome}")

    # Criar etapa
    etapa = EtapaFluxo.objects.create(
        fluxo=fluxo, nome="fila atendimento", cor="#6B7280", icone="📋"
    )
    print(f"✓ Etapa criada: {etapa.nome}")

    # Criar contato
    contato = Contato.objects.create(
        nome_contato="Cliente Teste",
        telefone="5511999999999",
        email="cliente@teste.com",
    )
    print(f"✓ Contato criado: {contato.nome_contato}")

    # Criar atendimento
    atendimento = Atendimento.objects.create(
        contato=contato,
        departamento=depto,
        etapa_atual=etapa,
        status="iniciado",
    )
    print(f"✓ Atendimento criado: {atendimento.id}")

    # Testar transferência
    fluxo_transferencia = "Atendimento Comercial - Comercial"
    print(f"🔄 Testando transferência: {fluxo_transferencia}")

    resultado = _processar_transferencia_atendimento(
        atendimento_obj=atendimento,
        fluxo_transferencia=fluxo_transferencia,
    )

    print(f"Resultado: {resultado}")

    # Recarregar e verificar
    atendimento.refresh_from_db()
    print(f"Status final: {atendimento.status}")
    print(f"Departamento final: {atendimento.departamento.nome}")
    print(f"Etapa final: {atendimento.etapa_atual.nome}")
    print(f"Fluxo transferência: {atendimento.fluxo_transferencia}")

    # Validações
    assert resultado == True, "A transferência deveria ter sido bem-sucedida"
    assert atendimento.status == "fila", "Status deveria ser 'fila'"
    assert atendimento.departamento.nome == "Comercial", (
        "Departamento incorreto"
    )
    assert atendimento.etapa_atual.nome == "fila atendimento", (
        "Etapa incorreta"
    )
    assert atendimento.fluxo_transferencia == fluxo_transferencia, (
        "Fluxo transferência incorreto"
    )

    print("\n✅ TESTE PASSOU!")
    print("✅ Funcionalidade implementada com sucesso!")

    # Limpar
    atendimento.delete()
    contato.delete()
    EtapaFluxo.objects.all().delete()
    FluxoAtendimento.objects.all().delete()
    Departamento.objects.all().delete()
    print("\n🧹 Dados limpos!")


if __name__ == "__main__":
    main()
