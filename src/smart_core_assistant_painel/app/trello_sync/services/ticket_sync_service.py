from datetime import timedelta
from typing import Any, Optional, cast

import requests

from django.db import transaction
from django.utils import timezone
from loguru import logger

from smart_core_assistant_painel.app.trello_sync.models import (
    TrelloCard,
    TrelloList,
)
from smart_core_assistant_painel.app.trello_sync.services.flow_sync_service import (
    FlowSyncService,
)
from smart_core_assistant_painel.app.trello_sync.services.member_sync_service import (
    MemberSyncService,
)
from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
)
from smart_core_assistant_painel.app.ui.operacional.models import TipoEtapa
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
                    conteudo: str = m.conteudo or ""

                    # Identificar remetente com ícone e rótulo textual
                    icone_remetente = "👤"
                    label_remetente = "Cliente"

                    if m.remetente == TipoRemetente.BOT.value:
                        icone_remetente = "🤖"
                        label_remetente = "Bot"
                    elif m.remetente == TipoRemetente.ATENDENTE_HUMANO.value:
                        icone_remetente = "👨‍💻"
                        label_remetente = "Atendente"

                    linhas.append(
                        f"**{icone_remetente} {label_remetente}** - {tempo_msg}"
                    )

                    if conteudo:
                        # Preserva quebras de linha e adiciona > em cada linha
                        quoted_content = "\n".join(
                            f"> {line}" for line in conteudo.splitlines()
                        )
                        linhas.append(quoted_content)

                    # Mostrar resposta do bot se existir (para mensagens de contato que tiveram resposta)
                    if getattr(m, "resposta_bot", None):
                        resp: str = str(m.resposta_bot)
                        if resp:
                            quoted_resp = "\n".join(
                                f"> {line}" for line in resp.splitlines()
                            )
                            linhas.append(f"> 🤖 *Resposta:*\n{quoted_resp}")

                    linhas.append("")  # Linha em branco entre mensagens
            else:
                linhas.append("*(Nenhuma mensagem recente disponível)*")
        except Exception:
            linhas.append("*(Não foi possível carregar mensagens)*")

        return "\n".join(linhas)

    def update_card_rich_content(self, atendimento: Atendimento) -> None:
        """[TRL-CRD-001] Atualiza conteúdo rico do card: descrição, membros e custom fields.

        Criação e Atualização de Cartões.

        Comentário: usa adapter Trello com fail-soft em campos ausentes.
        """
        # Recupera card do atendimento
        card: Optional[TrelloCard] = getattr(atendimento, "trello_card", None)
        if not card:
            logger.warning(
                "Atendimento {} sem card Trello para atualizar.",
                atendimento.pk,
            )
            return

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

    def sync_card_members(
        self, atendimento: Atendimento, old_atendente_id: Optional[int] = None
    ) -> None:
        """Sincroniza membros do card Trello com o atendente responsável.

        Args:
            atendimento: Instância de ``Atendimento``.
            old_atendente_id: ID do atendente anterior (opcional).
        """
        card: Optional[TrelloCard] = getattr(atendimento, "trello_card", None)
        if not card:
            logger.warning(
                "Atendimento {} sem card Trello para sync membros.",
                atendimento.pk,
            )
            return

        # 1. Resolver membro atual
        atendente_atual = getattr(atendimento, "atendente_humano", None)
        member_id_atual: Optional[str] = None
        if atendente_atual:
            member_id_atual = MemberSyncService().resolve_member_external_id(
                atendente_atual
            )

        # 2. Resolver membro anterior (se houver)
        member_id_anterior: Optional[str] = None
        if old_atendente_id:
            try:
                from smart_core_assistant_painel.app.ui.operacional.models import (
                    Atendente,
                )

                old_atendente = Atendente.objects.get(id=old_atendente_id)
                member_id_anterior = (
                    MemberSyncService().resolve_member_external_id(
                        old_atendente
                    )
                )
            except Exception:
                pass

        # 3. Atualizar no Trello
        try:
            # Adicionar novo membro
            if member_id_atual:
                try:
                    self.client.add_member_to_card(
                        card.external_id, member_id_atual
                    )
                except requests.exceptions.HTTPError as http_err:
                    # [FIX] Silencia erro se membro já estiver no card (400)
                    if (
                        http_err.response is not None
                        and http_err.response.status_code == 400
                        and "already on the card"
                        in http_err.response.text.lower()
                    ):
                        logger.info(
                            "Membro {} já está no card {}. Ignorando.",
                            member_id_atual,
                            card.external_id,
                        )
                    else:
                        # Loga outros erros HTTP como warning
                        logger.warning(
                            "Falha HTTP ao adicionar membro {} ao card {}: {}",
                            member_id_atual,
                            card.external_id,
                            http_err,
                        )
                except Exception as exc:
                    logger.warning(
                        "Falha ao adicionar membro {} ao card {}: {}",
                        member_id_atual,
                        card.external_id,
                        exc,
                    )

            # Remover membro anterior (se diferente e existir)
            if member_id_anterior and member_id_anterior != member_id_atual:
                try:
                    self.client.remove_member_from_card(
                        card.external_id, member_id_anterior
                    )
                except Exception as exc:
                    logger.warning(
                        "Falha ao remover membro {} do card {}: {}",
                        member_id_anterior,
                        card.external_id,
                        exc,
                    )

        except Exception as exc:
            logger.error("Erro geral ao sincronizar membros do card: {}", exc)

    def move_card_to_etapa(self, atendimento: Atendimento) -> None:
        """Move o card Trello para a lista correspondente à etapa atual.

        Args:
            atendimento: Instância de ``Atendimento``.
        """
        card: Optional[TrelloCard] = getattr(atendimento, "trello_card", None)
        if not card:
            logger.warning(
                "Atendimento {} sem card Trello para mover.", atendimento.pk
            )
            return

        etapa = getattr(atendimento, "etapa_atual", None)
        if not etapa:
            logger.warning(
                "Atendimento {} sem etapa atual definida.", atendimento.pk
            )
            return

        # Garante que a lista da etapa existe
        from .flow_sync_service import FlowSyncService

        trello_list = FlowSyncService().ensure_list_for_etapa(etapa)
        if not trello_list:
            logger.error(
                "Falha ao obter lista Trello para etapa {}.", etapa.pk
            )
            return

        # Se já estiver na lista correta, ignora (mas atualiza referência local se precisar)
        if card.list_sync_id == trello_list.id:
            return

        # Verifica se é uma movimentação entre boards diferentes (Cross-Board)
        current_board_id = card.list_sync.board_id if card.list_sync else None
        target_board_id = trello_list.board_id

        needs_cross_board_move = (
            current_board_id is not None
            and current_board_id != target_board_id
        )

        try:
            if needs_cross_board_move:
                logger.info(
                    "Card {} mudando de board (ID {} -> {}).",
                    card.external_id,
                    current_board_id,
                    target_board_id,
                )
                # Recupera external_id do board de destino
                target_board_ext = trello_list.board.external_id
                self.client.move_item_to_board(
                    item_id=card.external_id,
                    target_board_id=target_board_ext,
                    target_list_id=trello_list.external_id,
                )
            else:
                # Mesmo board, movimento simples de lista
                self.client.move_item(
                    card.external_id, trello_list.external_id
                )

            # Atualiza referência local
            card.list_sync = trello_list
            card.save(update_fields=["list_sync"])

            logger.info(
                "Card {} movido para lista {} (Etapa {})",
                card.external_id,
                trello_list.name,
                etapa.nome,
            )

        except requests.exceptions.HTTPError as http_exc:
            # Tratamento específico para 404 (Lista não existe mais no Trello)
            if http_exc.response.status_code == 404:
                logger.warning(
                    "Lista Trello {} não encontrada (404). Tentando recuperar...",
                    trello_list.external_id,
                )
                try:
                    # 1. Remove a lista obsoleta do banco
                    old_list_id = trello_list.external_id
                    trello_list.delete()

                    # 2. Garante recriação da lista correta
                    flow_service = FlowSyncService()
                    new_list = flow_service.ensure_list_for_etapa(etapa)

                    logger.info(
                        "Lista recriada: {} -> {}. Tentando mover card novamente...",
                        old_list_id,
                        new_list.external_id,
                    )

                    # 3. Tenta mover novamente (re-avaliando cross-board se necessário)
                    # Nota: na recuperação simplificamos para move_item ou move_item_to_board
                    # Assumindo que a recriação já traz o board correto.

                    target_board_ext_rec = new_list.board.external_id

                    if needs_cross_board_move:
                        self.client.move_item_to_board(
                            item_id=card.external_id,
                            target_board_id=target_board_ext_rec,
                            target_list_id=new_list.external_id,
                        )
                    else:
                        self.client.move_item(
                            card.external_id, new_list.external_id
                        )

                    # 4. Atualiza referência local
                    card.list_sync = new_list
                    card.save(update_fields=["list_sync"])

                except Exception as recovery_exc:
                    logger.error(
                        "Falha na recuperação automática de lista 404: {}",
                        recovery_exc,
                    )
            else:
                # Outros erros HTTP
                logger.error(
                    "Erro HTTP ao mover card {} para lista {}: {}",
                    card.external_id,
                    trello_list.external_id,
                    http_exc,
                )
        except Exception as exc:
            logger.error(
                "Falha ao mover card {} para lista {}: {}",
                card.external_id,
                trello_list.external_id,
                exc,
            )

    def process_webhook_card_move(
        self, card_id: str, list_after_id: str, member_creator_id: str
    ) -> None:
        """Processa movimentação de card originada no Trello (Webhook).

        Args:
            card_id: ID externo do card.
            list_after_id: ID externo da lista de destino.
            member_creator_id: ID externo do usuário que moveu.
        """
        try:
            # 1. Localizar Card e Lista no banco
            card = TrelloCard.objects.select_related("atendimento").get(
                external_id=card_id
            )
            nova_lista = TrelloList.objects.select_related("etapa").get(
                external_id=list_after_id
            )

            atendimento = card.atendimento
            nova_etapa = nova_lista.etapa

            # 2. Verificar se houve mudança real de etapa
            if atendimento.etapa_atual_id == nova_etapa.id:
                # Apenas mudou de lista (se houver múltiplas listas por etapa, o que não é o caso padrão)
                # ou evento duplicado. Atualiza referência do card apenas.
                if card.list_sync_id != nova_lista.id:
                    card.list_sync = nova_lista
                    card.save(update_fields=["list_sync"])
                return

            # 3. Atualizar Etapa do Atendimento
            # Importante: Usar o service de estrutura para garantir regras de negócio/transição?
            # Ou atualizar direto? Para evitar loops, idealmente usamos um método que saiba
            # que a origem é externa. Mas o `AttendanceStructureManager` pode não ter essa flag.
            # Vamos atualizar direto e confiar que os sinais tratarão o resto,
            # MAS precisamos evitar que o sinal de `post_save` do Atendimento tente mover o card de volta
            # ou duplicar a ação.
            # O `task_atendimento_move_to_etapa_list` verifica se já está na lista.
            # Então, se atualizarmos o `card.list_sync` ANTES de salvar o atendimento,
            # a task de sync vai ver que já está certo.

            # Recupera a etapa anterior para comparação
            etapa_anterior = atendimento.etapa_atual

            logger.info(
                "Card {} movido no Trello para lista {}. Atualizando Atendimento {} para etapa {}.",
                card_id,
                nova_lista.name,
                atendimento.pk,
                nova_etapa.nome,
            )

            with transaction.atomic():
                # Atualiza referência do card
                card.list_sync = nova_lista
                card.save(update_fields=["list_sync"])

                # Atualiza etapa do atendimento
                # Flag para indicar origem externa (se necessário nos signals)
                atendimento._syncing_from_trello = True
                atendimento.etapa_atual = nova_etapa
                atendimento.save(update_fields=["etapa_atual"])

                # --- Lógica de Atribuição de Atendente (FILA -> TRABALHO) ---
                if (
                    etapa_anterior
                    and etapa_anterior.tipo_etapa == TipoEtapa.FILA
                    and nova_etapa.tipo_etapa == TipoEtapa.TRABALHO
                    and member_creator_id
                ):
                    try:
                        atendente = MemberSyncService().resolve_atendente_by_external_id(
                            member_creator_id
                        )
                        if atendente:
                            logger.info(
                                "Movimento Trello detectado como 'Assumir Atendimento'. Atendente identificado: {}",
                                getattr(atendente, "nome", "Desconhecido"),
                            )
                            # Usa método que atribui, muda status e envia saudação
                            # Importante: transferir_para_humano_com_saudacao espera atendente_id
                            atendimento.transferir_para_humano_com_saudacao(
                                atendente_id=atendente.pk,
                            )
                        else:
                            logger.warning(
                                "Movimento para 'Em Trabalho' no Trello com member_id {} não resolvido para nenhum atendente.",
                                member_creator_id,
                            )
                    except Exception as e:
                        logger.error(
                            "Erro ao tentar atribuir atendente via movimento Trello: {}",
                            e,
                        )

        except TrelloCard.DoesNotExist:
            logger.warning(
                "Card movido no Trello {} não encontrado no sistema.", card_id
            )
        except TrelloList.DoesNotExist:
            logger.warning(
                "Lista de destino {} não encontrada no sistema.", list_after_id
            )
        except Exception as exc:
            logger.error(
                "Erro ao processar movimento de card via webhook: {}", exc
            )
