import logging
import socket
from io import StringIO
from pathlib import Path
from typing import Tuple

import psycopg2
import requests
from django.core.management import call_command
from django.db import connections

from ..models import TenantDatabase, TenantEvolution, TenantTrello

logger = logging.getLogger(__name__)


class ConnectionTester:
    """Service to test connections for Tenant integrations."""

    @staticmethod
    def test_evolution_connection(config: TenantEvolution) -> bool:
        """Tests connection to Evolution API."""
        if not config.server_url or not config.api_key:
            logger.warning(
                f"Evolution API check skipped for {config.tenant.slug}: "
                f"missing server_url or api_key"
            )
            return False

        try:
            # Evolution Go expõe a listagem em /instance/all
            # (o endpoint v2 /instance/fetchInstances retorna 404 no Go).
            url = f"{config.server_url.rstrip('/')}/instance/all"
            headers = {"apikey": config.api_key}

            logger.debug(
                f"Testing Evolution API connection for {config.tenant.slug}: "
                f"URL={url}"
            )

            response = requests.get(url, headers=headers, timeout=10)

            logger.debug(
                f"Evolution API response for {config.tenant.slug}: "
                f"status={response.status_code}"
            )

            if response.status_code == 200:
                return True

            # Log detalhado para debug
            logger.warning(
                f"Evolution API check failed for {config.tenant.slug}: "
                f"status={response.status_code}, "
                f"url={url}, "
                f"response={response.text[:200] if response.text else 'empty'}"
            )
            return False

        except requests.exceptions.ConnectionError as e:
            logger.error(
                f"Evolution API connection error for {config.tenant.slug}: "
                f"Cannot connect to {config.server_url}. Error: {str(e)}"
            )
            return False
        except requests.exceptions.Timeout as e:
            logger.error(
                f"Evolution API timeout for {config.tenant.slug}: "
                f"Request to {config.server_url} timed out. Error: {str(e)}"
            )
            return False
        except Exception as e:
            logger.error(
                f"Evolution API check error for {config.tenant.slug}: {str(e)}"
            )
            return False

    @staticmethod
    def test_trello_connection(config: TenantTrello) -> bool:
        """Tests connection to Trello API."""
        if not config.api_key or not config.token:
            return False

        try:
            url = "https://api.trello.com/1/members/me"
            params = {"key": config.api_key, "token": config.token}

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                return True

            logger.warning(
                f"Trello API check failed for "
                f"{config.tenant.slug}: {response.status_code}"
            )
            return False

        except Exception as e:
            logger.error(
                f"Trello API check error for {config.tenant.slug}: {str(e)}"
            )
            return False

    @staticmethod
    def test_postgres_connection(config: TenantDatabase) -> bool:
        """Tests connection to Tenant Database."""
        if not config.host or not config.database_name:
            return False

        try:
            conn = psycopg2.connect(
                host=config.host,
                port=config.port,
                dbname=config.database_name,
                user=config.username,
                password=config.password,
                connect_timeout=5,
            )
            conn.close()
            return True
        except Exception as e:
            logger.error(
                f"Postgres check error for {config.tenant.slug}: {str(e)}"
            )
            return False

    @staticmethod
    def test_tcp_connectivity(host: str, port: int, timeout: int = 5) -> bool:
        """Tests TCP connectivity to a host:port."""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (socket.error, socket.timeout):
            return False


class TenantMigrationRunner:
    """Service to run Django migrations on tenant databases."""

    @staticmethod
    def configure_tenant_database(config: TenantDatabase) -> str:
        """
        Configura conexão dinâmica para o banco do tenant.

        Returns:
            Nome do alias configurado no Django connections
        """
        alias = f"tenant_{config.tenant.slug}"

        # SSL mode mapping
        ssl_options = {}
        if config.ssl_mode and config.ssl_mode != "disable":
            ssl_options["sslmode"] = config.ssl_mode

        # Configura a conexão no Django com TODAS as opções necessárias
        connections.databases[alias] = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config.database_name,
            "USER": config.username,
            "PASSWORD": config.password,
            "HOST": config.host,
            "PORT": config.port,
            # Opções obrigatórias do Django
            "ATOMIC_REQUESTS": False,
            "AUTOCOMMIT": True,
            "CONN_MAX_AGE": 0,
            "CONN_HEALTH_CHECKS": False,
            "TIME_ZONE": None,
            "OPTIONS": {
                "connect_timeout": 10,
                **ssl_options,
            },
            "TEST": {
                "CHARSET": None,
                "COLLATION": None,
                "MIGRATE": True,
                "MIRROR": None,
                "NAME": None,
            },
        }

        return alias

    @classmethod
    def run_migrations(cls, config: TenantDatabase) -> Tuple[bool, str]:
        """
        Executa migrações Django no banco do tenant.

        Returns:
            Tuple (sucesso, mensagem)
        """
        # 1. Testar conectividade TCP primeiro
        if not ConnectionTester.test_tcp_connectivity(
            config.host, config.port
        ):
            return (
                False,
                f"Servidor {config.host}:{config.port} não está acessível",
            )

        # 2. Testar conexão com credenciais
        if not ConnectionTester.test_postgres_connection(config):
            return (False, "Falha na autenticação com o banco de dados")

        try:
            # 3. Configurar conexão dinâmica
            alias = cls.configure_tenant_database(config)

            # 4. Rodar migrations
            output = StringIO()
            call_command(
                "migrate",
                database=alias,
                verbosity=1,
                stdout=output,
            )

            # 5. Atualizar status
            config.connection_valid = True
            config.save()

            result_output = output.getvalue()
            logger.info(
                f"Migrations executadas para {config.tenant.slug}: "
                f"{result_output[:200]}"
            )

            return (True, "Migrações aplicadas com sucesso")

        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Erro ao executar migrations para "
                f"{config.tenant.slug}: {error_msg}"
            )

            # Ajuda de diagnóstico: esse erro costuma acontecer quando alguma migration
            # tenta criar FK para `auth_user` dentro do banco do tenant (que não
            # possui o app `auth` migrado). Ex.: operacional.Atendente.usuario.
            if "auth_user" in error_msg and "does not exist" in error_msg:
                try:
                    op_migration = (
                        Path(__file__).resolve().parents[2]
                        / "operacional"
                        / "migrations"
                        / "0001_initial.py"
                    )
                    op_has_fix = (
                        op_migration.exists()
                        and "db_constraint=False"
                        in op_migration.read_text(encoding="utf-8")
                    )
                    fix_hint = (
                        "Correção detectada no código atual (db_constraint=False). "
                        if op_has_fix
                        else "Correção NÃO detectada no código atual (db_constraint=False ausente). "
                    )
                except Exception:
                    fix_hint = ""

                return (
                    False,
                    'Erro ao aplicar migrações: relation "auth_user" does not exist. '
                    "Isso indica que alguma migration está tentando criar FK para auth_user no banco do tenant. "
                    f"{fix_hint}Reinicie o servidor/app após atualizar o código e execute novamente.",
                )
            return (False, f"Erro ao aplicar migrações: {error_msg}")
