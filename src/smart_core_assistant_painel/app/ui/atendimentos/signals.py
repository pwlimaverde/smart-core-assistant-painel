"""
Signals para o app de atendimentos.

Este módulo contém signals Django que escutam eventos de models
e executam ações automáticas.
"""

from typing import Any, Optional

from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from loguru import logger

from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
)

# Armazena o estado anterior do atendente_humano antes do save
_previous_atendente_humano: dict[int, Optional[int]] = {}


@receiver(pre_save, sender=Atendimento)
def store_previous_atendente_humano(
    sender: Any, instance: Atendimento, **kwargs: Any
) -> None:
    """
    Armazena o valor anterior do atendente_humano antes do save.

    Este signal é executado antes do save() e captura o estado
    anterior do campo atendente_humano para comparação posterior.

    Args:
        sender: Classe do modelo que enviou o signal (Atendimento)
        instance: Instância do Atendimento que será salva
        **kwargs: Argumentos adicionais do signal
    """
    if instance.pk:  # Só verifica se não é criação
        try:
            # Busca o estado atual no banco
            old_instance = Atendimento.objects.only("atendente_humano").get(
                pk=instance.pk
            )
            # Usa getattr para acessar o campo _id de forma type-safe
            _previous_atendente_humano[instance.pk] = getattr(
                old_instance, "atendente_humano_id", None
            )
        except Atendimento.DoesNotExist:
            _previous_atendente_humano[instance.pk] = None


@receiver(post_save, sender=Atendimento)
def auto_create_greeting_on_agent_assignment(
    sender: Any, instance: Atendimento, created: bool, **kwargs: Any
) -> None:
    """
    Cria automaticamente mensagem de saudação ao atribuir atendente humano.

    Monitora alterações no campo `atendente_humano` do modelo Atendimento.
    Quando um atendente humano é atribuído (mudança detectada), cria
    automaticamente uma mensagem de saudação que será enviada via Evolution API.

    Este signal funciona tanto para atribuições via código quanto pelo admin.

    Args:
        sender: Classe do modelo que enviou o signal (Atendimento)
        instance: Instância do Atendimento que foi salva
        created: True se a instância foi criada, False se foi atualizada
        **kwargs: Argumentos adicionais do signal
    """
    # Ignora criação de novos atendimentos
    if created:
        _previous_atendente_humano.pop(instance.pk, None)
        return

    # Recupera o valor anterior
    previous_id = _previous_atendente_humano.pop(instance.pk, None)
    # Usa getattr para acessar o campo _id de forma type-safe
    current_id: Optional[int] = getattr(instance, "atendente_humano_id", None)

    # Verifica se houve mudança real no atendente_humano
    if previous_id == current_id:
        return

    # Verifica se o novo valor é um atendente (não None)
    if current_id is None:
        return

    # Detectou mudança para um atendente humano - criar mensagem de saudação
    if instance.atendente_humano is None:
        return

    # Chama o método do modelo que já possui a lógica correta de instância
    # Usamos transaction.on_commit para garantir que o save atual termine
    def trigger_greeting() -> None:
        try:
            # Recarrega a instância para garantir dados frescos
            atendimento = Atendimento.objects.get(pk=instance.pk)

            # Chama o método passando o ID do atendente
            atendimento.transferir_para_humano_com_saudacao(
                atendente_id=current_id,
                observacao="Saudação automática disparada por signal",
            )

        except Exception as e:
            logger.error(
                f"Erro ao executar trigger_greeting para atendimento "
                f"{instance.id}: {e}"
            )

    # Agenda a execução
    transaction.on_commit(trigger_greeting)
