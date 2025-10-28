"""
Management command para configurar databases do Notion.

Este comando cria ou atualiza as configurações das databases do Notion
para os models que serão sincronizados, incluindo Departamento e Atendente.
"""

from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from loguru import logger

from ...models import NotionDatabaseConfig
from ...services.mappers import DepartamentoMapper, AtendenteMapper


class Command(BaseCommand):
    """
    Command para setup das databases do Notion.

    Cria configurações padrão para as databases que serão sincronizadas,
    incluindo schemas e propriedades necessárias.
    """

    help = "Configura databases do Notion para sincronização"

    def add_arguments(self, parser: Any) -> None:
        """Adiciona argumentos ao comando."""
        parser.add_argument(
            "--update",
            action="store_true",
            help="Atualiza configurações existentes",
        )
        parser.add_argument(
            "--database-id",
            type=str,
            help="ID da database específica para configurar",
        )
        parser.add_argument(
            "--data-source-id",
            type=str,
            help="ID do data source da API v2025-09-03",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Executa o comando de setup."""
        self.stdout.write(
            self.style.SUCCESS("Iniciando setup das databases do Notion...")
        )

        # Configuração padrão (pode ser sobrescrita pelos argumentos)
        database_id = options.get("database_id", "")
        data_source_id = options.get("data_source_id", "")
        update = options.get("update", False)

        try:
            # Configuração para Departamento
            self._setup_departamento_database(
                database_id, data_source_id, update
            )

            # Configuração para Atendente
            self._setup_atendente_database(
                database_id, data_source_id, update
            )

            self.stdout.write(
                self.style.SUCCESS(
                    "Setup das databases concluído com sucesso!"
                )
            )

        except Exception as exc:
            logger.error(f"Erro no setup das databases: {exc}")
            raise CommandError(f"Erro ao configurar databases: {exc}")

    def _setup_departamento_database(
        self, database_id: str, data_source_id: str, update: bool
    ) -> None:
        """
        Configura a database de Departamentos.

        Args:
            database_id: ID da database no Notion.
            data_source_id: ID do data source.
            update: Se deve atualizar configurações existentes.
        """
        self.stdout.write("Configurando database de Departamentos...")

        # Obtém schema do mapper
        schema = DepartamentoMapper.get_notion_schema()

        defaults = {
            "name": "Departamentos - Smart Core Assistant",
            "description": "Database para sincronização de departamentos da organização",
            "django_model": "operacional.Departamento",
            "django_app_label": "ui",
            "notion_schema": schema,
            "sync_enabled": False,  # Inicia desabilitado até configuração completa
            "sync_direction": "bidirectional",
            "sync_priority": 5,
            "auto_sync": True,
            "metadata": {
                "version": "1.0",
                "setup_date": timezone.now().isoformat(),
                "fields_count": len(schema),
            },
        }

        if database_id:
            defaults["notion_database_id"] = database_id
        else:
            # UUID temporário para permitir criação durante setup
            import uuid

            defaults["notion_database_id"] = uuid.uuid4()

        if data_source_id:
            defaults["data_source_id"] = data_source_id

        config, created = NotionDatabaseConfig.objects.update_or_create(
            slug="ui_operacional_departamento", defaults=defaults
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f"✓ Configuração criada: {config.name}")
            )
        elif update:
            self.stdout.write(
                self.style.SUCCESS(f"✓ Configuração atualizada: {config.name}")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"⚠ Configuração já existe: {config.name}")
            )

    def _setup_atendente_humano_database(
        self, database_id: str, data_source_id: str, update: bool
    ) -> None:
        """
        Configura a database de Atendentes Humanos.

        Args:
            database_id: ID da database no Notion.
            data_source_id: ID do data source.
            update: Se deve atualizar configurações existentes.
        """
        self.stdout.write("Configurando database de Atendentes Humanos...")

        # Obtém schema do mapper
        schema = AtendenteMapper.get_notion_schema()

        defaults = {
            "name": "Atendentes - Smart Core Assistant",
            "description": "Database para sincronização de atendentes da organização",
            "django_model": "operacional.Atendente",
            "django_app_label": "ui",
            "notion_schema": schema,
            "sync_enabled": False,  # Inicia desabilitado até configuração completa
            "sync_direction": "bidirectional",
            "sync_priority": 5,
            "auto_sync": True,
            "metadata": {
                "version": "1.0",
                "setup_date": timezone.now().isoformat(),
                "fields_count": len(schema),
            },
        }

        if database_id:
            defaults["notion_database_id"] = database_id
        else:
            # UUID temporário para permitir criação durante setup
            import uuid

            defaults["notion_database_id"] = uuid.uuid4()

        if data_source_id:
            defaults["data_source_id"] = data_source_id

        config, created = NotionDatabaseConfig.objects.update_or_create(
            slug="ui_operacional_atendente", defaults=defaults
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f"✓ Configuração criada: {config.name}")
            )
        elif update:
            self.stdout.write(
                self.style.SUCCESS(f"✓ Configuração atualizada: {config.name}")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"⚠ Configuração já existe: {config.name}")
            )

    def _print_database_info(self, config: NotionDatabaseConfig) -> None:
        """
        Imprime informações detalhadas sobre a configuração da database.

        Args:
            config: Configuração da database.
        """
        self.stdout.write(f"\n{'=' * 60}")
        self.stdout.write(f"Database: {config.name}")
        self.stdout.write(f"Slug: {config.slug}")
        self.stdout.write(f"Modelo: {config.django_model}")
        self.stdout.write(f"App: {config.django_app_label}")
        self.stdout.write(
            f"Sincronização: {'Habilitada' if config.sync_enabled else 'Desabilitada'}"
        )
        self.stdout.write(f"Prioridade: {config.sync_priority}")
        self.stdout.write(f"Campos: {len(config.notion_schema)}")
        self.stdout.write(f"{'=' * 60}\n")
