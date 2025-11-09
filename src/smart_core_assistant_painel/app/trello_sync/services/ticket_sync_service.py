from typing import Any, Optional, cast
from decimal import Decimal

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

from datetime import timedelta
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

        # Comentário: Trello (plano gratuito) — sem uso de Custom Fields

        # Comentário: create_item retorna o ID do card; montar payload.
        # Comentário: define datas (start/due) e labels de prioridade
        data_inicio = getattr(atendimento, "data_inicio", None)
        data_ultima = getattr(atendimento, "data_ultima_mensagem", None)
        # Comentário: due deve ser no próximo dia em relação ao start;
        # fallback para próxima dia da última mensagem.
        start_str: Optional[str] = (
            timezone.localtime(data_inicio).isoformat()
            if data_inicio is not None
            else None
        )
        if data_inicio is not None:
            try:
                due_str = (
                    timezone.localtime(
                        data_inicio + timedelta(days=1)
                    ).isoformat()
                )
            except Exception:
                due_str = (
                    (data_inicio + timedelta(days=1)).isoformat()
                )
        elif data_ultima is not None:
            try:
                due_str = (
                    timezone.localtime(
                        data_ultima + timedelta(days=1)
                    ).isoformat()
                )
            except Exception:
                due_str = (
                    (data_ultima + timedelta(days=1)).isoformat()
                )
        else:
            due_str = None

        id_labels: list[str] = []
        try:
            board_id: str = cast(str, lista.board.external_id)
            prioridade: str = getattr(atendimento, "prioridade", "normal")
            labels_map = self.client.ensure_labels(
                board_id,
                {
                    "baixa": "green",
                    "normal": "blue",
                    "alta": "orange",
                    "urgente": "red",
                },
            )
            lb_id = labels_map.get(prioridade)
            if lb_id:
                id_labels = [lb_id]
        except Exception:
            # Comentário: se adapter não suportar labels, segue sem elas
            id_labels = []

        payload: dict[str, Any] = {
            "name": name,
            "desc": desc,
            "idMembers": id_members or [],
            "idLabels": id_labels or [],
            "start": start_str,
            "due": due_str,
            # Comentário: sem "custom_fields" no payload
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
        Constrói o nome do card com assunto e contato.

        Comentário: sequência desejada pelo produto:
        "nome contato - nome fantasia (cliente) - assunto - intents".
        - Usa o primeiro cliente relacionado ao contato (se existir).
        - Limita o tamanho do nome do contato para evitar excesso.
        - Intents são resumidas (até 3) para manter título legível.
        """
        # Assunto com fallback para identificação básica do atendimento
        assunto: str = (
            getattr(atendimento, "assunto", None)
            or f"Atendimento {getattr(atendimento, 'pk', '')}"
        )

        # Nome do contato com fallback (perfil WhatsApp ou telefone)
        contato = getattr(atendimento, "contato", None)
        nome_contato: str = ""
        if contato is not None:
            nome_contato = (
                getattr(contato, "nome_contato", None)
                or getattr(contato, "nome_perfil_whatsapp", None)
                or getattr(contato, "telefone", "")
            ) or ""

        # Limitar tamanho do nome do contato para melhor leitura
        if len(nome_contato) > 40:
            nome_contato = nome_contato[:40] + "..."

        # Nome fantasia do primeiro cliente relacionado ao contato
        nome_fantasia: str = ""
        try:
            cliente_rel = getattr(atendimento, "cliente", None)
            if cliente_rel is not None:
                nome_fantasia = getattr(cliente_rel, "nome_fantasia", "")
        except Exception:
            # Comentário: em casos de erro de relacionamento, ignora nome fantasia
            nome_fantasia = ""

        # Intents detectadas (resumo curto: até 3 itens)
        intents_resumo: str = ""
        try:
            if hasattr(atendimento, "carregar_historico_mensagens"):
                hist = atendimento.carregar_historico_mensagens()
                intents_raw = hist.get("intents_detectados", [])
                nomes: list[str] = []
                for it in intents_raw:
                    # Suporta itens como dict ou string
                    if isinstance(it, dict):
                        nome = (
                            str(it.get("type", ""))
                            or str(it.get("nome", ""))
                            or str(it.get("name", ""))
                        )
                        if nome:
                            nomes.append(nome)
                    elif isinstance(it, str):
                        if it:
                            nomes.append(it)
                    else:
                        # Fallback genérico
                        nomes.append(str(it))
                    if len(nomes) >= 3:
                        break
                if nomes:
                    intents_resumo = " | ".join(nomes)
        except Exception:
            intents_resumo = ""

        # Monta sequência conforme especificação, omitindo partes vazias
        partes: list[str] = []
        if nome_contato:
            partes.append(nome_contato)
        if nome_fantasia:
            partes.append(nome_fantasia)
        if assunto:
            partes.append(assunto)
        if intents_resumo:
            partes.append(intents_resumo)

        titulo: str = " - ".join(partes) if partes else assunto
        return titulo

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
                cur: str = f"R$ {val:,.2f}"
                return (
                    cur.replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")
                )
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

        # Comentário: bloco de análise automática (intents/entidades)
        try:
            historico = atendimento.carregar_historico_mensagens()
            intents = cast(
                list[dict[str, str]], historico.get("intents_detectados", [])
            )
            entidades = cast(
                list[dict[str, str]], historico.get("entidades_extraidas", [])
            )
            if intents or entidades:
                linhas.append("")
                linhas.append("Análise de IA:")
            if intents:
                linhas.append("- Intenções detectadas:")
                for item in intents[:5]:
                    try:
                        k: str = list(item.keys())[0]
                        v: str = str(item.get(k, ""))
                        linhas.append(f"  - {k}: {v}")
                    except Exception:
                        linhas.append(f"  - {str(item)}")
            if entidades:
                linhas.append("- Entidades extraídas:")
                for item in entidades[:5]:
                    try:
                        k: str = list(item.keys())[0]
                        v: str = str(item.get(k, ""))
                        linhas.append(f"  - {k}: {v}")
                    except Exception:
                        linhas.append(f"  - {str(item)}")
        except Exception:
            linhas.append("")
            linhas.append("(Análise automática indisponível)")

        # Comentário: blocos de mensagens recentes
        linhas.append("")
        linhas.append("Mensagens recentes:")
        try:
            from smart_core_assistant_painel.app.ui.atendimentos.models import (
                Mensagem,
                TipoMensagem,
                TipoRemetente,
            )

            msgs_qs = (
                Mensagem.objects.filter(
                    atendimento=atendimento,
                    tipo=TipoMensagem.TEXTO_FORMATADO,
                    remetente=TipoRemetente.CONTATO,
                )
                .order_by("-timestamp")[:5]
            )
            for m in msgs_qs:
                conteudo: str = (m.conteudo or "").replace("\n", " ")
                preview: str = (
                    conteudo[:240] + ("..." if len(conteudo) > 240 else "")
                )
                ts_str: str = timezone.localtime(m.timestamp).strftime(
                    "%d/%m %H:%M"
                )
                linhas.append(f"- [{ts_str}] {m.remetente}: {preview}")
                # Comentário (PT-BR): exibe a resposta do bot abaixo da mensagem
                if getattr(m, "resposta_bot", None):
                    resp: str = str(m.resposta_bot).replace("\n", " ")
                    resp_prev: str = (
                        resp[:240] + ("..." if len(resp) > 240 else "")
                    )
                    linhas.append(f"  Resposta: {resp_prev}")
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

        # Comentário: sincroniza datas e label de prioridade
        data_inicio = getattr(atendimento, "data_inicio", None)
        data_ultima = getattr(atendimento, "data_ultima_mensagem", None)
        try:
            payload["start"] = (
                timezone.localtime(data_inicio).isoformat()
                if data_inicio is not None
                else None
            )
        except Exception:
            payload["start"] = None
        # Comentário: due deve ser no próximo dia em relação ao start;
        # fallback para próxima dia da última mensagem.
        try:
            if data_inicio is not None:
                payload["due"] = (
                    timezone.localtime(
                        data_inicio + timedelta(days=1)
                    ).isoformat()
                )
            elif data_ultima is not None:
                payload["due"] = (
                    timezone.localtime(
                        data_ultima + timedelta(days=1)
                    ).isoformat()
                )
            else:
                payload["due"] = None
        except Exception:
            try:
                if data_inicio is not None:
                    payload["due"] = (
                        (data_inicio + timedelta(days=1)).isoformat()
                    )
                elif data_ultima is not None:
                    payload["due"] = (
                        (data_ultima + timedelta(days=1)).isoformat()
                    )
                else:
                    payload["due"] = None
            except Exception:
                payload["due"] = None

        try:
            prioridade: str = getattr(atendimento, "prioridade", "normal")
            labels_map = self.client.ensure_labels(
                cast(str, card.list_sync.board.external_id),
                {
                    "baixa": "green",
                    "normal": "blue",
                    "alta": "orange",
                    "urgente": "red",
                },
            )
            lb_id = labels_map.get(prioridade)
            if lb_id:
                payload["idLabels"] = [lb_id]
        except Exception:
            # Comentário: se labels não suportadas, ignora
            pass

        atendente = getattr(atendimento, "atendente_humano", None)

        # Comentário: Trello (plano gratuito) — não atualiza Custom Fields

        try:
            self.client.update_item(
                data_source_id=card.list_sync.external_id,
                item_id=card.external_id,
                payload=payload,
            )
        except Exception as exc:
            logger.warning("Falha ao atualizar conteúdo do card: {}", exc)

        # Comentário (PT-BR): removido o envio de comentários ao Trello para
        # evitar duplicação de conteúdo; as mensagens recentes já constam na
        # descrição rica do card.
