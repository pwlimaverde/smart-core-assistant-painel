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

from ..models import ClickupList, ClickupTask


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
            raise RuntimeError("List não encontrada para o Fluxo do Atendimento")

        body = self._build_task_body(atendimento, etapa_nome)

        if existing:
            self.udservice.update_item(list_map.external_id, existing.external_id, body)
            logger.info("Atualizada Task ClickUp para atendimento {}", atendimento.id)
            return existing.external_id

        task_id: str = self.udservice.create_item(list_map.external_id, body)
        ClickupTask.objects.create(
            atendimento_id=atendimento.id,
            external_id=task_id,
            name=str(body.get("name", ""))[:256],
            list_external_id=list_map.external_id,
        )
        logger.info("Criada Task ClickUp {} para atendimento {}", task_id, atendimento.id)
        return task_id

    def update_rich_content(self, atendimento: Any, etapa_nome: str) -> None:
        """Atualiza descrição, datas e prioridade da Task."""
        task = ClickupTask.objects.filter(atendimento_id=atendimento.id).first()
        if not task:
            return

        body = self._build_task_body(atendimento, etapa_nome)
        self.udservice.update_item(task.list_external_id, task.external_id, body)
        logger.info(
            "Atualizado conteúdo enriquecido da Task {}", task.external_id
        )

    def _build_task_body(self, atendimento: Any, etapa_nome: str) -> dict[str, Any]:
        """Monta o corpo para criação/atualização de task no ClickUp."""
        name = self._build_task_name(atendimento)
        desc = self._build_rich_description(atendimento)

        priority_map = {"alta": 3, "media": 2, "baixa": 1}
        prio_val = priority_map.get(str(atendimento.prioridade).lower(), 2)

        body: dict[str, Any] = {
            "name": name,
            "description": desc,
            "status": etapa_nome,
            "priority": prio_val,
        }

        # Opcional: datas se existirem
        try:
            if atendimento.data_inicio:
                body["start_date"] = int(atendimento.data_inicio.timestamp() * 1000)
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