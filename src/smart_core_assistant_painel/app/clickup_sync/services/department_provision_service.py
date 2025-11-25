"""Serviço de provisionamento ClickUp para Departamento.

Responsável por garantir que ao criar um Departamento no painel,
seja criado (ou encontrado) um Space com o nome definido em
`CLICKUP_APP_ESPACO` e, em seguida, criado um Folder com o nome
do Departamento dentro desse Space.

Comentários em Português e tipagem completa, linhas ≤79 colunas.
"""

from __future__ import annotations

from typing import Any

from decouple import config
from loguru import logger

from smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter import (
    ClicupUnifiedDataService,
)
from smart_core_assistant_painel.modules.services.utils.erros import (
    UnifieldDataServicesError,
)
from smart_core_assistant_painel.modules.services.utils.parameters import (
    UnifieldDataServicesParameters,
)

from ..models import ClickupFolder, ClickupSpace


class DepartmentProvisionService:
    """Cria/garante Space e Folder para um Departamento."""

    def __init__(self) -> None:
        # Comentário: configura adapter com observabilidade ativa
        params = UnifieldDataServicesParameters(
            data_source_id="",
            provider="clickup",
            root_container_name="Unified Data Root",
            enable_observability=True,
            error=UnifieldDataServicesError(message="UDS ClickUp error"),
        )
        self.udservice = ClicupUnifiedDataService(params)

    def provision_on_department_create(self, departamento: Any) -> None:
        """Provisiona recursos no ClickUp ao criar um Departamento.

        Passos:
        1) Garante Space com nome `CLICKUP_APP_ESPACO`.
        2) Persiste Space em `ClickupSpace` se ainda não existir.
        3) Garante Folder com o nome do departamento dentro do Space.
        """

        space_name: str = config(
            "CLICKUP_APP_ESPACO", default="smart-core-assistant"
        )
        if not space_name:
            logger.warning(
                "CLICKUP_APP_ESPACO vazio; pulando provisionamento de Space."
            )
            return None

        # Garante Space por nome (cria se não existir)
        space_id: str = self.udservice.ensure_space_by_name(space_name)
        logger.info("Space alvo: {} -> {}", space_name, space_id)

        # Persiste Space uma única vez (modelo atual vincula a um depto)
        # Comentário: external_id é único; evitamos duplicar entre
        # departamentos. Guardamos o primeiro registro criado.
        if not ClickupSpace.objects.filter(external_id=space_id).exists():
            ClickupSpace.objects.create(
                departamento_id=int(departamento.id),
                external_id=space_id,
                name=space_name,
            )
            logger.info("Space salvo em ClickupSpace: {}", space_id)
        else:
            logger.info("Space já registrado em ClickupSpace: {}", space_id)

        # Garante Folder com nome do Departamento
        folder_name: str = str(getattr(departamento, "nome", "")).strip()
        if not folder_name:
            logger.warning("Departamento sem nome; não cria Folder.")
            return None

        existing = self.udservice.find_folder_by_name(space_id, folder_name)
        if existing:
            fid: str = str(existing.get("id", ""))
            logger.info("Folder existente: {} -> {}", folder_name, fid)
            ClickupFolder.objects.update_or_create(
                external_id=fid,
                defaults={
                    "departamento_id": int(departamento.id),
                    "name": folder_name,
                    "space_external_id": space_id,
                },
            )
            logger.info("Folder registrado localmente: {}", fid)
            return None

        folder_id: str = self.udservice.create_folder(space_id, folder_name)
        logger.info("Folder criado: {} -> {}", folder_name, folder_id)
        ClickupFolder.objects.update_or_create(
            external_id=folder_id,
            defaults={
                "departamento_id": int(departamento.id),
                "name": folder_name,
                "space_external_id": space_id,
            },
        )
        logger.info("Folder registrado localmente: {}", folder_id)
        return None

    def delete_on_department_delete(self, departamento: Any) -> None:
        """Remove recursos do ClickUp ao excluir um Departamento.

        Passos:
        1) Busca e remove o registro ClickupSpace.
        2) Busca e exclui o Folder do departamento.
        """
        space_name: str = config(
            "CLICKUP_APP_ESPACO", default="smart-core-assistant"
        )

        # Remove o registro local do Space
        space_obj = ClickupSpace.objects.filter(
            departamento_id=departamento.id
        ).first()

        if space_obj:
            space_id = space_obj.external_id
            space_obj.delete()
            logger.info("Space removido localmente: {}", space_id)

            # Busca e exclui o Folder
            folder_name: str = str(getattr(departamento, "nome", "")).strip()
            if folder_name:
                # Primeiro tenta registro local
                local_folder = ClickupFolder.objects.filter(
                    departamento_id=departamento.id,
                    name=folder_name,
                    space_external_id=space_id,
                ).first()
                folder_id = (
                    str(local_folder.external_id) if local_folder else ""
                )
                if not folder_id:
                    existing = self.udservice.find_folder_by_name(
                        space_id, folder_name
                    )
                    if existing:
                        folder_id = str(existing.get("id", ""))

                if folder_id:
                    success = self.udservice.delete_folder(folder_id)
                    if success:
                        logger.info(
                            "Folder excluído do ClickUp: {} -> {}",
                            folder_name,
                            folder_id,
                        )
                    else:
                        logger.error("Falha ao excluir folder: {}", folder_id)

                # Remove registro local, se existir
                if local_folder:
                    local_folder.delete()
                    logger.info(
                        "Registro local de Folder removido: {}", folder_name
                    )
        else:
            logger.warning(
                "Space não encontrado para departamento {}", departamento.id
            )
