"""Signals para o aplicativo Oráculo.

Este módulo define os signals e receivers para lidar com eventos assíncronos,
como o treinamento da IA após salvar um treinamento e o agendamento do
processamento de mensagens em buffer.
"""

from datetime import timedelta
from langchain_core.documents.base import Document

from smart_core_assistant_painel.app.ui.oraculo.models_treinamento import Treinamento
from typing import Any, cast

from django.db.models.signals import post_save, pre_delete
from django.dispatch import Signal, receiver
from django.utils import timezone
from django_q.models import Schedule
from django_q.tasks import async_task
from loguru import logger

from smart_core_assistant_painel.app.ui.oraculo.models_documento import Documento
from smart_core_assistant_painel.modules.services import SERVICEHUB

mensagem_bufferizada = Signal()

@receiver(post_save, sender=Treinamento)
def signals_gerar_documentos_treinamento(
    sender: Any, instance: Treinamento, created: bool, **kwargs: Any
) -> None:
    """Executa o treinamento da IA de forma assíncrona após salvar um treinamento.

    Args:
        sender (Any): O remetente do signal.
        instance (Treinamento): A instância do modelo de treinamento.
        created (bool): True se um novo registro foi criado.
        **kwargs (Any): Argumentos de palavra-chave adicionais.
    """
    try:
        # Só executa se o treinamento foi finalizado E ainda não foi vetorizado
        # Isso evita loops infinitos quando a vetorização atualiza o status
        if instance.treinamento_finalizado and not instance.treinamento_vetorizado:
            async_task(__gerar_documentos, instance.id)
    except Exception as e:
        logger.error(f"Erro ao processar signal de treinamento: {e}")

@receiver(post_save, sender=Documento)
def signals_embeddings_documento(
    sender: Any, instance: Documento, created: bool, **kwargs: Any
) -> None:
    """Gera embedding para o documento após criação ou atualização.
    
    Args:
        sender: O remetente do signal
        instance: Instância do Documento
        created: True se foi criado, False se foi atualizado
        **kwargs: Argumentos adicionais
    """
    try:
        # Só gera embedding se não existe ou se o conteúdo foi alterado
        if not instance.embedding or not instance.conteudo:
            if instance.conteudo and instance.conteudo.strip():
                async_task(__gerar_embedding_documento, instance.pk)
            else:
                logger.warning(f"Documento {instance.pk} sem conteúdo para embedding")
    except Exception as e:
        logger.error(f"Erro no signal de embedding do documento {instance.pk}: {e}")


@receiver(mensagem_bufferizada)
def signal_agendar_processamento_mensagens(
    sender: Any, phone: str, **kwargs: Any
) -> None:
    """Agenda o processamento de mensagens em buffer.

    Args:
        sender (Any): O remetente do signal.
        phone (str): O número de telefone para o qual agendar o processamento.
        **kwargs (Any): Argumentos de palavra-chave adicionais.
    """
    try:
        schedule_name = f"process_msg_{phone}"
        next_run = timezone.now() + timedelta(seconds=SERVICEHUB.TIME_CACHE)
        __limpar_schedules_telefone(phone)
        Schedule.objects.create(
            name=schedule_name,
            func="smart_core_assistant_painel.app.ui.oraculo.utils.send_message_response",
            args=phone,
            schedule_type=Schedule.ONCE,
            next_run=next_run,
        )
    except Exception as e:
        logger.error(
            f"Erro ao agendar processamento para {phone}: {e}", exc_info=True
        )


def __limpar_schedules_telefone(phone: str) -> None:
    """Remove agendamentos pendentes para um telefone específico.

    Args:
        phone (str): O número de telefone.
    """
    try:
        schedule_name = f"process_msg_{phone}"
        Schedule.objects.filter(
            name=schedule_name, next_run__gt=timezone.now()
        ).delete()
    except Exception as e:
        logger.warning(f"Erro ao limpar schedules para {phone}: {e}")


def __processar_conteudo_para_chunks(treinamento: Treinamento) -> list[Document]:
    """Processa conteúdo e cria chunks."""
    from smart_core_assistant_painel.modules.ai_engine.features.features_compose import FeaturesCompose
    
    # Prepara metadados
    metadata = {
        "source": "treinamento_manual", 
        "treinamento_id": str(treinamento.pk),
        "tag": treinamento.tag,
        "grupo": treinamento.grupo
    }
    
    # Garante que o conteúdo não é None
    conteudo = cast(str, treinamento.conteudo)

    # Usa a nova feature para gerar chunks
    chunks = FeaturesCompose.generate_chunks(
        conteudo=conteudo,
        metadata=metadata
    )
    
    return chunks

def __gerar_embedding_documento(documento_id: int) -> None:
    """Gera embedding para um documento específico.
    
    Args:
        documento_id: ID do documento para gerar embedding
    """
    try:
        from smart_core_assistant_painel.modules.ai_engine.features.features_compose import FeaturesCompose
        
        
        documento: Documento = Documento.objects.get(id=documento_id)
        
        if not documento.conteudo or not documento.conteudo.strip():
            logger.warning(f"Documento {documento_id} sem conteúdo válido")
            return
            
        embedding_vector: list[float] = FeaturesCompose.generate_embeddings(text=documento.conteudo)
        
        if embedding_vector:
            # Salva o embedding no documento
            Documento.objects.filter(id=documento_id).update(embedding=embedding_vector)
            logger.info(f"Embedding gerado e salvo para documento {documento_id}")
        else:
            logger.error(f"Falha ao gerar embedding para documento {documento_id}")
            
    except Documento.DoesNotExist:
        logger.error(f"Documento {documento_id} não encontrado")
    except Exception as e:
        logger.error(f"Erro ao gerar embedding para documento {documento_id}: {e}")


def __gerar_documentos(instance_id: int) -> None:

    try:
        instance: Treinamento = Treinamento.objects.get(id=instance_id)

        if not instance.conteudo or not instance.conteudo.strip():
            logger.warning(
                "Treinamento %s sem conteúdo para embedding.", instance_id
            )
            return
            
        if instance.treinamento_vetorizado:
            logger.info(f"Treinamento {instance_id} já está vetorizado, pulando...")
            return
        chunks: list[Document] = __processar_conteudo_para_chunks(treinamento=instance)
        from .models_documento import Documento

        Documento.criar_documentos_de_chunks(chunks=chunks, treinamento_id=instance_id)
        instance.treinamento_vetorizado = True
        instance.save()
        logger.info("Documentos gerados: %s", instance_id)

    except Treinamento.DoesNotExist:
        logger.error(f"Treinamento com ID {instance_id} não encontrado.")
    except Exception as e:
        logger.error(f"Erro ao executar treinamento {instance_id}: {e}")


@receiver(pre_delete, sender=Treinamento)
def signal_remover_treinamento_ia(
    sender: Any, instance: Treinamento, **kwargs: Any
) -> None:
    """Remove os dados de treinamento do banco vetorial antes de deletar.

    Args:
        sender (Any): O remetente do signal.
        instance (Treinamento): A instância do modelo de treinamento.
        **kwargs (Any): Argumentos de palavra-chave adicionais.

    Raises:
        Exception: Se a remoção do banco vetorial falhar.
    """
    try:
        if instance.treinamento_finalizado:
            __task_remover_treinamento_ia(instance.id)
    except Exception as e:
        logger.error(f"Erro ao processar remoção de treinamento: {e}")
        raise Exception(f"Falha ao remover treinamento {instance.id}: {e}")


def __task_remover_treinamento_ia(instance_id: int) -> None:
    """Tarefa para remover um treinamento do banco vetorial.

    Args:
        instance_id (int): O ID da instância de Treinamento.

    Raises:
        Exception: Se ocorrer um erro durante a remoção.
    """
    try:
        # Na nova arquitetura, não há campo embedding no Treinamento.
        # Os embeddings ficam nos documentos relacionados que são removidos
        # automaticamente devido ao CASCADE no ForeignKey.
        # Apenas marca como não vetorizado
        Treinamento.objects.filter(id=instance_id).update(treinamento_vetorizado=False)
        logger.info(
            "Treinamento marcado como não vetorizado: %s (pre_delete)", instance_id
        )
    except Exception as e:
        logger.error(f"Erro ao remover treinamento {instance_id}: {e}")
        raise