from typing import Any

from loguru import logger

from smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter import (
    ClicupUnifiedDataService,
)
from smart_core_assistant_painel.modules.services.utils.parameters import (
    UnifieldDataServicesParameters,
)
from smart_core_assistant_painel.modules.services.utils.erros import (
    UnifieldDataServicesError,
)

from ..models import ClickupList, ClickupTask, ClickupStatus


class TicketSyncService:
    """Sincroniza Atendimento com Task do ClickUp."""

    def __init__(self) -> None:
        # Comentário: inicializa adapter com parâmetros e observabilidade ativa
        params = UnifieldDataServicesParameters(
            data_source_id="",
            provider="clickup",
            root_container_name="Unified Data Root",
            enable_observability=True,
            error=UnifieldDataServicesError(message="UDS ClickUp error"),
        )
        self.udservice = ClicupUnifiedDataService(params)

    def ensure_task(
        self,
        atendimento: Any,
        etapa_nome: str,
    ) -> str:
        """Garante criação/atualização da Task para o Atendimento.

        Retorna o external_id da Task.
        """
        existing = ClickupTask.objects.filter(
            atendimento_id=atendimento.id
        ).first()

        list_map = ClickupList.objects.filter(
            fluxo_atendimento_id=atendimento.fluxo_atendimento_id
        ).first()

        if not list_map:
            raise RuntimeError(
                "List não encontrada para o Fluxo do Atendimento"
            )

        body = self._build_task_body(
            atendimento, etapa_nome, list_map.external_id
        )

        if existing:
            self.udservice.update_item(
                list_map.external_id, existing.external_id, body
            )
            logger.info(
                "Atualizada Task ClickUp para atendimento {}", atendimento.id
            )
            return existing.external_id

        task_id: str = self.udservice.create_item(list_map.external_id, body)
        ClickupTask.objects.create(
            atendimento_id=atendimento.id,
            external_id=task_id,
            name=str(body.get("name", ""))[:256],
            list_external_id=list_map.external_id,
        )
        logger.info(
            "Criada Task ClickUp {} para atendimento {}",
            task_id,
            atendimento.id,
        )
        return task_id

    def update_rich_content(self, atendimento: Any, etapa_nome: str) -> None:
        """Atualiza descrição, datas e prioridade da Task."""
        task = ClickupTask.objects.filter(
            atendimento_id=atendimento.id
        ).first()
        if not task:
            return

        body = self._build_task_body(
            atendimento, etapa_nome, task.list_external_id
        )
        self.udservice.update_item(
            task.list_external_id, task.external_id, body
        )
        logger.info(
            "Atualizado conteúdo enriquecido da Task {}", task.external_id
        )

    def append_message_comment(self, mensagem: Any) -> bool:
        """Adiciona a mensagem como comentário Markdown na Task.

        Comentário (PT-BR): mantém a sequência cronológica e evita
        poluição do card usando comentários ricos em markdown.
        """
        try:
            at_id = int(getattr(mensagem, "atendimento_id", 0))
        except Exception:
            at_id = 0
        if not at_id:
            logger.warning("Mensagem sem atendimento id: {}", mensagem)
            return False

        task = ClickupTask.objects.filter(atendimento_id=at_id).first()
        if not task:
            logger.warning(
                "Task não encontrada para atendimento {}", at_id
            )
            return False

        md: str = self._build_message_markdown(mensagem)
        try:
            self.udservice.add_comment(task.external_id, md, notify_all=False)
            logger.info(
                "Comentário de mensagem anexado na Task {}", task.external_id
            )
            return True
        except Exception as exc:
            logger.error(
                "Falha ao anexar comentário na Task {}: {}",
                task.external_id,
                exc,
            )
            return False

    def _build_message_markdown(self, mensagem: Any) -> str:
        """Gera Markdown rico para a mensagem do atendimento.

        Estrutura:
        - Cabeçalho com remetente e timestamp
        - Tipo de mensagem (texto/mídia)
        - Bloco com conteúdo preservando quebras
        - Opcional: resposta do bot
        """
        from django.utils import timezone
        try:
            ts = timezone.localtime(getattr(mensagem, "timestamp"))
        except Exception:
            ts = timezone.now()
        ts_str: str = ts.strftime("%d/%m/%Y %H:%M")

        remetente_raw = str(getattr(mensagem, "remetente", "")).lower()
        if remetente_raw == "bot":
            remetente_lbl = "Bot"
        elif remetente_raw == "atendente_humano":
            remetente_lbl = "Atendente"
        else:
            remetente_lbl = "Contato"

        tipo_raw = str(getattr(mensagem, "tipo", "")).strip()
        tipo_lbl = {
            "extendedTextMessage": "Texto",
            "imageMessage": "Imagem",
            "videoMessage": "Vídeo",
            "audioMessage": "Áudio",
            "documentMessage": "Documento",
            "stickerMessage": "Sticker",
            "locationMessage": "Localização",
            "contactMessage": "Contato",
            "listMessage": "Lista",
            "buttonsMessage": "Botões",
            "pollMessage": "Enquete",
            "reactMessage": "Reação",
        }.get(tipo_raw, "Mensagem")

        conteudo: str = str(getattr(mensagem, "conteudo", ""))
        # Comentário: usar bloco de citação para preservar visual
        quoted: str = "\n".join([f"> {line}" for line in conteudo.splitlines()])

        linhas: list[str] = []
        linhas.append(f"**{remetente_lbl}** — {ts_str}")
        linhas.append(f"Tipo: _{tipo_lbl}_")
        if quoted:
            linhas.append("")
            linhas.append(quoted)

        # Opcional: resposta do bot
        resp = getattr(mensagem, "resposta_bot", None)
        if resp:
            resp_txt = str(resp)
            resp_block = "\n".join(
                [f"> Resposta: {line}" for line in resp_txt.splitlines()]
            )
            linhas.append("")
            linhas.append(resp_block)

        return "\n".join(linhas)

    def _build_task_body(
        self,
        atendimento: Any,
        etapa_nome: str,
        list_external_id: str | None = None,
    ) -> dict[str, Any]:
        """Monta o corpo para criação/atualização de task no ClickUp."""
        name = self._build_task_name(atendimento)
        desc = self._build_rich_description(atendimento)

        priority_map = {"alta": 3, "media": 2, "baixa": 1}
        prio_val = priority_map.get(str(atendimento.prioridade).lower(), 2)

        # Comentário: escolhe o status baseado no mapeamento persistido
        status_val = etapa_nome
        try:
            etapa = getattr(atendimento, "etapa_atual", None)
            etapa_id = int(getattr(etapa, "id", 0))
            if list_external_id and etapa_id:
                st = ClickupStatus.objects.filter(
                    etapa_fluxo_id=etapa_id,
                    list_external_id=list_external_id,
                ).first()
                if st:
                    status_val = st.status_name
        except Exception:
            # Comentário: fallback para nome da etapa recebida
            status_val = etapa_nome

        body: dict[str, Any] = {
            "name": name,
            "description": desc,
            "status": status_val,
            "priority": prio_val,
        }

        # Opcional: datas se existirem
        try:
            if atendimento.data_inicio:
                body["start_date"] = int(
                    atendimento.data_inicio.timestamp() * 1000
                )
            if getattr(atendimento, "data_prevista_conclusao", None):
                dt = atendimento.data_prevista_conclusao
                body["due_date"] = int(dt.timestamp() * 1000)
        except Exception:
            # Comentário: datas podem não estar presentes ou válidas
            pass

        return body

    def _build_task_name(self, atendimento: Any) -> str:
        """Nome padronizado para task a partir do Atendimento."""
        contato = getattr(atendimento, "contato", None)
        contato_nome = getattr(contato, "nome", "").strip() if contato else ""
        assunto = str(getattr(atendimento, "assunto", "")).strip()
        base = assunto or "Atendimento"
        if contato_nome:
            return f"{base} - {contato_nome}"
        return base

    def _build_rich_description(self, atendimento: Any) -> str:
        """Descrição enriquecida baseada em dados do Atendimento.

        Inclui informações de contato, departamento, etapa, prioridade e tags.
        """
        parts: list[str] = []
        contato = getattr(atendimento, "contato", None)
        dep = getattr(atendimento, "departamento", None)
        etapa = getattr(atendimento, "etapa_atual", None)

        parts.append(f"Assunto: {getattr(atendimento, 'assunto', '')}")
        parts.append(f"Departamento: {getattr(dep, 'nome', '')}")
        parts.append(f"Etapa: {getattr(etapa, 'nome', '')}")
        parts.append(f"Prioridade: {getattr(atendimento, 'prioridade', '')}")

        if contato:
            parts.append(f"Contato: {getattr(contato, 'nome', '')}")
            parts.append(f"Canal: {getattr(contato, 'canal', '')}")
            parts.append(f"Telefone: {getattr(contato, 'telefone', '')}")

        # Tags e contexto
        try:
            tags = getattr(atendimento, "tags", [])
            if tags:
                parts.append("Tags: " + ", ".join([str(t) for t in tags]))
        except Exception:
            pass

        return "\n".join(parts)

    def delete_task(self, atendimento_id: int) -> bool:
        """Exclui permanentemente a Task do ClickUp correspondente ao Atendimento."""
        task = ClickupTask.objects.filter(
            atendimento_id=atendimento_id
        ).first()
        if not task:
            logger.warning(
                "Task não encontrada para atendimento {}", atendimento_id
            )
            return False

        try:
            # Primeiro remove o registro local
            task.delete()

            # Depois exclui a Task do ClickUp
            success = self.udservice.delete_item(task.external_id)

            if success:
                logger.info(
                    "Task excluída permanentemente para atendimento {} -> {}",
                    atendimento_id,
                    task.external_id,
                )
                return True
            else:
                logger.error(
                    "Falha ao excluir task do ClickUp: {}", task.external_id
                )
                return False
        except Exception as exc:
            logger.error("Falha ao excluir task {}: {}", task.external_id, exc)
            return False
