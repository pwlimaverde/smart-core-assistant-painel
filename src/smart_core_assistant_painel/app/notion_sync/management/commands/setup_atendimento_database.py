"""
Management command para configurar a database de Atendimentos do Notion.
"""

from typing import Any
import uuid

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from loguru import logger

from smart_core_assistant_painel.app.notion_sync.models import NotionDatabaseConfig
from smart_core_assistant_painel.app.notion_sync.services.mappers import AtendimentoMapper


class Command(BaseCommand):
    """
    Command para setup da database de Atendimentos no Notion.
    """

    help = "Configura a database de Atendimentos do Notion para sincronização"

    def handle(self, *args: Any, **options: Any) -> None:
        """Executa o comando de setup."""
        self.stdout.write(
            self.style.SUCCESS("Iniciando setup da database de Atendimentos...")
        )

        try:
            self._setup_atendimento_database()
            self._setup_mensagem_config()
            self.stdout.write(
                self.style.SUCCESS("Setup concluído com sucesso!")
            )
            self.stdout.write(
                self.style.WARNING("Lembre-se de preencher os IDs das databases no admin do Django.")
            )

        except Exception as exc:
            logger.error(f"Erro no setup da database de Atendimentos: {exc}")
            raise CommandError(f"Erro ao configurar database: {exc}")

    def _setup_atendimento_database(self) -> None:
        """Configura a database de Atendimentos."""
        self.stdout.write("Configurando database de Atendimentos...")

        schema = AtendimentoMapper.get_notion_schema()

        defaults = {
            "name": "Atendimentos - Smart Core Assistant",
            "description": "Database para sincronização de atendimentos",
            "django_model": "atendimentos.Atendimento",
            "django_app_label": "ui",
            "notion_schema": schema,
            "notion_database_id": uuid.uuid4(),  # ID Temporário
            "sync_enabled": True,
            "sync_direction": "bidirectional",
            "sync_priority": 10, # Prioridade alta
            "auto_sync": True,
        }

        config, created = NotionDatabaseConfig.objects.update_or_create(
            slug="ui_atendimentos_atendimento", defaults=defaults
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f"✓ Configuração de Atendimento criada: {config.name}")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"⚠ Configuração de Atendimento já existe: {config.name}")
            )

    def _setup_mensagem_config(self) -> None:
        """Configura a entidade Mensagem (sem database)."""
        self.stdout.write("Configurando entidade de Mensagens...")

        defaults = {
            "name": "Mensagens - Smart Core Assistant",
            "description": "Configuração para sincronização de mensagens como blocos",
            "django_model": "atendimentos.Mensagem",
            "django_app_label": "ui",
            "notion_schema": {},
            "notion_database_id": uuid.uuid4(), # Não aplicável, mas obrigatório
            "sync_enabled": True,
            "sync_direction": "django_to_notion", # Apenas envia
            "sync_priority": 7,
            "auto_sync": True,
        }

        config, created = NotionDatabaseConfig.objects.update_or_create(
            slug="ui_atendimentos_mensagem", defaults=defaults
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f"✓ Configuração de Mensagem criada: {config.name}")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"⚠ Configuração de Mensagem já existe: {config.name}")
            )
