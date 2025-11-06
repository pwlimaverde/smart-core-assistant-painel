"""Seed mínimo para o departamento Comercial.

Cria de forma idempotente:
- Departamento "Comercial" com fluxo e quatro etapas (Fila, Trabalho, Espera, Finalização)
- Um atendente humano associado ao departamento
- Contatos de exemplo
- Atendimentos distribuídos nas etapas
- Mensagens associadas, atualizando `data_ultima_mensagem`

Comentários em Português e type hints completos conforme padrões do projeto.
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from smart_core_assistant_painel.app.ui.clientes.models import Contato
from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
    Mensagem,
    StatusAtendimento,
    TipoMensagem,
    TipoRemetente,
)
from smart_core_assistant_painel.app.ui.operacional.models import (
    Departamento,
    FluxoAtendimento,
    EtapaFluxo,
    MovimentoFluxo,
    TipoEtapa,
    Atendente,
)


class Command(BaseCommand):
    help: str = (
        "Popula dados mínimos do fluxo Comercial (departamento, etapas, "
        "atendente, contatos, atendimentos e mensagens)."
    )

    def add_arguments(self, parser: Any) -> None:
        # Argumento opcional para nome do departamento (padrão: Comercial)
        parser.add_argument(
            "--departamento",
            type=str,
            default="Comercial",
            help="Nome do departamento a ser criado/populado",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        nome_departamento: str = options["departamento"]

        # 1) Departamento Comercial
        dep_slug: str = slugify(nome_departamento)
        departamento, _ = Departamento.objects.get_or_create(
            nome=nome_departamento,
            defaults={
                "slug": dep_slug,
                "descricao": "Departamento Comercial para Kanban de testes",
                "ativo": True,
            },
        )

        # 2) Fluxo e Etapas
        fluxo, _ = FluxoAtendimento.objects.get_or_create(
            departamento=departamento,
            defaults={
                "nome": f"Fluxo {nome_departamento}",
                "descricao": "Fluxo padrão do departamento Comercial",
                "ativo": True,
            },
        )

        etapas_def: list[dict[str, Any]] = [
            {
                "nome": "Fila",
                "ordem": 1,
                "tipo_etapa": TipoEtapa.FILA,
                "cor": "#6B7280",
                "permite_atribuicao": False,
            },
            {
                "nome": "Trabalho",
                "ordem": 2,
                "tipo_etapa": TipoEtapa.TRABALHO,
                "cor": "#F59E0B",
                "permite_atribuicao": True,
            },
            {
                "nome": "Espera",
                "ordem": 3,
                "tipo_etapa": TipoEtapa.ESPERA,
                "cor": "#0EA5E9",
                "permite_atribuicao": True,
            },
            {
                "nome": "Finalização",
                "ordem": 4,
                "tipo_etapa": TipoEtapa.FINALIZACAO,
                "cor": "#10B981",
                "permite_atribuicao": False,
            },
        ]

        etapas_por_ordem: dict[int, EtapaFluxo] = {}
        for ed in etapas_def:
            etapa, created = EtapaFluxo.objects.get_or_create(
                fluxo=fluxo,
                ordem=ed["ordem"],
                defaults={
                    "nome": ed["nome"],
                    "descricao": "Etapa do fluxo Comercial",
                    "tipo_etapa": ed["tipo_etapa"],
                    "cor": ed["cor"],
                    "permite_atribuicao": ed["permite_atribuicao"],
                    "automatico": False,
                    "ativo": True,
                },
            )
            # Atualiza se já existir com mesma ordem
            if not created:
                atualizados: list[str] = []
                if etapa.nome != ed["nome"]:
                    etapa.nome = ed["nome"]
                    atualizados.append("nome")
                if etapa.tipo_etapa != ed["tipo_etapa"]:
                    etapa.tipo_etapa = ed["tipo_etapa"]
                    atualizados.append("tipo_etapa")
                if etapa.cor != ed["cor"]:
                    etapa.cor = ed["cor"]
                    atualizados.append("cor")
                if etapa.permite_atribuicao != ed["permite_atribuicao"]:
                    etapa.permite_atribuicao = ed["permite_atribuicao"]
                    atualizados.append("permite_atribuicao")
                if atualizados:
                    etapa.save(update_fields=atualizados)
            etapas_por_ordem[etapa.ordem] = etapa

        etapa_fila: EtapaFluxo = etapas_por_ordem[1]
        etapa_trabalho: EtapaFluxo = etapas_por_ordem[2]
        etapa_espera: EtapaFluxo = etapas_por_ordem[3]
        etapa_final: EtapaFluxo = etapas_por_ordem[4]

        # 3) Atendente humano do Comercial
        atendente, _ = Atendente.objects.get_or_create(
            nome="Agente Comercial",
            cargo="Vendas",
            departamento=departamento,
            defaults={
                "telefone": "5511990001111",
                "email": "comercial@example.com",
                "disponivel": True,
                "max_atendimentos_simultaneos": 3,
            },
        )

        # 4) Contatos (mínimo)
        contatos_data: list[dict[str, str]] = [
            {"telefone": "551100000001", "nome_contato": "Alice Teste"},
            {"telefone": "551100000002", "nome_contato": "Bruno Teste"},
            {"telefone": "551100000003", "nome_contato": "Carla Teste"},
            {"telefone": "551100000004", "nome_contato": "Diego Teste"},
            {"telefone": "551100000005", "nome_contato": "Eva Teste"},
        ]
        contatos: list[Contato] = []
        for cd in contatos_data:
            contato, _ = Contato.objects.get_or_create(
                telefone=cd["telefone"],
                defaults={
                    "nome_contato": cd["nome_contato"],
                    "ativo": True,
                },
            )
            contatos.append(contato)

        # 5) Atendimentos por etapa
        # - 2 na Fila, 1 em Trabalho, 1 em Espera, 1 Finalizado
        def criar_atendimento(
            contato: Contato,
            etapa: EtapaFluxo,
            assunto: str,
            status_legado: StatusAtendimento,
            atribuir_atendente: bool = False,
        ) -> Atendimento:
            """Cria atendimento idempotente e movimenta para a etapa desejada."""
            atendimento, _ = Atendimento.objects.get_or_create(
                contato=contato,
                departamento=departamento,
                defaults={
                    "assunto": assunto,
                    "prioridade": "normal",
                    "produto_servico": "Plano Gold",
                    "categoria_venda": "assinatura",
                    "valor_orcamento": 199.90,
                    "status": status_legado,
                },
            )

            # Ajusta atendente conforme etapa
            atendente_destino = atendente if atribuir_atendente else None

            # Registra movimento para etapa atual (idempotente simples: cria se ainda não estiver na mesma etapa)
            if atendimento.etapa_atual_id != etapa.id:
                MovimentoFluxo.criar_movimento(
                    atendimento=atendimento,
                    etapa_destino=etapa,
                    atendente_destino=atendente_destino,
                    motivo=f"Seed Comercial: movido para {etapa.nome}",
                    automatico=False,
                )

            return atendimento

        # Distribuição
        a1 = criar_atendimento(
            contatos[0],
            etapa_fila,
            "Solicitação de orçamento",
            StatusAtendimento.FILA,
        )
        a2 = criar_atendimento(
            contatos[1],
            etapa_fila,
            "Cotação de serviço",
            StatusAtendimento.FILA,
        )
        a3 = criar_atendimento(
            contatos[2],
            etapa_trabalho,
            "Negociação em andamento",
            StatusAtendimento.EM_ATENDIMENTO,
            True,
        )
        a4 = criar_atendimento(
            contatos[3],
            etapa_espera,
            "Aguardando retorno do cliente",
            StatusAtendimento.AGUARDANDO_RETORNO,
            True,
        )
        a5 = criar_atendimento(
            contatos[4],
            etapa_final,
            "Venda concluída",
            StatusAtendimento.RESOLVIDO,
            True,
        )

        atendimentos: list[Atendimento] = [a1, a2, a3, a4, a5]

        # 6) Mensagens para cada atendimento
        for idx, at in enumerate(atendimentos, start=1):
            # Mensagem do contato
            m1, _ = Mensagem.objects.get_or_create(
                atendimento=at,
                conteudo=f"Olá, tenho interesse no produto (caso {idx}).",
                tipo=TipoMensagem.TEXTO_FORMATADO,
                remetente=TipoRemetente.CONTATO,
            )
            # Resposta do atendente/bot
            m2, _ = Mensagem.objects.get_or_create(
                atendimento=at,
                conteudo="Obrigado pelo contato! Vou verificar e retorno.",
                tipo=TipoMensagem.TEXTO_FORMATADO,
                remetente=TipoRemetente.ATENDENTE_HUMANO,
                defaults={"metadados": {"atendente": atendente.nome}},
            )

            # Atualiza data_ultima_mensagem no atendimento
            ultimo_ts = m2.timestamp if m2.timestamp else timezone.now()
            if at.data_ultima_mensagem != ultimo_ts:
                at.data_ultima_mensagem = ultimo_ts
                at.save(update_fields=["data_ultima_mensagem"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed mínimo do departamento '{departamento.nome}' concluído com sucesso."
            )
        )
