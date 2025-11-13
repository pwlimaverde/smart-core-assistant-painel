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

from ..models import ClickupList, ClickupStatus
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
        workspace_name: str = config(
            "CLICKUP_APP_ESPACO", default="smart-core-assistant"
        ).strip()
        if not workspace_name:
            raise RuntimeError("CLICKUP_APP_ESPACO não definido")
        space_id: str = self.udservice.ensure_space_by_name(workspace_name)
        logger.info(
            "Workspace ClickUp garantido: {} -> {}", workspace_name, space_id
        )
        return space_id

    def _ensure_department_folder(
        self, space_id: str, departamento_nome: str
    ) -> str:
        """Garante um Folder para o Departamento dentro do Space único."""
        found = self.udservice.find_folder_by_name(space_id, departamento_nome)
        if found:
            folder_id: str = str(found.get("id", ""))
            logger.info(
                "Folder existente para Departamento {} -> {}",
                departamento_nome,
                folder_id,
            )
            return folder_id
        folder_id = self.udservice.create_folder(space_id, departamento_nome)
        logger.info(
            "Folder criado para Departamento {} -> {}",
            departamento_nome,
            folder_id,
        )
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
        if not departamento:
            # Comentário: não cria Folder sem Departamento no banco.
            # Mantém regra "só cadastra se estiver no banco".
            raise RuntimeError(
                (
                    "Departamento não encontrado para FluxoAtendimento {}"
                ).format(fluxo_id)
            )
        departamento_nome = getattr(departamento, "nome", "")
        fluxo_nome = getattr(fluxo, "nome", f"Fluxo {fluxo_id}")

        etapas = list(
            EtapaFluxo.objects.filter(fluxo_id=fluxo_id)
            .order_by("ordem")
            .values("id", "nome", "cor", "tipo_etapa")
        )

        # Comentário: prepara mapeamento de etapas → statuses
        # respeitando grupos do ClickUp: 'open', 'done' e 'closed'.
        # Apenas um 'open' e um 'closed' são permitidos.
        statuses: list[dict[str, str]] = self._build_clickup_statuses(etapas)

        list_obj = ClickupList.objects.filter(
            fluxo_atendimento_id=fluxo_id
        ).first()
        if list_obj:
            self._update_list_statuses(list_obj.external_id, etapas)
            return list_obj.external_id

        space_id = self._ensure_workspace()
        folder_id = self._ensure_department_folder(space_id, departamento_nome)
        # Pré-checagem idempotente: reaproveitar List existente por nome
        try:
            existing = self.udservice.find_list_in_folder_by_name(
                folder_id, fluxo_nome
            )
            if existing:
                list_id = str(existing.get("id", ""))
                logger.info(
                    "List existente reaproveitada por nome: {} -> {}",
                    fluxo_nome,
                    list_id,
                )
                ClickupList.objects.update_or_create(
                    external_id=list_id,
                    defaults={
                        "fluxo_atendimento_id": fluxo_id,
                        "name": fluxo_nome,
                        "space_external_id": space_id,
                    },
                )
                # Atualiza statuses de forma idempotente
                self._update_list_statuses(list_id, etapas)
                return list_id
        except Exception as exc:
            logger.warning(
                (
                    "Falha ao buscar List por nome '{}' em Folder {}: {}. "
                    "Prosseguindo com criação."
                ),
                fluxo_nome,
                folder_id,
                exc,
            )

        # Criação da List com fallback para nome já existente no Folder
        try:
            # Comentário: cria a List já com statuses customizados para
            # evitar herança do Folder/Space que ignora atualização posterior.
            list_id = self.udservice.add_list_to_folder(
                folder_id, fluxo_nome, statuses=statuses
            )
        except Exception as exc:
            logger.warning(
                (
                    "Falha ao criar List '{}' em Folder {}: {}. "
                    "Tentando localizar existente por nome."
                ),
                fluxo_nome,
                folder_id,
                exc,
            )
            existing = self.udservice.find_list_in_folder_by_name(
                folder_id, fluxo_nome
            )
            if existing:
                list_id = str(existing.get("id", ""))
                logger.info(
                    "List existente localizada por nome: {} -> {}",
                    fluxo_nome,
                    list_id,
                )
            else:
                raise
        ClickupList.objects.update_or_create(
            external_id=list_id,
            defaults={
                "fluxo_atendimento_id": fluxo_id,
                "name": fluxo_nome,
                "space_external_id": space_id,
            },
        )
        logger.info(
            "Criada List ClickUp em Folder: {} -> {}", fluxo_nome, list_id
        )
        # Comentário: confirmação pós-criação via GET da List
        try:
            data = self.udservice.get_data_source(list_id)
            server_statuses = (
                data.get("statuses", []) if isinstance(data, dict) else []
            )
            names = (
                ", ".join(
                    [str(s.get("status", "")) for s in server_statuses]
                )
                if isinstance(server_statuses, list)
                else ""
            )
            logger.info(
                "Statuses retornados na criação para List {}: {}",
                list_id,
                names,
            )
            # Comentário: persiste mapeamento inicial mesmo que a API
            # retorne apenas os padrões (to do/complete). Isso garante
            # que os registros de ClickupStatus existam no banco.
            try:
                self._persist_status_mapping(
                    list_id, etapas, server_statuses
                )
            except Exception as persist_err:
                logger.warning(
                    (
                        "Falha ao persistir mapeamento inicial de "
                        "statuses para List {}: {}"
                    ),
                    list_id,
                    persist_err,
                )
        except Exception as confirm_err:
            logger.warning(
                "Não foi possível confirmar statuses na criação: {}",
                confirm_err,
            )

        # Comentário: aplica atualização idempotente dos statuses
        # para garantir consistência caso a criação não os tenha fixado.
        self._update_list_statuses(list_id, etapas)
        return list_id

    def _update_list_statuses(
        self, list_id: str, etapas: list[dict[str, Any]]
    ) -> None:
        """Atualiza statuses da List usando o adapter.

        Espera que cada etapa tenha `nome` e opcional `cor`.
        """
        # Comentário: usar helper para garantir apenas um 'open' e um
        # 'closed'; etapas intermediárias serão 'done'.
        statuses: list[dict[str, str]] = self._build_clickup_statuses(etapas)

        try:
            # Comentário: loga ordem e tipos aplicados para observabilidade
            ordered = ", ".join([s.get("status", "") for s in statuses])
            logger.info("Ordem de statuses configurada: {}", ordered)

            self.udservice.update_schema(
                list_id, {"override_statuses": True, "statuses": statuses}
            )
            logger.info(
                "Atualizados statuses da List {} ({} itens)",
                list_id,
                len(statuses),
            )

            # Comentário: validação pós-atualização via GET list
            try:
                data = self.udservice.get_data_source(list_id)
                server_statuses = (
                    data.get("statuses", []) if isinstance(data, dict) else []
                )
                # Comentário: persiste mapeamento Etapa → Status por List
                self._persist_status_mapping(list_id, etapas, server_statuses)
                count = (
                    len(server_statuses)
                    if isinstance(server_statuses, list)
                    else 0
                )
                names = (
                    ", ".join([str(s.get("status", "")) for s in server_statuses])
                    if isinstance(server_statuses, list)
                    else ""
                )
                logger.info(
                    "Statuses no servidor para List {} ({} itens): {}",
                    list_id,
                    count,
                    names,
                )
                if count <= 2:
                    logger.warning(
                        (
                            "API ClickUp manteve statuses padrão (to do/complete). "
                            "Personalização por List pode não ser suportada via API."
                        )
                    )
            except Exception as confirm_err:
                logger.warning(
                    "Não foi possível confirmar statuses via GET list {}: {}",
                    list_id,
                    confirm_err,
                )
        except Exception as exc:
            logger.error(
                "Falha ao atualizar statuses da List {}: {}", list_id, exc
            )
            # Comentário: ainda assim persiste mapeamento local com
            # atributos padrão para garantir criação de registros.
            try:
                self._persist_status_mapping(list_id, etapas, [])
            except Exception as persist_err:
                logger.warning(
                    (
                        "Falha ao persistir mapeamento após erro de "
                        "atualização para List {}: {}"
                    ),
                    list_id,
                    persist_err,
                )

    def _build_clickup_statuses(
        self, etapas: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """Constroi lista de statuses com tipos válidos do ClickUp.

        Regras:
        - Apenas um status do tipo 'open' e um 'closed'.
        - Etapas intermediárias usam tipo 'done'.
        - Se houver múltiplas etapas de 'finalizacao', somente a
          primeira recebe 'closed'; as demais ficam como 'done'.
        - Se não houver 'finalizacao', a última etapa vira 'closed'.

        Args:
            etapas: lista de dicionários com chaves 'nome', 'cor' e
                'tipo_etapa'.

        Returns:
            Lista de dicionários com chaves 'status', 'type' e 'color'.
        """
        statuses: list[dict[str, str]] = []
        open_set: bool = False
        closed_set: bool = False
        default_color: str = "#6B7280"

        for e in etapas:
            nome = str(e.get("nome", "")).strip()
            cor = str(e.get("cor", default_color)).strip() or default_color
            tipo = str(e.get("tipo_etapa", "")).strip().lower()
            if not nome:
                continue

            status_type: str
            if tipo == "finalizacao":
                if not closed_set:
                    status_type = "closed"
                    closed_set = True
                else:
                    status_type = "done"
            else:
                if not open_set:
                    status_type = "open"
                    open_set = True
                else:
                    status_type = "done"

            statuses.append(
                {"status": nome, "type": status_type, "color": cor}
            )

        # Garantir pelo menos um 'closed' ao final
        if not closed_set and statuses:
            statuses[-1]["type"] = "closed"
            closed_set = True

        # Garantir pelo menos um 'open' no início
        if not open_set and statuses:
            statuses[0]["type"] = "open"

        return statuses

    def archive_list_for_fluxo(self, fluxo_id: int) -> None:
        """Arquiva a List correspondente ao FluxoAtendimento."""
        list_obj = ClickupList.objects.filter(
            fluxo_atendimento_id=fluxo_id
        ).first()
        if not list_obj:
            logger.warning("List não encontrada para fluxo {}", fluxo_id)
            return
        try:
            self.udservice.update_schema(
                list_obj.external_id, {"archived": True}
            )
            logger.info(
                "List arquivada para fluxo {} -> {}",
                fluxo_id,
                list_obj.external_id,
            )
        except Exception as exc:
            logger.error(
                "Falha ao arquivar list {}: {}", list_obj.external_id, exc
            )

    def delete_list_for_fluxo(self, fluxo_id: int) -> None:
        """Exclui permanentemente a List do ClickUp correspondente ao FluxoAtendimento."""
        list_obj = ClickupList.objects.filter(
            fluxo_atendimento_id=fluxo_id
        ).first()
        if not list_obj:
            logger.warning("List não encontrada para fluxo {}", fluxo_id)
            return

        try:
            # Remove mapeamentos ClickupStatus desta List
            ClickupStatus.objects.filter(
                list_external_id=list_obj.external_id
            ).delete()

            # Primeiro remove o registro local
            list_obj.delete()

            # Depois exclui a List do ClickUp
            success = self.udservice.delete_list(list_obj.external_id)

            if success:
                logger.info(
                    "List excluída permanentemente para fluxo {} -> {}",
                    fluxo_id,
                    list_obj.external_id,
                )
            else:
                logger.error(
                    "Falha ao excluir list do ClickUp: {}",
                    list_obj.external_id,
                )
        except Exception as exc:
            logger.error(
                "Falha ao excluir list {}: {}", list_obj.external_id, exc
            )
    def _persist_status_mapping(
        self,
        list_id: str,
        etapas: list[dict[str, Any]],
        server_statuses: list[dict[str, Any]],
    ) -> None:
        """Persiste correlação entre EtapaFluxo e Status da List.

        A correspondência é feita por nome de etapa ↔ nome do status,
        ambos por fluxo/lista. Atualiza ou cria o registro local.
        """
        try:
            server_by_name: dict[str, dict[str, Any]] = {}
            for idx, st in enumerate(server_statuses):
                name = str(st.get("status", "")).strip()
                if not name:
                    continue
                entry = dict(st)
                entry["orderindex"] = int(st.get("orderindex", idx))
                server_by_name[name] = entry

            etapa_ids: list[int] = []
            for e in etapas:
                etapa_id = int(e.get("id", 0))
                nome = str(e.get("nome", "")).strip()
                if not etapa_id or not nome:
                    continue
                etapa_ids.append(etapa_id)
                st = server_by_name.get(nome, {})
                status_name = nome
                status_type = str(st.get("type", "open"))
                color = str(st.get("color", "#6B7280"))
                order_index = int(st.get("orderindex", 0))

                ClickupStatus.objects.update_or_create(
                    etapa_fluxo_id=etapa_id,
                    list_external_id=list_id,
                    defaults={
                        "status_name": status_name,
                        "status_type": status_type,
                        "color": color,
                        "order_index": order_index,
                    },
                )

            # Comentário: remove mapeamentos órfãos (etapas apagadas)
            if etapa_ids:
                qs = ClickupStatus.objects.filter(
                    list_external_id=list_id
                )
                qs = qs.exclude(etapa_fluxo_id__in=etapa_ids)
                qs.delete()
            else:
                # Se não há etapas, remove todos os mapeamentos da List
                ClickupStatus.objects.filter(
                    list_external_id=list_id
                ).delete()
        except Exception as err:
            logger.warning(
                "Falha ao persistir mapeamento de statuses para List {}: {}",
                list_id,
                err,
            )
