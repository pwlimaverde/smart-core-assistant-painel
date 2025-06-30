from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django_q.tasks import async_task
from loguru import logger

from smart_core_assistant_painel.modules.services.features.service_hub import SERVICEHUB

from .models import Treinamentos


@receiver(post_save, sender=Treinamentos)
def signals_treinamento_ia(sender, instance, created, **kwargs):
    """
    Signal executado após salvar um treinamento.
    Executa o treinamento da IA de forma assíncrona se o treinamento foi finalizado.
    """
    try:
        if instance.treinamento_finalizado:
            logger.info(
                f"Iniciando treinamento assíncrono para instância {
                    instance.id}")
            async_task(__task_treinar_ia, instance.id)
    except Exception as e:
        logger.error(
            f"Erro ao processar signal de treinamento para instância {
                instance.id}: {e}")


def __task_treinar_ia(instance_id):
    """
    Task para treinar a IA com documentos de um treinamento específico.

    Args:
        instance_id: ID da instância de Treinamento
    """
    instance = Treinamentos.objects.get(id=instance_id)

    try:
        logger.info(
            f"Iniciando task de treinamento para instância {instance_id}")

        # Remove dados antigos do treinamento antes de adicionar novos
        logger.info(f"Removendo dados antigos do treinamento {instance_id}")
        SERVICEHUB.vetor_storage.remove_by_metadata(
            "id_treinamento", str(instance_id))

        # Processa documentos
        documentos = instance.get_documentos()
        if not documentos:
            logger.warning(
                f"Nenhum documento encontrado para o treinamento {instance_id}")
            return

        # Cria ou atualiza banco vetorial
        SERVICEHUB.vetor_storage.write(documentos)

        logger.info(f"Treinamento {instance_id} concluído com sucesso")

    except Exception as e:
        logger.error(f"Erro ao executar treinamento {instance_id}: {e}")
        instance.treinamento_finalizado = False


@receiver(pre_delete, sender=Treinamentos)
def signal_remover_treinamento_ia(sender, instance, **kwargs):
    """
    Signal executado antes de deletar um treinamento.
    Remove os dados do treinamento do banco vetorial FAISS.
    Se houver erro na remoção, interrompe a deleção do treinamento.
    """
    try:
        if instance.treinamento_finalizado:
            logger.info(
                f"Removendo treinamento {
                    instance.id} do banco vetorial antes da deleção")
            # Executa a remoção de forma síncrona para garantir que seja concluída
            # antes da deleção do objeto
            __task_remover_treinamento_ia(instance.id)
            logger.info(
                f"Treinamento {
                    instance.id} removido com sucesso do banco vetorial")
    except Exception as e:
        logger.error(
            f"Erro ao processar remoção de treinamento para instância {
                instance.id}: {e}")
        # Interrompe a deleção levantando uma exceção
        raise Exception(
            f"Falha ao remover treinamento {
                instance.id} do banco vetorial. Deleção interrompida: {e}")


def __task_remover_treinamento_ia(instance_id):
    """
    Task para remover um treinamento específico do banco vetorial FAISS.

    Args:
        instance_id: ID da instância de Treinamento

    Raises:
        Exception: Se houver erro na remoção do banco vetorial
    """
    try:
        logger.info(f"Removendo treinamento {instance_id} do banco vetorial")
        SERVICEHUB.vetor_storage.remove_by_metadata(
            "id_treinamento", str(instance_id))
        logger.info(
            f"Treinamento {instance_id} removido com sucesso do banco vetorial")

    except Exception as e:
        logger.error(
            f"Erro ao remover treinamento {instance_id} do banco vetorial: {e}")
        # Propaga a exceção para interromper o processo de deleção
        raise
