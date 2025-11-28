from datetime import timedelta
from typing import Any, Optional, cast

from django.db import transaction
from django.utils import timezone
from loguru import logger

from smart_core_assistant_painel.app.trello_sync.models import (
    TrelloCard,
    TrelloList,
)
from smart_core_assistant_painel.app.trello_sync.services.member_sync_service import (
    MemberSyncService,
)
from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
)
from smart_core_assistant_painel.modules.services import (
    SERVICEHUB,
    FeaturesCompose,
)
from smart_core_assistant_painel.modules.services.features.unifield_data_services.domain.interface.unified_data_service import (
    UnifiedDataService,
)


class TicketSyncService:
    """[TRL-CRD-001] Serviço de sincronização de tickets (Atendimento → Card).

    Criação e Atualização de Cartões.
    """

    def __init__(self) -> None:
        # Comentário (PT-BR): Obtém o UDS do SERVICEHUB. Se necessário,
        # inicializa via FeaturesCompose para registrar a instância.
        try:
            self.client: UnifiedDataService = SERVICEHUB.unified_data_service
        except Exception:
            FeaturesCompose.unifield_data_services()
            self.client = SERVICEHUB.unified_data_service

    def ensure_card_for_atendimento(
        self, atendimento: Any
    ) -> Optional[TrelloCard]:
        """[TRL-CRD-001] Garante criação de Card no Trello para o atendimento.

        Criação e Atualização de Cartões.
        """
        # Lock no atendimento para evitar duplicidade de criação de card
        atendimento_id = getattr(atendimento, "id", None)
        if not atendimento_id:
            return None

        with transaction.atomic():
            atendimento_locked = Atendimento.objects.select_for_update().get(
                id=atendimento_id
            )

            existing: Optional[TrelloCard] = getattr(
                atendimento_locked, "trello_card", None
            )
            if existing:
                return existing

            etapa = getattr(atendimento_locked, "etapa_atual", None)
            if not etapa:
                logger.info(
                    "Atendimento %s sem etapa_atual; aguardando definição para criar card",
                    atendimento_locked.pk,
                )
                return None

            lista: Optional[TrelloList] = getattr(etapa, "trello_list", None)
            if not lista:
                from .flow_sync_service import FlowSyncService

                lista = FlowSyncService().ensure_list_for_etapa(etapa)

            # Comentário (PT-BR): Monta nome e descrição rica para o card.
            name: str = self._build_card_name(atendimento_locked)
            desc: str = self._build_rich_description(atendimento_locked)

            # Comentário: Atribui membro se já houver um atendente humano
            id_members: list[str] = []
            atendente = getattr(atendimento_locked, "atendente_humano", None)
            if atendente is not None:
                member_id = MemberSyncService().resolve_member_external_id(
                    atendente
                )
                if member_id:
                    id_members = [member_id]

            # Comentário: Trello (plano gratuito) — sem uso de Custom Fields

            # Comentário: create_item retorna o ID do card; montar payload.
            # Comentário: define datas (start/due) e labels de prioridade
            data_inicio = getattr(atendimento_locked, "data_inicio", None)
            data_ultima = getattr(
                atendimento_locked, "data_ultima_mensagem", None
            )
            # Comentário: due deve ser no próximo dia em relação ao start;
            # fallback para próxima dia da última mensagem.
            start_str: Optional[str] = (
                timezone.localtime(data_inicio).isoformat()
                if data_inicio is not None
                else None
            )
            if data_inicio is not None:
                try:
                    due_str = timezone.localtime(
                        data_inicio + timedelta(days=1)
                    ).isoformat()
                except Exception:
                    due_str = (data_inicio + timedelta(days=1)).isoformat()
            elif data_ultima is not None:
                try:
                    due_str = timezone.localtime(
                        data_ultima + timedelta(days=1)
                    ).isoformat()
                except Exception:
                    due_str = (data_ultima + timedelta(days=1)).isoformat()
            else:
                due_str = None

            id_labels: list[str] = []
            try:
                board_id: str = cast(str, lista.board.external_id)
                prioridade: str = getattr(
                    atendimento_locked, "prioridade", "normal"
                )
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
                atendimento=atendimento_locked,
                list_sync=lista,
                external_id=card_id,
                name=card_data.get("name", name),
                url=card_data.get("shortUrl"),
                metadata=card_data,
            )
            # Comentário: Atualiza descrição com mensagens recentes, sem bloquear criação
            try:
                self.update_card_rich_content(card, atendimento_locked)
            except Exception:
                # Falhas de enriquecimento não devem impedir o fluxo básico
                pass
            return card

    def _get_status_emoji(self, status: str) -> str:
        """Retorna emoji apropriado para o status do atendimento."""
        emoji_map = {
            "fila": "⏳",
            "em_atendimento": "💬",
            "pendencia": "⏸️",
            "resolvido": "✅",
            "cancelado": "❌",
            "transferido": "↪️",
        }
        return emoji_map.get(status, "📋")

    def _get_prioridade_emoji(self, prioridade: str) -> str:
        """Retorna emoji apropriado para a prioridade."""
        emoji_map = {
            "baixa": "🟢",
            "normal": "🔵",
            "alta": "🟠",
            "urgente": "🔴",
        }
        return emoji_map.get(prioridade.lower(), "⚪")

    def _get_canal_emoji(self, canal: str) -> str:
        """Retorna emoji apropriado para o canal de comunicação."""
        canal_lower = canal.lower()
        if "whatsapp" in canal_lower:
            return "📱"
        elif "telegram" in canal_lower:
            return "✈️"
        elif "email" in canal_lower:
            return "📧"
        elif "web" in canal_lower:
            return "🌐"
        return "💬"

    def _format_time_delta(self, dt: Optional[Any]) -> str:
        """Formata timedelta de forma humanizada.

        Args:
            dt: Datetime a ser comparado com o momento atual.

        Returns:
            String formatada como "há X dia(s)/hora(s)/minuto(s)".
        """
        if dt is None:
            return "(não disponível)"

        try:
            delta = timezone.now() - dt

            if delta.days > 0:
                return f"há {delta.days} dia(s)"

            hours = delta.seconds // 3600
            if hours > 0:
                return f"há {hours} hora(s)"

            minutes = (delta.seconds % 3600) // 60
            if minutes > 0:
                return f"há {minutes} minuto(s)"

            return "há menos de 1 minuto"
        except Exception:
            return "(erro ao calcular)"

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
        Monta descrição rica com formatação Markdown aprimorada.

        Comentário: usa headings, emojis e tempo humanizado para
        leitura visual superior e identificação rápida de informações.
        """
        # Extração de dados do atendimento
        contato = getattr(atendimento, "contato", None)
        nome_contato: str = (
            getattr(contato, "nome_contato", "")
            or getattr(contato, "nome_perfil_whatsapp", "")
            if contato
            else ""
        )
        telefone: str = getattr(contato, "telefone", "") if contato else ""
        email: str = getattr(contato, "email", "") if contato else ""

        status: str = getattr(atendimento, "status", "")
        # prioridade: str = getattr(atendimento, "prioridade", "normal") # Removido da descrição
        canal: str = getattr(atendimento, "canal", "")

        tags: list[str] = cast(list[str], getattr(atendimento, "tags", []))

        atendente = getattr(atendimento, "atendente_humano", None)
        atendente_nome: str = (
            getattr(atendente, "nome", "") if atendente else ""
        )

        assunto: str = getattr(atendimento, "assunto", "") or "(sem assunto)"
        data_inicio = getattr(atendimento, "data_inicio", None)
        ultima_msg_dt = getattr(atendimento, "data_ultima_mensagem", None)

        # Fallback para data_ultima_mensagem se estiver nulo
        if ultima_msg_dt is None:
            try:
                from smart_core_assistant_painel.app.ui.atendimentos.models import (
                    Mensagem,
                )

                last_msg = (
                    Mensagem.objects.filter(atendimento=atendimento)
                    .order_by("-timestamp")
                    .first()
                )
                if last_msg:
                    ultima_msg_dt = last_msg.timestamp
            except Exception:
                pass

        # Obter emojis para visualização
        status_emoji = self._get_status_emoji(status)
        # prioridade_emoji = self._get_prioridade_emoji(prioridade) # Removido
        canal_emoji = self._get_canal_emoji(canal)

        # Calcular tempo total do atendimento
        tempo_total = self._format_time_delta(data_inicio)
        tempo_ultima_msg = self._format_time_delta(ultima_msg_dt)

        # Construir descrição com headings Markdown
        linhas: list[str] = [
            f"# {status_emoji} Atendimento #{getattr(atendimento, 'pk', '')}",
            "",
            f"**Assunto:** {assunto}",
            f"**Canal:** {canal_emoji} {canal}",
            "",
            "## 📋 Informações do Contato",
            "",
            f"**Nome:** {nome_contato or '(não informado)'}",
            f"**Telefone:** `{telefone}`",
            f"**E-mail:** {email or '(não informado)'}",
        ]

        # Seção de métricas
        linhas.extend(
            [
                "",
                "## ⏱️ Métricas",
                "",
                f"**Tempo Total:** {tempo_total}",
                f"**Última Interação:** {tempo_ultima_msg}",
                f"**Atendente:** {atendente_nome or '⏳ Não atribuído'}",
            ]
        )

        # Adicionar tags se existirem
        if tags:
            linhas.extend(
                [
                    "",
                    f"**Tags:** {', '.join(tags)}",
                ]
            )

        # Bloco de análise automática (intents/entidades)
        try:
            historico = atendimento.carregar_historico_mensagens()
            intents = cast(
                list[dict[str, str]], historico.get("intents_detectados", [])
            )
            entidades = cast(
                list[dict[str, str]], historico.get("entidades_extraidas", [])
            )

            if intents or entidades:
                linhas.extend(
                    [
                        "",
                        "## 🤖 Análise de IA",
                        "",
                    ]
                )

            if intents:
                linhas.append("**Intenções Detectadas:**")
                for item in intents[:5]:
                    try:
                        if isinstance(item, dict):
                            k: str = list(item.keys())[0]
                            v: str = str(item.get(k, ""))
                            linhas.append(f"- `{k}`: {v}")
                        else:
                            linhas.append(f"- {str(item)}")
                    except Exception:
                        linhas.append(f"- {str(item)}")
                linhas.append("")

            if entidades:
                linhas.append("**Entidades Extraídas:**")
                for item in entidades[:5]:
                    try:
                        if isinstance(item, dict):
                            k: str = list(item.keys())[0]
                            v: str = str(item.get(k, ""))
                            linhas.append(f"- `{k}`: {v}")
                        else:
                            linhas.append(f"- {str(item)}")
                    except Exception:
                        linhas.append(f"- {str(item)}")
        except Exception:
            linhas.extend(
                [
                    "",
                    "*(Análise automática indisponível)*",
                ]
            )

        # Bloco de mensagens recentes (máximo 10)
        linhas.extend(
            [
                "",
                "## 💬 Mensagens Recentes (últimas 10)",
                "",
            ]
        )

        try:
            from smart_core_assistant_painel.app.ui.atendimentos.models import (
                Mensagem,
                TipoMensagem,
                TipoRemetente,
            )

            # Buscar últimas 10 mensagens de qualquer remetente
            msgs_qs = Mensagem.objects.filter(
                atendimento=atendimento,
                tipo=TipoMensagem.TEXTO_FORMATADO,
            ).order_by("-timestamp")[:10]

            if msgs_qs.exists():
                # Reordenar para cronológico (mais antigo -> mais novo) para leitura natural
                msgs_list = list(msgs_qs)[::-1]

                for m in msgs_list:
                    # Formato: tempo humanizado + conteúdo
                    tempo_msg = self._format_time_delta(m.timestamp)
                    conteudo: str = (m.conteudo or "").replace("\n", " ")
                    preview: str = conteudo[:200] + (
                        "..." if len(conteudo) > 200 else ""
                    )

                    # Identificar remetente com ícone
                    icone_remetente = "👤"  # Contato
                    if m.remetente == TipoRemetente.BOT.value:
                        icone_remetente = "🤖"
                    elif m.remetente == TipoRemetente.ATENDENTE_HUMANO.value:
                        icone_remetente = "👨‍💻"

                    linhas.append(f"**{icone_remetente} {tempo_msg}**")
                    if preview:
                        linhas.append(f"> {preview}")

                    # Mostrar resposta do bot se existir (para mensagens de contato que tiveram resposta)
                    if getattr(m, "resposta_bot", None):
                        resp: str = str(m.resposta_bot).replace("\n", " ")
                        resp_prev: str = resp[:200] + (
                            "..." if len(resp) > 200 else ""
                        )
                        linhas.append(f"> 🤖 *Resposta:* {resp_prev}")

                    linhas.append("")  # Linha em branco entre mensagens
            else:
                linhas.append("*(Nenhuma mensagem recente disponível)*")
        except Exception:
            linhas.append("*(Não foi possível carregar mensagens)*")

        return "\n".join(linhas)

    def update_card_rich_content(
        self, card: TrelloCard, atendimento: Atendimento
    ) -> None:
        """[TRL-CRD-001] Atualiza conteúdo rico do card: descrição, membros e custom fields.

        Criação e Atualização de Cartões.

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
                payload["due"] = timezone.localtime(
                    data_inicio + timedelta(days=1)
                ).isoformat()
            elif data_ultima is not None:
                payload["due"] = timezone.localtime(
                    data_ultima + timedelta(days=1)
                ).isoformat()
            else:
                payload["due"] = None
        except Exception:
            try:
                if data_inicio is not None:
                    payload["due"] = (
                        data_inicio + timedelta(days=1)
                    ).isoformat()
                elif data_ultima is not None:
                    payload["due"] = (
                        data_ultima + timedelta(days=1)
                    ).isoformat()
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

        # atendente = getattr(atendimento, "atendente_humano", None) # Removido variável não utilizada

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
