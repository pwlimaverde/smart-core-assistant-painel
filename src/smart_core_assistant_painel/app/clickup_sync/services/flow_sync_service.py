from typing import Any

from loguru import logger
from decouple import config

from smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter import (
    ClicupUnifiedDataService,
)
from smart_core_assistant_painel.modules.services.utils.parameters import (
    UnifieldDataServicesParameters,
)
from smart_core_assistant_painel.modules.services.utils.erros import (
    UnifieldDataServicesError,
)

from ..models import ClickupList
from smart_core_assistant_painel.app.ui.operacional.models import (
    FluxoAtendimento,
    EtapaFluxo,
    Departamento,
)


class FlowSyncService:
    """Sincroniza Departamentos/Fluxos com Space único, Folder e Lists.

    Organização:
    - Space único definido por `CLICKUP_APP_ESPACO`.
    - Folder por Departamento.
    - List por FluxoAtendimento dentro do Folder do Departamento.
    - EtapaFluxo mapeada para os `statuses` da List.
    """

    def __init__(self) -> None:
        # Comentário: inicializa adapter do ClickUp com parâmetros explícitos
        params = UnifieldDataServicesParameters(
            data_source_id="",
            provider="clickup",
            root_container_name="Unified Data Root",
            enable_observability=True,
            error=UnifieldDataServicesError(message="UDS ClickUp error"),
        )
        self.udservice = ClicupUnifiedDataService(params)

    def _ensure_workspace(self) -> str:
        """Garante o Space único definido em `CLICKUP_APP_ESPACO`.

        Comentário: não persiste em tabela local para evitar conflitos
        de `external_id` único entre departamentos.
        """
        workspace_name: str = config("CLICKUP_APP_ESPACO", default="smart-core-assistant").strip()
        if not workspace_name:
            raise RuntimeError("CLICKUP_APP_ESPACO não definido")
        space_id: str = self.udservice.ensure_space_by_name(workspace_name)
        logger.info("Workspace ClickUp garantido: {} -> {}", workspace_name, space_id)
        return space_id

    def _ensure_department_folder(self, space_id: str, departamento_nome: str) -> str:
        """Garante um Folder para o Departamento dentro do Space único."""
        found = self.udservice.find_folder_by_name(space_id, departamento_nome)
        if found:
            folder_id: str = str(found.get("id", ""))
            logger.info("Folder existente para Departamento {} -> {}", departamento_nome, folder_id)
            return folder_id
        folder_id = self.udservice.create_folder(space_id, departamento_nome)
        logger.info("Folder criado para Departamento {} -> {}", departamento_nome, folder_id)
        return folder_id

    def ensure_list_for_fluxo_from_db(self, fluxo_id: int) -> str:
        """Garante a List do Fluxo no Folder do Departamento e atualiza statuses.

        Comentário: resolve nomes e etapas diretamente do banco.
        """
        fluxo = FluxoAtendimento.objects.filter(id=fluxo_id).first()
        if not fluxo:
            raise RuntimeError(f"FluxoAtendimento não encontrado: {fluxo_id}")

        dep_id = int(getattr(fluxo, "departamento_id", 0))
        departamento = Departamento.objects.filter(id=dep_id).first()
        departamento_nome = getattr(departamento, "nome", "Departamento")
        fluxo_nome = getattr(fluxo, "nome", f"Fluxo {fluxo_id}")

        etapas = list(
            EtapaFluxo.objects.filter(fluxo_id=fluxo_id).order_by("ordem").values("nome", "cor")
        )

        list_obj = ClickupList.objects.filter(fluxo_atendimento_id=fluxo_id).first()
        if list_obj:
            self._update_list_statuses(list_obj.external_id, etapas)
            return list_obj.external_id

        space_id = self._ensure_workspace()
        folder_id = self._ensure_department_folder(space_id, departamento_nome)
        list_id = self.udservice.add_list_to_folder(folder_id, fluxo_nome)
        ClickupList.objects.create(
            fluxo_atendimento_id=fluxo_id,
            external_id=list_id,
            name=fluxo_nome,
            space_external_id=space_id,
        )
        logger.info("Criada List ClickUp em Folder: {} -> {}", fluxo_nome, list_id)
        self._update_list_statuses(list_id, etapas)
        return list_id

    def _update_list_statuses(self, list_id: str, etapas: list[dict[str, Any]]) -> None:
        """Atualiza statuses da List usando o adapter.

        Espera que cada etapa tenha `nome` e opcional `cor`.
        """
        statuses: list[dict[str, str]] = []
        for e in etapas:
            nome = str(e.get("nome", "")).strip()
            cor = str(e.get("cor", "grey")).strip() or "grey"
            if not nome:
                continue
            statuses.append({"status": nome, "type": "custom", "color": cor})

        try:
            self.udservice.update_schema(
                list_id,
                {"statuses": statuses},
            )
            logger.info(
                "Atualizados statuses da List {} ({} itens)",
                list_id,
                len(statuses),
            )
        except Exception as exc:
            logger.error("Falha ao atualizar statuses da List {}: {}", list_id, exc)

    def archive_list_for_fluxo(self, fluxo_id: int) -> None:
        """Arquiva a List correspondente ao FluxoAtendimento."""
        list_obj = ClickupList.objects.filter(fluxo_atendimento_id=fluxo_id).first()
        if not list_obj:
            logger.warning("List não encontrada para fluxo {}", fluxo_id)
            return
        try:
            self.udservice.update_schema(list_obj.external_id, {"archived": True})
            logger.info("List arquivada para fluxo {} -> {}", fluxo_id, list_obj.external_id)
        except Exception as exc:
            logger.error("Falha ao arquivar list {}: {}", list_obj.external_id, exc)