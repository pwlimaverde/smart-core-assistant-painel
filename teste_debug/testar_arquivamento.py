#!/usr/bin/env python3
"""Script de debug para testar a equivalência do status ARQUIVADO no Django."""

import os
import sys
from datetime import timedelta

# Adiciona o diretório src ao path do Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

# Configura o Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smart_core_assistant_painel.app.core.settings")
import django
django.setup()

from django.utils import timezone
from smart_core_assistant_painel.app.tenants.models import Tenant
from smart_core_assistant_painel.app.clientes.models import Contato
from smart_core_assistant_painel.app.atendimentos.models import (
    Atendimento,
    StatusAtendimento,
    buscar_atendimento_ativo_por_contato,
)
from smart_core_assistant_painel.app.gestao_kanban.selectors import (
    board_snapshot_by_fluxo,
)
from smart_core_assistant_painel.app.chat_evolution.selectors import (
    list_conversations,
)

def rodar_testes() -> None:
    print("=" * 60)
    print("  TESTANDO COMPORTAMENTO DO STATUS ARQUIVADO")
    print("=" * 60)

    # 1. Obter tenant ativo de teste
    tenant = Tenant.objects.filter(active=True).first()
    if not tenant:
        print("[ERRO] Nenhum tenant ativo cadastrado.")
        return
    print(f"Usando Tenant: {tenant.slug}")

    # 2. Criar ou obter contato de teste
    contato, _ = Contato.objects.get_or_create(
        telefone="5599999999999",
        defaults={"nome_contato": "Contato Teste Arquivado"}
    )
    print(f"Contato: {contato.nome_contato} ({contato.telefone})")

    # 3. Criar atendimento de teste
    atendimento = Atendimento.objects.create(
        contato=contato,
        status=StatusAtendimento.FILA,
        assunto="Teste de Arquivamento"
    )
    print(f"Atendimento criado ID={atendimento.id} com status FILA.")

    # Validar que ele é ativo
    ativo = buscar_atendimento_ativo_por_contato(contato.id)
    assert ativo is not None, "O atendimento recém-criado deveria estar ativo!"
    print("[OK] Atendimento está ativo corretamente.")

    # 4. Alterar status para ARQUIVADO
    atendimento.status = StatusAtendimento.ARQUIVADO
    atendimento.data_fim = timezone.now()
    atendimento.save()
    print(f"Atendimento ID={atendimento.id} atualizado para status ARQUIVADO.")

    # 5. Validar que NÃO está ativo
    ativo = buscar_atendimento_ativo_por_contato(contato.id)
    assert ativo is None, "Atendimento ARQUIVADO não deveria ser considerado ativo!"
    print("[OK] Atendimento arquivado não é considerado ativo.")

    # 6. Validar que ele é excluído do snap do Kanban se tiver fluxo
    # (Criamos um fluxo fake se necessário, ou usamos um existente se houver)
    from smart_core_assistant_painel.app.operacional.models import FluxoAtendimento
    fluxo = FluxoAtendimento.objects.filter(ativo=True).first()
    if fluxo:
        atendimento.fluxo_atendimento = fluxo
        atendimento.save()
        snap = board_snapshot_by_fluxo(fluxo.id, is_owner=True)
        # Varre todos os cards em todas as etapas no payload retornado
        todos_cards = []
        for etapa_cards in snap.get("cards", {}).values():
            todos_cards.extend(etapa_cards)
        
        card_encontrado = any(c.get("atendimento_id") == atendimento.id for c in todos_cards)
        assert not card_encontrado, "Atendimento ARQUIVADO não deveria aparecer no Kanban!"
        print("[OK] Atendimento arquivado não aparece no Kanban.")
    else:
        print("[AVISO] Nenhum fluxo ativo para testar exclusão no Kanban.")

    # 7. Validar que ele é excluído do Modo Conversas (list_conversations)
    conversas = list_conversations(is_owner=True)
    conv_encontrada = any(c.get("atendimento_id") == atendimento.id for c in conversas)
    assert not conv_encontrada, "Atendimento ARQUIVADO não deveria aparecer na listagem de conversas do chat!"
    print("[OK] Atendimento arquivado não aparece na listagem do chat.")

    # 8. Validar a janela de feedback de 10 minutos
    recent_resolved = (
        Atendimento.objects.filter(
            contato_id=contato.id,
            status__in=[StatusAtendimento.RESOLVIDO, StatusAtendimento.ARQUIVADO],
            data_fim__gte=timezone.now() - timedelta(minutes=10),
        )
        .order_by("-data_fim")
        .first()
    )
    assert recent_resolved is not None, "Atendimento arquivado recentemente deveria ser localizado na janela de 10 min!"
    assert recent_resolved.id == atendimento.id
    print("[OK] Janela de 10 minutos localiza o atendimento arquivado corretamente.")

    # Limpeza do banco de dados local
    atendimento.delete()
    print("Atendimento de teste removido.")
    print("=" * 60)
    print("  TODOS OS TESTES LÓGICOS PASSARAM COM SUCESSO!")
    print("=" * 60)

if __name__ == "__main__":
    rodar_testes()
