"""Comando para executar migrations no banco de dados de um tenant específico."""

from typing import Any

from django.core.management import call_command
from django.core.management.base import (
    BaseCommand,
    CommandError,
    CommandParser,
)
from django.db import connections
from loguru import logger

from smart_core_assistant_painel.app.tenants.models import Tenant


class Command(BaseCommand):
    help = "Executa migrations no banco de dados de um tenant específico"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "tenant_slug", type=str, help="Slug do tenant alvo"
        )

    def handle(self, *args: Any, **options: Any) -> None:
        slug = options["tenant_slug"]

        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            raise CommandError(f"Tenant '{slug}' não encontrado")

        try:
            db_config = getattr(tenant, "database_config", None)
            if not db_config:
                raise CommandError(
                    f"Tenant '{slug}' não possui configuração de banco de dados"
                )

            if not db_config.connection_valid:
                self.stderr.write(
                    self.style.WARNING(
                        f"Conexão do tenant '{slug}' não validada previamente"
                    )
                )
        except Exception as e:
            raise CommandError(f"Erro ao acessar config do banco: {str(e)}")

        alias = f"tenant_{slug}"

        # Configurar conexão
        connections.databases[alias] = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": db_config.database_name,
            "USER": db_config.username,
            "PASSWORD": db_config.password,
            "HOST": db_config.host,
            "PORT": db_config.port,
            "OPTIONS": {"sslmode": db_config.ssl_mode},
        }

        self.stdout.write(
            f"Iniciando migrations para tenant: {slug} (DB: {db_config.database_name})"
        )
        logger.info(f"migrate_tenant: iniciando para {slug}")

        try:
            call_command(
                "migrate",
                database=alias,
                verbosity=options.get("verbosity", 1),
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Migrations aplicadas com sucesso para '{slug}'"
                )
            )
        except Exception as e:
            logger.error(f"Erro ao migrar tenant {slug}: {e}")
            raise CommandError(f"Falha na migração: {e}")
