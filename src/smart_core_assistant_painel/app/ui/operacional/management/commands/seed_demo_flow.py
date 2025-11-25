"""Comando de seed de dados demo para Fluxo de Atendimento.

Cria um `Departamento` de demonstração e um `FluxoAtendimento` com
etapas padrão (Fila, Trabalho, Espera, Finalização). Este comando é
idempotente e pode ser executado várias vezes sem duplicar registros.

Comentários em Português seguem as diretrizes do projeto.
"""

from typing import Any

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from smart_core_assistant_painel.app.ui.operacional.models import (
    Departamento,
    EtapaFluxo,
    FluxoAtendimento,
    TipoEtapa,
)


class Command(BaseCommand):
    help: str = (
        "Cria dados de demonstração: Departamento, Fluxo e Etapas padrão."
    )

    def add_arguments(self, parser: Any) -> None:  # type: ignore[override]
        parser.add_argument(
            "--department",
            dest="department",
            default="Comercial Demo",
            help=(
                "Nome do departamento a ser criado/atualizado "
                "(padrão: 'Comercial Demo')."
            ),
        )

    def handle(self, *args: Any, **options: Any) -> None:  # type: ignore[override]
        dept_name: str = options.get("department") or "Comercial Demo"

        # Criar/obter departamento de demonstração
        dept_slug: str = slugify(dept_name)
        departamento, _ = Departamento.objects.get_or_create(
            slug=dept_slug,
            defaults={
                "nome": dept_name,
                "descricao": "Departamento de demonstração para o Kanban.",
                "ativo": True,
            },
        )
        # Garantir nome atualizado se registro existir com mesmo slug
        if departamento.nome != dept_name:
            departamento.nome = dept_name
            departamento.save(update_fields=["nome"])

        # Criar/obter fluxo do departamento
        fluxo, _ = FluxoAtendimento.objects.get_or_create(
            departamento=departamento,
            defaults={
                "nome": f"Fluxo {dept_name}",
                "descricao": "Fluxo padrão com quatro etapas.",
                "ativo": True,
            },
        )

        # Comentário: Etapas padrão para um fluxo simples de atendimento.
        etapas_def = [
            {
                "nome": "Fila de Entrada",
                "ordem": 1,
                "tipo_etapa": TipoEtapa.FILA,
                "cor": "#3B82F6",
                "permite_atribuicao": False,
            },
            {
                "nome": "Em Trabalho",
                "ordem": 2,
                "tipo_etapa": TipoEtapa.TRABALHO,
                "cor": "#F59E0B",
                "permite_atribuicao": True,
            },
            {
                "nome": "Aguardando Resposta",
                "ordem": 3,
                "tipo_etapa": TipoEtapa.ESPERA,
                "cor": "#0EA5E9",
                "permite_atribuicao": True,
            },
            {
                "nome": "Finalizados",
                "ordem": 4,
                "tipo_etapa": TipoEtapa.FINALIZACAO,
                "cor": "#10B981",
                "permite_atribuicao": False,
            },
        ]

        for ed in etapas_def:
            etapa, created = EtapaFluxo.objects.get_or_create(
                fluxo=fluxo,
                ordem=ed["ordem"],
                defaults={
                    "nome": ed["nome"],
                    "descricao": "Etapa de demonstração.",
                    "tipo_etapa": ed["tipo_etapa"],
                    "cor": ed["cor"],
                    "permite_atribuicao": ed["permite_atribuicao"],
                    "automatico": False,
                    "ativo": True,
                },
            )
            # Atualiza campos caso já exista com mesma ordem
            if not created:
                updated_fields = []
                if etapa.nome != ed["nome"]:
                    etapa.nome = ed["nome"]
                    updated_fields.append("nome")
                if etapa.tipo_etapa != ed["tipo_etapa"]:
                    etapa.tipo_etapa = ed["tipo_etapa"]
                    updated_fields.append("tipo_etapa")
                if etapa.cor != ed["cor"]:
                    etapa.cor = ed["cor"]
                    updated_fields.append("cor")
                if etapa.permite_atribuicao != ed["permite_atribuicao"]:
                    etapa.permite_atribuicao = ed["permite_atribuicao"]
                    updated_fields.append("permite_atribuicao")
                if updated_fields:
                    etapa.save(update_fields=updated_fields)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed concluído. Departamento '{departamento.nome}' e "
                f"fluxo '{fluxo.nome}' estão prontos."
            )
        )
