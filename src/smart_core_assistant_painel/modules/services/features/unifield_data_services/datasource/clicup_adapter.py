"""Adapter do ClickUp para UnifiedDataService.

Este módulo implementa um adapter que conecta o UnifiedDataService
com a API do ClickUp (v2), permitindo operações de criação e
manipulação de espaços, pastas (folders), listas e tarefas através
da interface unificada.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests
from decouple import config
from loguru import logger

from smart_core_assistant_painel.modules.services.features.unifield_data_services.domain.interface.unified_data_service import (
    UnifiedDataService,
)
from smart_core_assistant_painel.modules.services.utils.parameters import (
    UnifieldDataServicesParameters,
)


class ClicupUnifiedDataService(UnifiedDataService):
    """Adapter de `UnifiedDataService` para ClickUp.

    Comentários em Português: esta classe mapeia operações genéricas
    para recursos do ClickUp. Um `container` corresponde a um `space`,
    uma `folder` corresponde ao agrupador por departamento, uma
    `data source` a uma `list` e um `item` a uma `task`.
    """

    def __init__(self, params: UnifieldDataServicesParameters) -> None:
        """Inicializa o adapter do ClickUp.

        Args:
            params: Parâmetros de configuração do serviço.
        """
        self._params = params
        self._observability: bool = params.enable_observability
        self._default_data_source_id: str = params.data_source_id

        # Configura credenciais de API (OAuth access token preferencial)
        oauth_token: str = config("CLICKUP_OAUTH_ACCESS_TOKEN", default="")
        personal_token: str = config("CLICKUP_PERSONAL_TOKEN", default="")
        token: str = oauth_token or personal_token
        if not token:
            raise ValueError(
                "CLICKUP_OAUTH_ACCESS_TOKEN/PERSONAL_TOKEN não configurados"
            )

        # Normaliza header Authorization com Bearer
        if token.lower().startswith("bearer "):
            self._headers: Dict[str, str] = {"Authorization": token}
        else:
            self._headers = {"Authorization": f"Bearer {token}"}

        # Base URL da API v2 do ClickUp
        self._base_url: str = "https://api.clickup.com/api/v2"

        # Opcional: team_id pode ser fornecido no .env para evitar lookup
        self._team_id: str = config("CLICKUP_TEAM_ID", default="")

        if self._observability:
            logger.info("ClicupUnifiedDataService inicializado")

    # -------------------------- Utilitários HTTP ---------------------------
    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Executa requisição HTTP ao ClickUp.

        Comentários: consolida autenticação e tratamento de erros.
        Retorna o corpo JSON como `dict`.
        """
        url = f"{self._base_url}{path}"

        method_map: Dict[str, Any] = {
            "GET": requests.get,
            "POST": requests.post,
            "PUT": requests.put,
            "DELETE": requests.delete,
        }
        req = method_map.get(method)
        if req is None:
            raise ValueError(f"Método HTTP não suportado: {method}")

        resp = req(
            url,
            headers=self._headers,
            params=params,
            json=json,
            timeout=30,
        )
        if not resp.ok:
            logger.error(
                "Falha ClickUp API: {status} {text}",
                status=resp.status_code,
                text=resp.text,
            )
            resp.raise_for_status()
        data: Dict[str, Any] = resp.json() if resp.content else {}
        return data

    def _log(self, message: str, **kwargs: Any) -> None:
        """Emite log informativo quando a observabilidade está ativa."""
        if self._observability:
            logger.info(message, **kwargs)

    def _get_team_id(self) -> str:
        """Obtém o `team_id` do ambiente ou via API.

        Comentário: quando não fornecido em `CLICKUP_TEAM_ID`, busca
        o primeiro time disponível com `GET /team`.
        """
        if self._team_id:
            return self._team_id
        data = self._request("GET", "/team")
        teams: List[Dict[str, Any]] = data.get("teams", [])
        if not teams:
            raise ValueError("Nenhum team disponível na conta ClickUp")
        team_id: str = str(teams[0].get("id", ""))
        self._team_id = team_id
        self._log("team selecionado: {team}", team=team_id)
        return team_id

    # -------------------------- Mapeamento UDS ----------------------------
    def create_container(self, name: str) -> str:
        """Cria um space e retorna seu ID."""
        team_id = self._get_team_id()
        body: Dict[str, Any] = {
            "name": name,
            "private": False,
        }
        data = self._request("POST", f"/team/{team_id}/space", json=body)
        space_id = str(data.get("id", ""))
        self._log("space criado: {name} -> {id}", name=name, id=space_id)
        return space_id

    def add_data_source(
        self,
        container_id: str,
        data_source_id: str,
        position: Optional[float] = None,
    ) -> str:
        """Cria uma lista no space e retorna seu ID.

        Observação: `data_source_id` aqui é usado como nome da lista.
        `position` não é suportado pela API do ClickUp para listas.
        """
        body: Dict[str, Any] = {"name": data_source_id}
        data = self._request("POST", f"/space/{container_id}/list", json=body)
        list_id = str(data.get("id", ""))
        self._log(
            "lista criada: {name} em {space} -> {list}",
            name=data_source_id,
            space=container_id,
            list=list_id,
        )
        return list_id

    def add_list_to_folder(
        self,
        folder_id: str,
        name: str,
        statuses: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Cria uma lista dentro de um folder e retorna seu ID.

        Comentário: usa `POST /folder/{folder_id}/list`.
        Quando `statuses` é fornecido, tenta criar a List já com
        statuses personalizados (tipo `open`/`closed`). Alguns workspaces
        exigem que os statuses sejam definidos na criação para efetivar
        a personalização por List.
        """
        body: Dict[str, Any] = {"name": name}
        if statuses:
            # Comentário: aplica statuses customizados na criação da List
            body["statuses"] = statuses

        data = self._request("POST", f"/folder/{folder_id}/list", json=body)
        list_id = str(data.get("id", ""))
        self._log(
            "lista criada: {name} em folder {folder} -> {list}",
            name=name,
            folder=folder_id,
            list=list_id,
        )
        return list_id

    # -------------------------- Espaços e Folders -------------------------
    def list_spaces(self) -> List[Dict[str, Any]]:
        """Lista spaces disponíveis no workspace (team atual).

        Comentário: usa `GET /team/{team_id}/space`.
        """
        team_id = self._get_team_id()
        data = self._request("GET", f"/team/{team_id}/space")
        spaces: List[Dict[str, Any]] = data.get("spaces", [])
        if isinstance(spaces, list):
            return spaces
        return []

    def ensure_space_by_name(self, name: str) -> str:
        """Garante a existência de um Space com determinado nome.

        Retorna o `space_id`. Se não existir, cria.
        """
        spaces = self.list_spaces()
        for sp in spaces:
            if str(sp.get("name", "")) == name:
                sid: str = str(sp.get("id", ""))
                self._log("space existente: {name} -> {id}", name=name, id=sid)
                return sid
        return self.create_container(name)

    def list_folders(self, space_id: str) -> List[Dict[str, Any]]:
        """Lista folders de um Space.

        Comentário: `GET /space/{space_id}/folder`.
        """
        data = self._request("GET", f"/space/{space_id}/folder")
        folders: List[Dict[str, Any]] = data.get("folders", [])
        if isinstance(folders, list):
            return folders
        return []

    def find_folder_by_name(
        self, space_id: str, name: str
    ) -> Optional[Dict[str, Any]]:
        """Busca folder por nome dentro de um Space."""
        folders = self.list_folders(space_id)
        for f in folders:
            if str(f.get("name", "")) == name:
                return f
        return None

    def create_folder(self, space_id: str, name: str) -> str:
        """Cria um Folder dentro de um Space e retorna seu ID."""
        body: Dict[str, Any] = {"name": name}
        data = self._request("POST", f"/space/{space_id}/folder", json=body)
        folder_id = str(data.get("id", ""))
        self._log(
            "folder criado: {name} em {space} -> {folder}",
            name=name,
            space=space_id,
            folder=folder_id,
        )
        return folder_id

    def list_folder_lists(self, folder_id: str) -> List[Dict[str, Any]]:
        """Lista listas de um folder do ClickUp.

        Comentário: usa `GET /folder/{folder_id}/list`.
        """
        data = self._request("GET", f"/folder/{folder_id}/list")
        lists: List[Dict[str, Any]] = data.get("lists", [])
        if isinstance(lists, list):
            return lists
        return []

    def find_list_in_folder_by_name(
        self, folder_id: str, name: str
    ) -> Optional[Dict[str, Any]]:
        """Busca uma lista por nome dentro de um Folder."""
        lists = self.list_folder_lists(folder_id)
        for lst in lists:
            if str(lst.get("name", "")) == name:
                return lst
        return None

    def update_schema(
        self, data_source_id: str, schema: Dict[str, Any]
    ) -> str:
        """Atualiza a List com campos do schema (inclui statuses/archived).

        Comentário: envia o `schema` diretamente via `PUT /list/{id}`.
        Retorna um ID simbólico de versão baseado na lista.
        """
        _ = self._request("PUT", f"/list/{data_source_id}", json=schema)
        version_id: str = f"schema-{data_source_id}"
        self._log(
            "list atualizada: {list} campos={keys}",
            list=data_source_id,
            keys=list(schema.keys()),
        )
        return version_id

    def _normalize_task_body(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza corpo de criação/atualização de task.

        Comentário: converte apenas campos suportados e ignora nulos.
        """
        body: Dict[str, Any] = {}
        mapping: Dict[str, str] = {
            "name": "name",
            "description": "description",
            "status": "status",
            "priority": "priority",
        }
        for src, dst in mapping.items():
            if src in payload and payload[src] is not None:
                body[dst] = payload[src]

        # due_date deve ser epoch em milissegundos
        if "due_date" in payload and payload["due_date"] is not None:
            try:
                body["due_date"] = int(payload["due_date"])  # type: ignore[arg-type]
            except Exception:
                # Comentário: ignora conversão inválida
                pass

        # assignees deve ser lista de ints/strings
        if "assignees" in payload and isinstance(payload["assignees"], list):
            body["assignees"] = payload["assignees"]

        # tags como lista de strings
        if "tags" in payload and isinstance(payload["tags"], list):
            body["tags"] = payload["tags"]

        return body

    def create_item(self, data_source_id: str, payload: Dict[str, Any]) -> str:
        """Cria uma task na lista e retorna o ID da task."""
        list_id = data_source_id or self._default_data_source_id
        body = self._normalize_task_body(payload)
        data = self._request("POST", f"/list/{list_id}/task", json=body)
        task_id = str(data.get("id", ""))
        self._log(
            "task criada: lista={list} -> {task}", list=list_id, task=task_id
        )
        return task_id

    def update_item(
        self, data_source_id: str, item_id: str, payload: Dict[str, Any]
    ) -> str:
        """Atualiza uma task existente e retorna o ID da operação."""
        body = self._normalize_task_body(payload)
        data = self._request("PUT", f"/task/{item_id}", json=body)
        version_id = str(data.get("id", item_id))
        self._log(
            "task atualizada: lista={list} -> {task}",
            list=data_source_id,
            task=item_id,
        )
        return version_id

    def delete_item(self, item_id: str) -> bool:
        """Exclui uma task do ClickUp.

        Args:
            item_id: ID da task a ser excluída

        Returns:
            True se a exclusão foi bem sucedida
        """
        try:
            self._request("DELETE", f"/task/{item_id}")
            self._log("task excluída: {task}", task=item_id)
            return True
        except Exception as exc:
            self._log(
                "falha ao excluir task {task}: {error}",
                task=item_id,
                error=str(exc),
            )
            return False

    def delete_list(self, list_id: str) -> bool:
        """Exclui uma lista do ClickUp.

        Args:
            list_id: ID da lista a ser excluída

        Returns:
            True se a exclusão foi bem sucedida
        """
        try:
            self._request("DELETE", f"/list/{list_id}")
            self._log("lista excluída: {list}", list=list_id)
            return True
        except Exception as exc:
            self._log(
                "falha ao excluir lista {list}: {error}",
                list=list_id,
                error=str(exc),
            )
            return False

    def delete_folder(self, folder_id: str) -> bool:
        """Exclui uma pasta do ClickUp.

        Args:
            folder_id: ID da pasta a ser excluída

        Returns:
            True se a exclusão foi bem sucedida
        """
        try:
            self._request("DELETE", f"/folder/{folder_id}")
            self._log("pasta excluída: {folder}", folder=folder_id)
            return True
        except Exception as exc:
            self._log(
                "falha ao excluir pasta {folder}: {error}",
                folder=folder_id,
                error=str(exc),
            )
            return False

    def remove_member(self, member_id: str) -> bool:
        """Remove um membro do workspace/time.

        Args:
            member_id: ID do membro a ser removido

        Returns:
            True se a remoção foi bem sucedida
        """
        try:
            team_id = self._get_team_id()
            self._request("DELETE", f"/team/{team_id}/member/{member_id}")
            self._log("membro removido: {member}", member=member_id)
            return True
        except Exception as exc:
            self._log(
                "falha ao remover membro {member}: {error}",
                member=member_id,
                error=str(exc),
            )
            return False

    def add_relation_property(
        self, data_source_id: str, property_name: str, target_id: str
    ) -> str:
        """Adiciona uma propriedade de relação como comentário na task.

        Comentário: ClickUp não tem relação nativa entre tasks/listas
        via API simples. Como representação, adicionamos um comentário
        com a referência ao recurso alvo.
        """
        text = f"{property_name}: {target_id}"
        data = self._request(
            "POST",
            f"/task/{data_source_id}/comment",
            json={"comment_text": text},
        )
        comment_id = str(data.get("id", ""))
        self._log(
            "comentário de relação criado: task={task} -> {comment}",
            task=data_source_id,
            comment=comment_id,
        )
        return comment_id

    def get_container(self, container_id: str) -> Optional[Dict[str, Any]]:
        """Obtém dados do space."""
        try:
            data = self._request("GET", f"/space/{container_id}")
            return data
        except Exception:
            return None

    def get_data_source(self, data_source_id: str) -> Optional[Dict[str, Any]]:
        """Obtém dados da lista."""
        try:
            data = self._request("GET", f"/list/{data_source_id}")
            return data
        except Exception:
            return None

    def get_item(
        self, data_source_id: str, item_id: str
    ) -> Optional[Dict[str, Any]]:
        """Obtém dados da task."""
        try:
            data = self._request("GET", f"/task/{item_id}")
            return data
        except Exception:
            return None

    def append_block(self, container_id: str, block: Dict[str, Any]) -> str:
        """Cria uma task de nota na primeira `list` do space.

        Comentário: ClickUp não possui bloco textual em space; usamos
        uma task como bloco de nota.
        """
        lists_data = self._request("GET", f"/space/{container_id}/list")
        lists: List[Dict[str, Any]] = lists_data.get("lists", [])
        list_id: Optional[str] = str(lists[0].get("id")) if lists else None

        if list_id is None:
            list_id = self.add_data_source(container_id, "Notes")

        payload: Dict[str, Any] = {
            "name": block.get("title", "Note"),
            "description": block.get("text", ""),
        }
        task_id = self.create_item(list_id, payload)
        self._log(
            "bloco anexado como task: space={space} -> {task}",
            space=container_id,
            task=task_id,
        )
        return task_id

    # -------------------------- Extensões de contrato ---------------------
    def list_items(self, data_source_id: str) -> List[Dict[str, Any]]:
        """Lista tasks de uma lista do ClickUp."""
        try:
            data = self._request("GET", f"/list/{data_source_id}/task")
            tasks: List[Dict[str, Any]] = data.get("tasks", [])
            if isinstance(tasks, list):
                return tasks
            return []
        except Exception:
            return []

    def list_data_sources(self, container_id: str) -> List[Dict[str, Any]]:
        """Lista listas de um space do ClickUp."""
        try:
            data = self._request("GET", f"/space/{container_id}/list")
            lists: List[Dict[str, Any]] = data.get("lists", [])
            if isinstance(lists, list):
                return lists
            return []
        except Exception:
            return []

    def set_data_source_position(
        self, data_source_id: str, position: float | str
    ) -> bool:
        """Atualiza posição da lista.

        Comentário: API do ClickUp não expõe `orderindex` público
        para listas; mantemos `NotImplemented` para evitar falso
        suporte.
        """
        raise NotImplementedError("set_data_source_position não suportado")
