"""Comando de seed para criar usuários do Django para atendentes humanos.

Este comando cria contas de usuário (django.contrib.auth.models.User) para
cada registro de AtendenteHumano que possua o campo ``usuario_sistema``
preenchido e ainda não tenha uma conta correspondente no sistema.

Uso:
    uv run python src/smart_core_assistant_painel/app/ui/manage.py seed_atendentes_users

Observações:
- Senha padrão: "123456" (apenas para ambiente de desenvolvimento)
- O comando só executa em ambiente com ``settings.DEBUG`` = True
"""

from __future__ import annotations

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from loguru import logger

from smart_core_assistant_painel.app.ui.operacional.models import (
    AtendenteHumano,
)


class Command(BaseCommand):
    """Comando Django para seed de usuários dos atendentes humanos."""

    help = (
        "Cria usuários do Django para registros de AtendenteHumano com "
        "usuario_sistema definido e sem conta correspondente."
    )

    def handle(self, *args, **options) -> None:
        """Ponto de entrada do comando.

        Args:
            *args (Any): Argumentos posicionais do comando.
            **options (Any): Opções nomeadas do comando.
        Returns:
            None
        """
        # Garantir execução apenas em ambiente de desenvolvimento
        if not getattr(settings, "DEBUG", False):
            self.stdout.write(
                self.style.ERROR(
                    "Este comando só deve ser executado em ambiente de desenvolvimento (DEBUG=True)."
                )
            )
            return

        default_password: str = "123456"
        created_count: int = 0
        skipped_count: int = 0

        # Buscar atendentes com usuario_sistema definido (não nulo e não vazio)
        atendentes = (
            AtendenteHumano.objects.filter(usuario_sistema__isnull=False)
            .exclude(usuario_sistema="")
            .all()
        )
        if not atendentes:
            self.stdout.write(
                self.style.WARNING(
                    "Nenhum AtendenteHumano com 'usuario_sistema' encontrado."
                )
            )
            return

        # Evitar uso de estilos não suportados (NOTICE)
        self.stdout.write(
            f"Processando {atendentes.count()} atendente(s) para criação de usuários..."
        )

        for agente in atendentes:
            username = (agente.usuario_sistema or "").strip()
            if not username:
                skipped_count += 1
                continue

            user_exists = User.objects.filter(username=username).exists()
            if user_exists:
                skipped_count += 1
                logger.info(
                    "Usuário já existe para atendente '{}': username='{}'",
                    getattr(agente, "nome", "(sem nome)"),
                    username,
                )
                continue

            # Criar usuário com senha padrão (apenas DEV)
            user = User.objects.create_user(
                username=username,
                password=default_password,
                email=getattr(agente, "email", "") or "",
            )
            # Tornar staff para acesso ao admin, se necessário
            user.is_staff = True
            user.save(update_fields=["is_staff"])

            created_count += 1
            logger.info(
                "Usuário criado para atendente '{}': username='{}' senha='{}'",
                getattr(agente, "nome", "(sem nome)"),
                username,
                default_password,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed concluído. Criados: {created_count}, Ignorados: {skipped_count}."
            )
        )
