from typing import Any, Optional, cast

from loguru import logger

from smart_core_assistant_painel.modules.services import (
    FeaturesCompose,
    SERVICEHUB,
)
from smart_core_assistant_painel.modules.services.features.unifield_data_services.domain.interface.unified_data_service import (
    UnifiedDataService,
)
from smart_core_assistant_painel.app.trello_sync.models import (
    TrelloCard,
    TrelloList,
)

from decimal import Decimal
from django.utils import timezone

from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
)
from smart_core_assistant_painel.app.trello_sync.services.member_sync_service import (
    MemberSyncService,
)


class TicketSyncService:
    """
    Serviço de sincronização de tickets (Atendimento → Card).
    """

    def __init__(self) -> None:
        # Comentário (PT-BR): Obtém o UDS do SERVICEHUB. Se necessário,
        # inicializa via FeaturesCompose para registrar a instância.
        try:
            self.client: UnifiedDataService = SERVICEHUB.unified_data_service
        except Exception:
            FeaturesCompose.unifield_data_services()
            self.client = SERVICEHUB.unified_data_service

    def ensure_card_for_atendimento(self, atendimento: Any) -> TrelloCard:
        """
        Garante criação de Card no Trello para o atendimento.
        """
        existing: Optional[TrelloCard] = getattr(
            atendimento, "trello_card", None
        )
        if existing:
            return existing

        etapa = getattr(atendimento, "etapa_atual", None)
        if not etapa:
            logger.info(
                "Atendimento %s sem etapa_atual; não cria card",
                atendimento.pk,
            )
            raise ValueError("Atendimento sem etapa_atual para Trello")

        lista: Optional[TrelloList] = getattr(etapa, "trello_list", None)
        if not lista:
            from .flow_sync_service import FlowSyncService

            lista = FlowSyncService().ensure_list_for_etapa(etapa)

        # Comentário (PT-BR): Monta nome e descrição rica para o card.
        name: str = self._build_card_name(atendimento)
        desc: str = self._build_rich_description(atendimento)

        # Comentário: Atribui membro se já houver um atendente humano
        id_members: list[str] = []
        atendente = getattr(atendimento, "atendente_humano", None)
        if atendente is not None:
            member_id = MemberSyncService().resolve_member_external_id(
                atendente
            )
            if member_id:
                id_members = [member_id]

        # Comentário: Define custom fields se existirem no board
        custom_fields: dict[str, str] = {}
        try:
            board_id: str = cast(str, lista.board.external_id)
            cf_map = self.client.ensure_custom_fields(
                board_id,
                {
                    "Contato": "text",
                    "Telefone": "text",
                    "Departamento": "text",
                    "Canal": "text",
                    "Prioridade": "text",
                    "Produto/Serviço": "text",
                    "Valor Orçamento": "text",
                    "Categoria Venda": "text",
                    "Atendente": "text",
                },
            )
            # Comentário: Mapeia valores dos campos para IDs resolvidos
            contato = getattr(atendimento, "contato", None)
            nome_contato: str = (
                getattr(contato, "nome_contato", None) or "(não informado)"
            )
            telefone: str = getattr(contato, "telefone", "")
            departamento_nome: str = (
                getattr(getattr(atendimento, "departamento", None), "nome", "")
                or "(não informado)"
            )
            canal: str = getattr(atendimento, "canal", "")
            prioridade: str = getattr(atendimento, "prioridade", "")
            produto_servico: str = getattr(atendimento, "produto_servico", "")
            valor_orc: Optional[Decimal] = getattr(
                atendimento, "valor_orcamento", None
            )
            categoria_venda: str = getattr(
                atendimento, "categoria_venda", ""
            )
            atendente_nome: str = (
                getattr(atendente, "nome", "") if atendente is not None else ""
            )

            def fmt_currency(val: Optional[Decimal]) -> str:
                # Comentário: formata valor monetário com fallback
                if val is None:
                    return ""
                try:
                    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                except Exception:
                    return str(val)

            if cf_map.get("Contato"):
                custom_fields[cf_map["Contato"]] = nome_contato
            if cf_map.get("Telefone"):
                custom_fields[cf_map["Telefone"]] = telefone
            if cf_map.get("Departamento"):
                custom_fields[cf_map["Departamento"]] = departamento_nome
            if cf_map.get("Canal"):
                custom_fields[cf_map["Canal"]] = canal
            if cf_map.get("Prioridade"):
                custom_fields[cf_map["Prioridade"]] = prioridade
            if cf_map.get("Produto/Serviço"):
                custom_fields[cf_map["Produto/Serviço"]] = produto_servico
            if cf_map.get("Valor Orçamento"):
                custom_fields[cf_map["Valor Orçamento"]] = fmt_currency(
                    valor_orc
                )
            if cf_map.get("Categoria Venda"):
                custom_fields[cf_map["Categoria Venda"]] = categoria_venda
            if cf_map.get("Atendente"):
                custom_fields[cf_map["Atendente"]] = atendente_nome
        except Exception:
            custom_fields = {}

        # Comentário: create_item retorna o ID do card; montar payload.
        payload: dict[str, Any] = {
            "name": name,
            "desc": desc,
            "idMembers": id_members or [],
            "custom_fields": custom_fields or {},
        }
        card_id: str = self.client.create_item(
            data_source_id=lista.external_id, payload=payload
        )
        # Buscar dados completos do card para metadados.
        data: Optional[dict[str, Any]] = self.client.get_item(
            data_source_id=lista.external_id, item_id=card_id
        )
        card_data: dict[str, Any] = data if isinstance(data, dict) else {}
        card: TrelloCard = TrelloCard.objects.create(
            atendimento=atendimento,
            list_sync=lista,
            external_id=card_id,
            name=card_data.get("name", name),
            url=card_data.get("shortUrl"),
            metadata=card_data,
        )
        # Comentário: Atualiza descrição com mensagens recentes, sem bloquear criação
        try:
            self.update_card_rich_content(card, atendimento)
        except Exception:
            # Falhas de enriquecimento não devem impedir o fluxo básico
            pass
        return card

    def _build_card_name(self, atendimento: Any) -> str:
        """
        Constrói o nome do card com assunto, prioridade e contato.

        Comentário: foca numa visualização rápida na lista.
        """
        assunto: str = (
            getattr(atendimento, "assunto", None) or f"Atendimento {getattr(atendimento, 'pk', '')}"
        )
        prioridade: str = getattr(atendimento, "prioridade", "normal")
        contato = getattr(atendimento, "contato", None)
        nome_contato: str = getattr(contato, "nome_contato", "") if contato else ""
        contato_hint: str = f" — {nome_contato}" if nome_contato else ""
        return f"[{prioridade}] {assunto}{contato_hint}"

    def _build_rich_description(self, atendimento: Any) -> str:
        """
        Monta descrição rica com dados-chave do atendimento e últimas mensagens.

        Comentário: texto multi-linha para leitura rápida ao abrir o card.
        """
        contato = getattr(atendimento, "contato", None)
        nome_contato: str = getattr(contato, "nome_contato", "") if contato else ""
        telefone: str = getattr(contato, "telefone", "") if contato else ""
        email: str = getattr(contato, "email", "") if contato else ""
        departamento_nome: str = (
            getattr(getattr(atendimento, "departamento", None), "nome", "")
            or "(não informado)"
        )
        etapa_nome: str = (
            getattr(getattr(atendimento, "etapa_atual", None), "nome", "")
            or "(não informado)"
        )
        prioridade: str = getattr(atendimento, "prioridade", "")
        canal: str = getattr(atendimento, "canal", "")
        produto_servico: str = getattr(atendimento, "produto_servico", "")
        valor_orc: Optional[Decimal] = getattr(atendimento, "valor_orcamento", None)
        categoria_venda: str = getattr(atendimento, "categoria_venda", "")
        tags: list[str] = cast(list[str], getattr(atendimento, "tags", []))
        atendente = getattr(atendimento, "atendente_humano", None)
        atendente_nome: str = getattr(atendente, "nome", "") if atendente else ""
        assunto: str = getattr(atendimento, "assunto", "") or "(sem assunto)"
        ultima_msg_dt = getattr(atendimento, "data_ultima_mensagem", None)

        def fmt_currency(val: Optional[Decimal]) -> str:
            if val is None:
                return ""
            try:
                return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            except Exception:
                return str(val)

        linhas: list[str] = [
            (
                f"### Atendimento #{getattr(atendimento, 'pk', '')} — "
                f"{assunto}"
            ),
            "---",
            "Resumo:",
            f"- Contato: {nome_contato or '(não informado)'}",
            f"- Telefone: {telefone}",
            f"- E-mail: {email or '(não informado)'}",
            f"- Departamento: {departamento_nome}",
            f"- Etapa atual: {etapa_nome}",
            f"- Prioridade: {prioridade}",
            f"- Canal: {canal}",
            # Mantém 'Atendente:' para compatibilidade com testes e leitura
            f"- Atendente: {atendente_nome or '(não atribuído)'}",
        ]
        if produto_servico:
            linhas.append(f"Produto/Serviço: {produto_servico}")
        if categoria_venda:
            linhas.append(f"Categoria Venda: {categoria_venda}")
        if valor_orc is not None:
            linhas.append(f"Valor Orçamento: {fmt_currency(valor_orc)}")
        if tags:
            linhas.append(f"Tags: {', '.join(tags)}")
        if ultima_msg_dt:
            try:
                linhas.append(
                    (
                        "- Última mensagem: "
                        f"{timezone.localtime(ultima_msg_dt).strftime('%d/%m/%Y %H:%M')}"
                    )
                )
            except Exception:
                linhas.append("- Última mensagem: (indisponível)")

        # Comentário: blocos de mensagens recentes
        linhas.append("")
        linhas.append("Mensagens recentes:")
        try:
            from smart_core_assistant_painel.app.ui.atendimentos.models import (
                Mensagem,
            )

            msgs_qs = Mensagem.objects.filter(atendimento=atendimento).order_by(
                "-timestamp"
            )[:5]
            for m in msgs_qs:
                conteudo = (m.conteudo or "").replace("\n", " ")
                preview = conteudo[:240] + ("..." if len(conteudo) > 240 else "")
                ts_str = timezone.localtime(m.timestamp).strftime("%d/%m %H:%M")
                linhas.append(
                    f"- [{ts_str}] {m.remetente}: {preview}"
                )
        except Exception:
            linhas.append("(Não foi possível carregar mensagens)")

        return "\n".join(linhas)

    def update_card_rich_content(self, card: TrelloCard, atendimento: Atendimento) -> None:
        """
        Atualiza conteúdo rico do card: descrição, membros e custom fields.

        Comentário: usa adapter Trello com fail-soft em campos ausentes.
        """
        desc: str = self._build_rich_description(atendimento)
        payload: dict[str, Any] = {"desc": desc}

        atendente = getattr(atendimento, "atendente_humano", None)
        member_id: Optional[str] = None
        if atendente is not None:
            member_id = MemberSyncService().resolve_member_external_id(
                atendente
            )

        try:
            board_id: str = cast(str, card.list_sync.board.external_id)
            cf_map = self.client.ensure_custom_fields(
                board_id,
                {
                    "Contato": "text",
                    "Telefone": "text",
                    "Departamento": "text",
                    "Canal": "text",
                    "Prioridade": "text",
                    "Produto/Serviço": "text",
                    "Valor Orçamento": "text",
                    "Categoria Venda": "text",
                    "Atendente": "text",
                },
            )
            contato = getattr(atendimento, "contato", None)
            nome_contato: str = (
                getattr(contato, "nome_contato", None) or "(não informado)"
            )
            telefone: str = getattr(contato, "telefone", "")
            departamento_nome: str = (
                getattr(getattr(atendimento, "departamento", None), "nome", "")
                or "(não informado)"
            )
            canal: str = getattr(atendimento, "canal", "")
            prioridade: str = getattr(atendimento, "prioridade", "")
            produto_servico: str = getattr(atendimento, "produto_servico", "")
            valor_orc: Optional[Decimal] = getattr(
                atendimento, "valor_orcamento", None
            )
            categoria_venda: str = getattr(
                atendimento, "categoria_venda", ""
            )
            atendente_nome: str = (
                getattr(atendente, "nome", "") if atendente is not None else ""
            )

            def fmt_currency(val: Optional[Decimal]) -> str:
                if val is None:
                    return ""
                try:
                    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                except Exception:
                    return str(val)

            cf_values: dict[str, str] = {}
            if cf_map.get("Contato"):
                cf_values[cf_map["Contato"]] = nome_contato
            if cf_map.get("Telefone"):
                cf_values[cf_map["Telefone"]] = telefone
            if cf_map.get("Departamento"):
                cf_values[cf_map["Departamento"]] = departamento_nome
            if cf_map.get("Canal"):
                cf_values[cf_map["Canal"]] = canal
            if cf_map.get("Prioridade"):
                cf_values[cf_map["Prioridade"]] = prioridade
            if cf_map.get("Produto/Serviço"):
                cf_values[cf_map["Produto/Serviço"]] = produto_servico
            if cf_map.get("Valor Orçamento"):
                cf_values[cf_map["Valor Orçamento"]] = fmt_currency(valor_orc)
            if cf_map.get("Categoria Venda"):
                cf_values[cf_map["Categoria Venda"]] = categoria_venda
            if cf_map.get("Atendente"):
                cf_values[cf_map["Atendente"]] = atendente_nome

            if cf_values:
                payload["custom_fields"] = cf_values
        except Exception:
            # Comentário: se não houver Power-Up ou IDs, segue sem custom fields
            pass

        try:
            self.client.update_item(
                data_source_id=card.list_sync.external_id,
                item_id=card.external_id,
                payload=payload,
            )
        except Exception as exc:
            logger.warning("Falha ao atualizar conteúdo do card: {}", exc)

        # Comentário: adiciona membro ao card pela API dedicada (mais confiável)
        try:
            if member_id:
                from smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter import (
                    TrelloUnifiedDataService,
                )
                trello_client = cast(TrelloUnifiedDataService, self.client)
                trello_client.add_member_to_card(card.external_id, member_id)
        except Exception as exc:
            logger.warning("Falha ao adicionar membro ao card (update): {}", exc)

        # Comentário: adiciona comentário com resumo das últimas mensagens
        try:
            from smart_core_assistant_painel.app.ui.atendimentos.models import (
                Mensagem,
            )
            msgs_qs = Mensagem.objects.filter(atendimento=atendimento).order_by(
                "-timestamp"
            )[:3]
            for m in msgs_qs:
                conteudo = (m.conteudo or "").replace("\n", " ")
                preview = conteudo[:500] + ("..." if len(conteudo) > 500 else "")
                ts_str = timezone.localtime(m.timestamp).strftime("%d/%m/%Y %H:%M")
                comment_text = f"[{ts_str}] {m.remetente}: {preview}"
                # Comentário: reutiliza API de comentário do adapter
                self.client.add_relation_property(
                    data_source_id=card.external_id,
                    property_name="Mensagem",
                    target_id=comment_text,
                )
        except Exception:
            # Comentário: ignoramos falhas ao adicionar comentários
            pass
