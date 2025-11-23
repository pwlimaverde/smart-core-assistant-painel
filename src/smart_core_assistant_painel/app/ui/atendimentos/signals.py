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
    Mensagem,
    TipoMensagem,
    TipoRemetente,
)


# Armazena o estado anterior do atendente_humano antes do save
_previous_atendente_humano: dict[int, Optional[int]] = {}

# Flag para evitar recursão quando criamos mensagem dentro do signal
_creating_greeting_message: set[int] = set()


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

    # Evita recursão se já estamos criando mensagem para este atendimento
    if instance.pk in _creating_greeting_message:
        return

    # Recupera o valor anterior
    previous_id = _previous_atendente_humano.pop(instance.pk, None)
    # Usa getattr para acessar o campo _id de forma type-safe
    current_id: Optional[int] = getattr(instance, "atendente_humano_id", None)

    # Verifica se houve mudança real no atendente_humano
    if previous_id == current_id:
        logger.debug(
            f"Signal: Atendimento {instance.id} - "
            f"Sem mudança no atendente_humano"
        )
        return

    # Verifica se o novo valor é um atendente (não None)
    if current_id is None:
        logger.debug(
            f"Signal: Atendimento {instance.id} - "
            f"Atendente removido (de {previous_id} para None)"
        )
        return

    # Detectou mudança para um atendente humano - criar mensagem de saudação
    if instance.atendente_humano is None:
        logger.warning(
            f"Signal: Atendimento {instance.id} tem current_id={current_id} "
            "mas atendente_humano é None"
        )
        return

    atendente_nome = instance.atendente_humano.nome
    logger.info(
        f"Signal: Detectada atribuição de atendente {atendente_nome} "
        f"(ID: {current_id}) ao atendimento {instance.id}. "
        f"Criando mensagem de saudação..."
    )

    try:
        # Marca que estamos criando mensagem para este atendimento
        _creating_greeting_message.add(instance.pk)

        # Prepara mensagem de saudação
        mensagem_saudacao = (
            f"Olá, meu nome é {atendente_nome}, irei continuar seu "
            "atendimento."
        )

        # Copia metadados da última mensagem (se existir)
        metadados: dict[str, Any] = {}
        ultima_mensagem = instance.mensagens.order_by("-timestamp").first()
        if ultima_mensagem and ultima_mensagem.metadados:
            # Copia os metadados para manter estrutura de evolution
            metadados = dict(ultima_mensagem.metadados)

        # Cria mensagem com saudação usando transaction.on_commit
        # para garantir que só execute após o commit do atendimento
        def create_greeting() -> None:
            try:
                mensagem = Mensagem.objects.create(
                    atendimento=instance,
                    tipo=TipoMensagem.TEXTO_FORMATADO,
                    conteudo="",  # Conteúdo vazio, pois é mensagem de saída
                    remetente=TipoRemetente.ATENDENTE_HUMANO,
                    resposta_bot=mensagem_saudacao,
                    metadados=metadados,
                    respondida=False,  # Será marcado True após envio
                )

                logger.info(
                    f"Signal: Mensagem de saudação criada (ID: {mensagem.id}) "
                    f"para atendimento {instance.id}"
                )
            except Exception as e:
                logger.error(
                    f"Erro ao criar mensagem de saudação no signal "
                    f"para atendimento {instance.id}: {e}"
                )
            finally:
                # Remove da lista de criação
                _creating_greeting_message.discard(instance.pk)

        # Agenda a criação da mensagem após o commit
        transaction.on_commit(create_greeting)

    except Exception as e:
        logger.error(
            f"Erro no signal ao processar atendimento {instance.id}: {e}"
        )
        _creating_greeting_message.discard(instance.pk)
