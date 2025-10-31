"""
Management command para inicializar registros de sincronização existentes.

Este comando cria registros de sync para todos os models existentes
que ainda não possuem sincronização configurada.
"""

from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from loguru import logger


class Command(BaseCommand):
    """
    Command para inicializar registros de sincronização.

    Cria registros DepartamentoSync e AtendenteSync para
    todos os models existentes que ainda não possuem sync.
    """

    help = "Inicializa registros de sincronização para models existentes"

    def add_arguments(self, parser: Any) -> None:
        """Adiciona argumentos ao comando."""
        parser.add_argument(
            "--force",
            action="store_true",
            help="Força recriação de todos os registros (cuidado!)",
        )
        parser.add_argument(
            "--departamentos-only",
            action="store_true",
            help="Processa apenas departamentos",
        )
        parser.add_argument(
            "--atendentes-only",
            action="store_true",
            help="Processa apenas atendentes",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Executa o comando de inicialização."""
        self.stdout.write(
            self.style.SUCCESS(
                "Iniciando inicialização de registros de sync..."
            )
        )

        force = options.get("force", False)
        deptos_only = options.get("departamentos_only", False)
        atendentes_only = options.get("atendentes_only", False)

        try:
            with transaction.atomic():
                if not atendentes_only:
                    self._init_departamento_syncs(force)

                if not deptos_only:
                    self._init_atendente_syncs(force)

            self.stdout.write(
                self.style.SUCCESS(
                    "Inicialização de registros concluída com sucesso!"
                )
            )

        except Exception as exc:
            logger.error(f"Erro na inicialização de syncs: {exc}")
            raise CommandError(f"Erro ao inicializar registros: {exc}")

    def _init_departamento_syncs(self, force: bool) -> None:
        """
        Inicializa registros de sync para Departamentos.

        Args:
            force: Se deve forçar recriação de todos os registros.
        """
        self.stdout.write("Processando Departamentos...")

        # Obtém configuração do Notion
        try:
            config = NotionDatabaseConfig.objects.get(
                slug="ui_operacional_departamento"
            )
        except NotionDatabaseConfig.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(
                    "⚠ Configuração do Notion para Departamentos não encontrada"
                )
            )
            return

        # Contadores
        created_count = 0
        skipped_count = 0
        error_count = 0

        # Processa todos os departamentos
        for depto in Departamento.objects.all():
            try:
                # Verifica se já existe sync
                existing = DepartamentoSync.objects.filter(
                    departamento=depto
                ).first()

                if existing and not force:
                    skipped_count += 1
                    continue

                # Se force, remove existente
                if existing and force:
                    existing.delete()

                # Cria novo registro
                sync = DepartamentoSync.objects.create(
                    departamento=depto,
                    config=config,
                    external_id=None,
                    sync_status="pending",
                    nome_formatado=depto.nome.strip().title()
                    if depto.nome
                    else "",
                    slug_formatado=depto.slug or "",
                    descricao_formatada=depto.descricao.strip()
                    if depto.descricao
                    else "",
                    status_formatado="Ativo" if depto.ativo else "Inativo",
                    count_atendentes=depto.atendentes.filter(
                        ativo=True
                    ).count(),
                )

                # Prepara dados para Notion
                sync.prepare_notion_data()
                sync.save()

                created_count += 1
                self.stdout.write(
                    f"  ✓ Departamento sync criado: {depto.nome}"
                )

            except Exception as exc:
                error_count += 1
                logger.error(
                    f"Erro ao processar departamento {depto.id}: {exc}"
                )

        # Resumo
        self.stdout.write(f"\nResumo Departamentos:")
        self.stdout.write(f"  Criados: {created_count}")
        self.stdout.write(f"  Ignorados: {skipped_count}")
        self.stdout.write(f"  Erros: {error_count}\n")

    def _init_atendente_syncs(self, force: bool) -> None:
        """
        Inicializa registros de sync para Atendentes Humanos.

        Args:
            force: Se deve forçar recriação de todos os registros.
        """
        self.stdout.write("Processando Atendentes Humanos...")

        # Obtém configuração do Notion
        try:
            config = NotionDatabaseConfig.objects.get(
                slug="ui_operacional_atendente"
            )
        except NotionDatabaseConfig.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(
                    "⚠ Configuração do Notion para Atendentes não encontrada"
                )
            )
            return

        # Contadores
        created_count = 0
        skipped_count = 0
        error_count = 0

        # Processa todos os atendentes
        for atendente in Atendente.objects.all():
            try:
                # Verifica se já existe sync
                existing = AtendenteSync.objects.filter(
                    atendente=atendente
                ).first()

                if existing and not force:
                    skipped_count += 1
                    continue

                # Se force, remove existente
                if existing and force:
                    existing.delete()

                # Prepara dados
                nome_formatado = (
                    atendente.nome.strip().title() if atendente.nome else ""
                )
                cargo_formatado = (
                    atendente.cargo.strip().title() if atendente.cargo else ""
                )
                departamento_nome = (
                    atendente.departamento.nome
                    if atendente.departamento
                    else None
                )
                email_formatado = (
                    atendente.email.lower().strip()
                    if atendente.email
                    else None
                )

                # Busca sync do departamento se existir
                departamento_sync = None
                if atendente.departamento:
                    try:
                        departamento_sync = DepartamentoSync.objects.get(
                            departamento=atendente.departamento
                        )
                    except DepartamentoSync.DoesNotExist:
                        pass

                # Cria novo registro
                sync = AtendenteSync.objects.create(
                    atendente=atendente,
                    config=config,
                    external_id=None,
                    sync_status="pending",
                    departamento_sync=departamento_sync,
                    nome_formatado=nome_formatado,
                    cargo_formatado=cargo_formatado,
                    departamento_nome=departamento_nome,
                    email_formatado=email_formatado,
                    status_formatado="Ativo" if atendente.ativo else "Inativo",
                    disponibilidade_formatada="Disponível"
                    if atendente.disponivel
                    else "Indisponível",
                    carga_atual=atendente.get_atendimentos_ativos(),
                    capacidade_maxima=atendente.max_atendimentos_simultaneos,
                )

                # Prepara dados para Notion
                sync.prepare_notion_data()
                sync.save()

                created_count += 1
                self.stdout.write(
                    f"  ✓ Atendente sync criado: {atendente.nome}"
                )

            except Exception as exc:
                error_count += 1
                logger.error(
                    f"Erro ao processar atendente {atendente.id}: {exc}"
                )

        # Resumo
        self.stdout.write(f"\nResumo Atendentes:")
        self.stdout.write(f"  Criados: {created_count}")
        self.stdout.write(f"  Ignorados: {skipped_count}")
        self.stdout.write(f"  Erros: {error_count}\n")

    def _print_sync_summary(self) -> None:
        """
        Imprime resumo dos registros de sincronização.
        """
        self.stdout.write(f"\n{'=' * 60}")
        self.stdout.write("RESUMO DA SINCRONIZAÇÃO")
        self.stdout.write(f"{'=' * 60}")

        # Departamentos
        dept_total = Departamento.objects.count()
        dept_sync = DepartamentoSync.objects.count()
        dept_pending = DepartamentoSync.objects.filter(
            sync_status="pending"
        ).count()

        self.stdout.write(f"\nDEPARTAMENTOS:")
        self.stdout.write(f"  Total no Django: {dept_total}")
        self.stdout.write(f"  Com sync: {dept_sync}")
        self.stdout.write(f"  Pendentes: {dept_pending}")

        # Atendentes
        aten_total = Atendente.objects.count()
        aten_sync = AtendenteSync.objects.count()
        aten_pending = AtendenteSync.objects.filter(
            sync_status="pending"
        ).count()

        self.stdout.write(f"\nATENDENTES HUMANOS:")
        self.stdout.write(f"  Total no Django: {aten_total}")
        self.stdout.write(f"  Com sync: {aten_sync}")
        self.stdout.write(f"  Pendentes: {aten_pending}")

        self.stdout.write(f"\n{'=' * 60}\n")
