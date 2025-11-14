from typing import Any, Dict, List, Optional
from datetime import datetime

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

from ..models import (
    ClickupList,
    ClickupTask,
    ClickupStatus,
    ClickupCustomField,
    ClickupMember,
)
from smart_core_assistant_painel.app.ui.atendimentos.models import Mensagem


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
            # Comentário: após atualizar a Task, sincroniza Custom Fields
            try:
                self.update_custom_fields(atendimento)
            except Exception as exc:
                logger.warning(
                    "Falha ao sincronizar Custom Fields após update: {}",
                    exc,
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
        # Comentário: sincroniza Custom Fields após criação da Task
        try:
            self.update_custom_fields(atendimento)
        except Exception as exc:
            logger.warning(
                "Falha ao sincronizar Custom Fields após criação: {}",
                exc,
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
        # Comentário: sincroniza Custom Fields junto com conteúdo rico
        try:
            self.update_custom_fields(atendimento)
        except Exception as exc:
            logger.warning(
                "Falha ao sincronizar Custom Fields após rich update: {}",
                exc,
            )

    # ---------------------- Custom Fields Sync ----------------------
    def update_custom_fields(self, atendimento: Any) -> None:
        """Atualiza valores de Custom Fields na Task do Atendimento.

        Comentário (PT-BR): Garante que os campos personalizados definidos
        na List do ClickUp estejam mapeados localmente e aplica os valores
        derivados do Atendimento (assunto, departamento, etapa, prioridade,
        contato, canal, telefone e data da última mensagem).
        """
        task: Optional[ClickupTask] = ClickupTask.objects.filter(
            atendimento_id=atendimento.id
        ).first()
        if not task:
            return

        # Comentário: sincroniza catálogo de Custom Fields da List
        self._sync_list_custom_fields(task.list_external_id)

        values: Dict[str, Any] = self._map_cf_values(atendimento)

        # Comentário: aplica valores apenas para campos existentes na List
        for name, value in values.items():
            cf: Optional[ClickupCustomField] = (
                ClickupCustomField.objects.filter(
                    name=name,
                    scope_type="list",
                    scope_external_id=task.list_external_id,
                ).first()
            )
            if cf is None:
                continue

            payload_value: Any = value
            # Comentário: normaliza tipos conforme ClickUp
            try:
                if cf.type == "date":
                    if isinstance(value, datetime):
                        payload_value = int(value.timestamp() * 1000)
                    elif value is None:
                        payload_value = None
                elif cf.type in {"number"}:
                    # Garante número quando possível
                    payload_value = (
                        float(value) if value is not None else None
                    )
                else:
                    # Fallback para texto
                    payload_value = (
                        str(value) if value is not None else None
                    )
            except Exception:
                payload_value = (
                    str(value) if value is not None else None
                )

            try:
                self.udservice.set_task_custom_field(
                    task.external_id, cf.field_id, payload_value
                )
            except Exception as exc:
                logger.warning(
                    "Falha ao aplicar CF '{}' na task {}: {}",
                    name,
                    task.external_id,
                    exc,
                )

    def sync_assignees(self, atendimento: Any, old_atendente_id: Optional[int]) -> None:
        """Sincroniza assignees da Task com base no atendente do Atendimento.

        Comentário (PT-BR): resolve o mapeamento `ClickupMember` para o
        atendente; quando ausente ou local, tenta registrar via e-mail.
        Atualiza a Task no ClickUp com a lista de assignees correspondente.
        """
        task: Optional[ClickupTask] = ClickupTask.objects.filter(
            atendimento_id=atendimento.id
        ).first()
        if not task:
            return

        try:
            atual_id: Optional[int] = getattr(
                atendimento, "atendente_humano_id", None
            )

            # Remoção de assignee quando não há atendente
            if atual_id is None:
                self.udservice.set_task_assignees(task.external_id, [])
                logger.info(
                    "Removidos assignees da task {} (sem atendente)",
                    task.external_id,
                )
                return

            member: Optional[ClickupMember] = (
                ClickupMember.objects.filter(atendente_id=atual_id).first()
            )

            # Se não houver mapeamento ou for local, tenta resolver por e-mail
            if member is None or str(member.external_id).startswith("local-"):
                try:
                    from .member_sync_service import MemberSyncService

                    atendente = getattr(atendimento, "atendente_humano", None)
                    if atendente is not None:
                        MemberSyncService().find_and_register_by_email(atendente)
                        member = ClickupMember.objects.filter(
                            atendente_id=atual_id
                        ).first()
                except Exception as exc:
                    logger.warning(
                        "Falha ao resolver membro do ClickUp por e-mail: {}",
                        exc,
                    )

            if member is None or str(member.external_id).startswith("local-"):
                logger.info(
                    "Sem membro ClickUp resolvido para atendente {} na task {}",
                    atual_id,
                    task.external_id,
                )
                return

            self.udservice.set_task_assignees(
                task.external_id, [str(member.external_id)]
            )
            logger.info(
                "Assignees sincronizados para task {} -> [{}]",
                task.external_id,
                str(member.external_id),
            )
        except Exception as exc:
            logger.warning(
                "Falha ao sincronizar assignees na task {}: {}",
                getattr(task, "external_id", "?"),
                exc,
            )

    def _sync_list_custom_fields(self, list_external_id: str) -> None:
        """Sincroniza o catálogo de Custom Fields da List no banco local."""
        fields: List[Dict[str, Any]] = self.udservice.get_list_custom_fields(
            list_external_id
        )
        if not fields:
            # Comentário: nenhum CF acessível; orientar configuração no ClickUp
            logger.info(
                "List {} sem Custom Fields acessíveis; nada para sincronizar",
                list_external_id,
            )
            return
        for f in fields:
            field_id: str = str(f.get("id", ""))
            name: str = str(f.get("name", ""))
            ftype: str = str(f.get("type", ""))
            if not field_id or not name:
                continue
            obj, _ = ClickupCustomField.objects.update_or_create(
                field_id=field_id,
                defaults={
                    "name": name,
                    "type": ftype,
                    "scope_type": "list",
                    "scope_external_id": list_external_id,
                },
            )
            # Comentário: update_or_create garante persistência do catálogo

    def _map_cf_values(self, atendimento: Any) -> Dict[str, Any]:
        """Monta o dicionário de valores para Custom Fields a partir do Atendimento."""
        contato = getattr(atendimento, "contato", None)
        departamento = getattr(atendimento, "departamento", None)
        etapa = getattr(atendimento, "etapa_atual", None)

        # Comentário: resolve nome do contato com fallback
        contato_nome: str = (
            str(getattr(contato, "nome_contato", ""))
            or str(getattr(contato, "nome_perfil_whatsapp", ""))
            or str(getattr(contato, "nome", ""))
        )
        telefone: Optional[str] = getattr(contato, "telefone", None)
        canal: Optional[str] = getattr(atendimento, "canal", None)
        assunto: Optional[str] = getattr(atendimento, "assunto", None)
        prioridade: str = getattr(atendimento, "prioridade", "normal")

        # Comentário: calcula data da última mensagem
        last_msg: Optional[Mensagem] = (
            Mensagem.objects.filter(atendimento_id=atendimento.id)
            .order_by("-timestamp")
            .first()
        )
        last_dt: Optional[datetime] = (
            getattr(last_msg, "timestamp", None)
            if last_msg is not None
            else getattr(atendimento, "data_ultima_mensagem", None)
        )

        # Comentário: suportar nomes em PT-BR e EN conforme documentação
        values: Dict[str, Any] = {
            # Resumo/Assunto
            "Assunto": assunto,
            "Subject (Summary)": assunto,
            # Departamento
            "Departamento": str(getattr(departamento, "nome", "")),
            "Department": str(getattr(departamento, "nome", "")),
            # Fluxo/List contexto
            "Etapa": str(getattr(etapa, "nome", "")),
            "Flow": str(getattr(getattr(atendimento, "fluxo_atendimento", None), "nome", "")),
            # Prioridade
            "Prioridade": prioridade,
            "Priority (Local)": prioridade,
            # Contato (dados derivados)
            "Contato": contato_nome,
            "Contact Name": contato_nome,
            "Telefone": telefone,
            "Contact Phone": telefone,
            "Contact Email": getattr(contato, "email", None),
            "Contact ID": getattr(contato, "id", None),
            # Canal
            "Canal": canal,
            "Channel": canal,
            # Datas
            "Last Message At": last_dt,
            "First Response At": getattr(atendimento, "data_primeira_resposta", None),
            "Service Start": getattr(atendimento, "data_inicio", None),
            "Service End": getattr(atendimento, "data_fim", None),
            # Feedback/Avaliação
            "Customer Rating (1–5)": getattr(atendimento, "avaliacao", None),
            "Customer Feedback": getattr(atendimento, "feedback", None),
        }
        return values

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
