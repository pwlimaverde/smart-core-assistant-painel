from django.apps import AppConfig


class AtendimentoUnificadoConfig(AppConfig):
    """Configuração do app Workspace de Atendimento Unificado.

    O app entrega a tela única que combina chat estilo WhatsApp Web e
    pipeline Kanban sobre as estruturas existentes
    (`EtapaFluxo`/`Atendimento`/`Mensagem`). Toda a integração com os
    demais apps acontece via signals e Celery tasks, mantendo o princípio
    de independência total: nenhum app de produção em `app/` é editado.
    """

    name: str = "smart_core_assistant_painel.app.atendimento_unificado"
    label: str = "atendimento_unificado"
    verbose_name: str = "Atendimento Unificado (Workspace)"
    default_auto_field: str = "django.db.models.BigAutoField"

    def ready(self) -> None:
        # Comentário (PT-BR): Carrega sinais ao iniciar a app, espelhando
        # o padrão usado por `trello_sync`.
        try:
            from . import (
                signals,  # noqa: F401  # pyright: ignore[reportUnusedImport]
            )
        except Exception as exc:
            from loguru import logger

            logger.warning(
                "Falha ao carregar sinais do atendimento_unificado: {}", exc
            )
