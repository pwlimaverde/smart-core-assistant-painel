"""Adapter do Trello para UnifiedDataService.

Este módulo implementa um adapter que conecta o UnifiedDataService
com a API do Trello, permitindo operações de criação e manipulação
de boards, listas e cards através da interface unificada.
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


class TrelloUnifiedDataService(UnifiedDataService):
    """Adapter de `UnifiedDataService` para Trello.

    Comentários em Português: esta classe mapeia operações genéricas
    para recursos do Trello. Um `container` corresponde a um `board`,
    uma `data source` a uma `list` e um `item` a um `card`.
    """

    def __init__(self, params: UnifieldDataServicesParameters) -> None:
        """Inicializa o adapter do Trello.

        Args:
            params: Parâmetros de configuração do serviço.
        """
        self._params = params
        self._observability: bool = params.enable_observability
        self._default_data_source_id: str = params.data_source_id

        # Configura credenciais de API
        self._api_key: str = config("TRELLO_API_KEY", default="")
        self._token: str = config("TRELLO_TOKEN", default="")
        if not self._api_key or not self._token:
            raise ValueError(
                "TRELLO_API_KEY/TRELLO_TOKEN não configurados no ambiente"
            )

        # Base URL da API do Trello
        self._base_url: str = "https://api.trello.com/1"

        if self._observability:
            logger.info("TrelloUnifiedDataService inicializado")

    # -------------------------- Utilitários HTTP ---------------------------
    def _auth_params(self) -> Dict[str, str]:
        """Retorna parâmetros de autenticação padrão para a API."""
        return {"key": self._api_key, "token": self._token}

    def _normalize_query_params(
        self, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Normaliza valores para envio em query string.

        Comentário (PT-BR): A API do Trello espera booleanos como
        strings minúsculas ("true"/"false") e ignora parâmetros
        com valor `None`. Esta função converte booleanos e remove
        chaves com valores `None` antes de enviar.
        """
        normalized: Dict[str, Any] = {}
        for key, value in params.items():
            if isinstance(value, bool):
                normalized[key] = "true" if value else "false"
            elif value is None:
                # Não incluir parâmetros nulos na query
                continue
            else:
                normalized[key] = value
        return normalized

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Executa requisição HTTP ao Trello.

        Comentários em Português: consolida autenticação e tratamento
        de erros. Retorna o corpo JSON como `dict`.
        """
        url = f"{self._base_url}{path}"
        all_params: Dict[str, Any] = self._auth_params()
        if params:
            all_params.update(params)
            all_params = self._normalize_query_params(all_params)

        method_map: Dict[str, Any] = {
            "GET": requests.get,
            "POST": requests.post,
            "PUT": requests.put,
            "DELETE": requests.delete,
        }
        req = method_map.get(method)
        if req is None:
            raise ValueError(f"Método HTTP não suportado: {method}")

        resp = req(url, params=all_params, json=json, timeout=30)
        if not resp.ok:
            # Comentário: log detalhado para diagnóstico
            logger.error(
                "Falha Trello API: {status} {text}",
                status=resp.status_code,
                text=resp.text,
            )
            resp.raise_for_status()
        return resp.json()

    def _log(self, message: str, **kwargs: Any) -> None:
        """Emite log informativo quando a observabilidade está ativa.

        Comentário: aceita placeholders nomeados no `message` e valores
        via `kwargs`, compatível com o formato do `loguru`.
        """
        if self._observability:
            logger.info(message, **kwargs)

    # -------------------------- Mapeamento UDS ----------------------------
    def create_container(self, name: str) -> str:
        """Cria um board e retorna seu ID."""
        # Comentário: Trello espera boolean em minúsculo na query
        body: Dict[str, Any] = {"name": name, "defaultLists": False}
        data = self._request("POST", "/boards/", params=body)
        board_id = data.get("id", "")
        self._log(f"board criado: {name} -> {board_id}")
        return board_id

    def add_data_source(
        self,
        container_id: str,
        data_source_id: str,
        position: Optional[float] = None,
    ) -> str:
        """Cria uma lista no board e retorna seu ID.

        Observação: `data_source_id` aqui é utilizado como nome da lista.
        """
        params: Dict[str, Any] = {
            "name": data_source_id,
            "idBoard": container_id,
            "pos": position,
        }
        data = self._request("POST", "/lists", params=params)
        list_id = data.get("id", "")
        self._log(
            "lista criada: {name} em {board} -> {list}",
            name=data_source_id,
            board=container_id,
            list=list_id,
        )
        return list_id

    def set_data_source_position(
        self, data_source_id: str, position: float | str
    ) -> bool:
        """Atualiza a posição de uma lista no board (Trello).

        Comentário: usa PUT /lists/{id} com parâmetro `pos`.
        """
        params: Dict[str, Any] = {"pos": position}
        data = self._request("PUT", f"/lists/{data_source_id}", params=params)
        self._log(
            "pos atualizado: lista={list} -> {pos}",
            list=data.get("id", data_source_id),
            pos=data.get("pos", position),
        )
        return True

    def update_schema(
        self, data_source_id: str, schema: Dict[str, Any]
    ) -> str:
        """Atualiza o schema lógico associado à lista.

        Comentário: Trello não possui um `schema` nativo de lista;
        aqui registramos o schema como metadado lógico (sem criar
        campos customizados automaticamente). Integração com custom
        fields pode ser adicionada futuramente.
        """
        # Implementação mínima: retorna um UUID-like gerado pelo Trello
        # não existe endpoint para schema; usamos o ID da lista como base
        version_id = f"schema-{data_source_id}"
        self._log(
            f"schema lógico atualizado para lista {data_source_id}: "
            f"{list(schema.keys())}"
        )
        return version_id

    def create_item(self, data_source_id: str, payload: Dict[str, Any]) -> str:
        """Cria um card na lista e retorna o ID do card."""
        params: Dict[str, Any] = {
            "idList": data_source_id or self._default_data_source_id,
            "name": payload.get("name", ""),
            "desc": payload.get("desc", ""),
            "due": payload.get("due", None),
            "start": payload.get("start", None),
            "pos": payload.get("pos", None),
        }
        # Campos opcionais reconhecidos pela API
        if "idMembers" in payload:
            params["idMembers"] = ",".join(payload["idMembers"])  # type: ignore[arg-type]
        if "idLabels" in payload:
            params["idLabels"] = ",".join(payload["idLabels"])  # type: ignore[arg-type]

        data = self._request("POST", "/cards", params=params)
        card_id = data.get("id", "")
        self._log(
            "card criado: lista={list_id} -> {card_id}",
            list_id=data_source_id,
            card_id=card_id,
        )

        # Define custom fields se fornecidos
        custom_fields = payload.get("custom_fields")
        if isinstance(custom_fields, dict):
            for cf_id, cf_value in custom_fields.items():
                self._set_custom_field(card_id, str(cf_id), cf_value)

        return card_id

    def update_item(
        self, data_source_id: str, item_id: str, payload: Dict[str, Any]
    ) -> str:
        """Atualiza um card existente e retorna o ID da operação."""
        params: Dict[str, Any] = {}
        # Mapeia campos padrão
        for key in (
            "name",
            "desc",
            "due",
            "start",
            "pos",
            "idList",
            "idBoard",
            "dueComplete",
        ):
            if key in payload:
                params[key] = payload[key]

        if "idMembers" in payload:
            params["idMembers"] = ",".join(payload["idMembers"])  # type: ignore[arg-type]
        if "idLabels" in payload:
            params["idLabels"] = ",".join(payload["idLabels"])  # type: ignore[arg-type]

        data = self._request("PUT", f"/cards/{item_id}", params=params)
        version_id = data.get("id", item_id)
        self._log(
            "card atualizado: lista={list_id} -> {card_id}",
            list_id=data_source_id,
            card_id=item_id,
        )

        custom_fields = payload.get("custom_fields")
        if isinstance(custom_fields, dict):
            for cf_id, cf_value in custom_fields.items():
                self._set_custom_field(item_id, str(cf_id), cf_value)

        return version_id

    def move_item(self, item_id: str, target_data_source_id: str) -> bool:
        """Move um card para outra lista.

        Args:
            item_id: ID do card.
            target_data_source_id: ID da lista de destino.

        Returns:
            bool: True se sucesso.
        """
        params: Dict[str, Any] = {"idList": target_data_source_id}
        self._request("PUT", f"/cards/{item_id}", params=params)
        self._log(
            "card movido: card={card} -> lista={list}",
            card=item_id,
            list=target_data_source_id,
        )
        return True

    def move_item_to_board(
        self, item_id: str, target_board_id: str, target_list_id: str
    ) -> bool:
        """Move um card para outro board e lista.

        Usa PUT /cards/{id}?idBoard={boardId}&idList={listId}
        Para movimentação entre boards diferentes.
        """
        params: Dict[str, Any] = {
            "idBoard": target_board_id,
            "idList": target_list_id,
        }
        data = self._request("PUT", f"/cards/{item_id}", params=params)
        self._log(
            "card movido entre boards: {card} -> board={board}, lista={list}",
            card=item_id,
            board=target_board_id,
            list=target_list_id,
        )
        return True

    # -------------------------- Membros (Boards/Cards) --------------------
    def invite_member_to_board(
        self, board_id: str, email: str, member_type: str = "normal"
    ) -> Dict[str, Any]:
        """Envia convite de membro por e-mail para um board do Trello.

        Comentário: usa PUT /boards/{id}/members com `email`.
        Alguns workspaces retornam um objeto de organização/board;
        capturamos o JSON como metadado e retornamos.
        """
        params: Dict[str, Any] = {"email": email, "type": member_type}
        data = self._request(
            "PUT", f"/boards/{board_id}/members", params=params
        )
        self._log(
            "convite enviado: board={board} email={email}",
            board=board_id,
            email=email,
        )
        return data if isinstance(data, dict) else {"status": "invited"}

    def get_board_members(self, board_id: str) -> List[Dict[str, Any]]:
        """Lista membros de um board do Trello (id, username, fullName)."""
        try:
            data = self._request("GET", f"/boards/{board_id}/members")
            if isinstance(data, list):
                return data
            return []
        except Exception:
            return []

    def add_member_to_card(self, card_id: str, member_id: str) -> bool:
        """Adiciona um membro a um card (POST /cards/{id}/idMembers)."""
        params: Dict[str, Any] = {"value": member_id}
        self._request("POST", f"/cards/{card_id}/idMembers", params=params)
        self._log(
            "membro adicionado ao card: card={card} member={member}",
            card=card_id,
            member=member_id,
        )
        return True

    def remove_member_from_card(self, card_id: str, member_id: str) -> bool:
        """Remove um membro de um card (DELETE /cards/{id}/idMembers/{mid}).

        Comentário: usa endpoint específico de remoção de membros do card.
        """
        self._request("DELETE", f"/cards/{card_id}/idMembers/{member_id}")
        self._log(
            "membro removido do card: card={card} member={member}",
            card=card_id,
            member=member_id,
        )
        return True

    def remove_member_from_board(self, board_id: str, member_id: str) -> bool:
        """Remove um membro de um board (DELETE /boards/{id}/members/{idMember}).

        Comentário: a API do Trello aceita remoção via path param
        `members/{idMember}`. Caso o membro não esteja no board, a
        API pode retornar erro; nesse caso propagamos exceção.
        """
        self._request("DELETE", f"/boards/{board_id}/members/{member_id}")
        self._log(
            "membro removido do board: board={board} member={member}",
            board=board_id,
            member=member_id,
        )
        return True

    def add_relation_property(
        self, data_source_id: str, property_name: str, target_id: str
    ) -> str:
        """Adiciona uma propriedade de relação como comentário no card.

        Comentário: Trello não tem relação nativa entre cards/listas.
        Como representação simples, adicionamos um comentário com a
        referência ao recurso alvo.
        """
        text = f"{property_name}: {target_id}"
        data = self._request(
            "POST",
            f"/cards/{data_source_id}/actions/comments",
            params={"text": text},
        )
        action_id = data.get("id", "")
        self._log(
            "comentário de relação criado: card={card} -> {action}",
            card=data_source_id,
            action=action_id,
        )
        return action_id

    def get_container(self, container_id: str) -> Optional[Dict[str, Any]]:
        """Obtém dados do board."""
        try:
            data = self._request("GET", f"/boards/{container_id}")
            return data
        except Exception:
            return None

    def get_data_source(self, data_source_id: str) -> Optional[Dict[str, Any]]:
        """Obtém dados da lista."""
        try:
            data = self._request("GET", f"/lists/{data_source_id}")
            return data
        except Exception:
            return None

    def get_item(
        self, data_source_id: str, item_id: str
    ) -> Optional[Dict[str, Any]]:
        """Obtém dados do card."""
        try:
            data = self._request("GET", f"/cards/{item_id}")
            return data
        except Exception:
            return None

    def append_block(self, container_id: str, block: Dict[str, Any]) -> str:
        """Cria um card de nota no primeiro `list` do board.

        Comentário: Trello não possui blocos de texto em board; usamos
        um card como bloco de nota.
        """
        lists: List[Dict[str, Any]] = self._request(
            "GET", f"/boards/{container_id}/lists"
        )
        list_id: Optional[str] = lists[0].get("id") if lists else None

        if list_id is None:
            # Se não houver listas, cria uma lista padrão
            list_id = self.add_data_source(container_id, "Notes")

        payload = {
            "name": block.get("title", "Note"),
            "desc": block.get("text", ""),
        }
        card_id = self.create_item(list_id, payload)
        self._log(
            "bloco anexado como card: board={board} -> {card}",
            board=container_id,
            card=card_id,
        )
        return card_id

    def list_items(self, data_source_id: str) -> List[Dict[str, Any]]:
        """Lista cards de uma lista do Trello."""
        try:
            data = self._request("GET", f"/lists/{data_source_id}/cards")
            if isinstance(data, list):
                return data
            return []
        except Exception:
            return []

    def list_data_sources(self, container_id: str) -> List[Dict[str, Any]]:
        """Lista listas de um board do Trello."""
        try:
            data = self._request("GET", f"/boards/{container_id}/lists")
            if isinstance(data, list):
                return data
            return []
        except Exception:
            return []

    def archive_container(self, container_id: str) -> bool:
        """Arquiva um board no Trello (fecha o quadro)."""
        params: Dict[str, Any] = {"value": True}
        data = self._request(
            "PUT", f"/boards/{container_id}/closed", params=params
        )
        self._log(
            "board arquivado: {board}",
            board=data.get("id", container_id),
        )
        return True

    def archive_data_source(self, data_source_id: str) -> bool:
        """Arquiva uma lista no Trello (fecha a lista)."""
        params: Dict[str, Any] = {"value": True}
        data = self._request(
            "PUT", f"/lists/{data_source_id}/closed", params=params
        )
        self._log(
            "lista arquivada: {list}",
            list=data.get("id", data_source_id),
        )
        return True

    def archive_item(self, item_id: str) -> bool:
        """Arquiva um card no Trello (fecha o card).

        Comentário: utiliza endpoint específico de fechamento do card
        `PUT /cards/{id}/closed?value=true`. Retorna verdadeiro em caso
        de sucesso.
        """
        params: Dict[str, Any] = {"value": True}
        data = self._request("PUT", f"/cards/{item_id}/closed", params=params)
        self._log("card arquivado: {card}", card=data.get("id", item_id))
        return True

    # -------------------------- Métodos auxiliares ------------------------
    def _set_custom_field(self, card_id: str, cf_id: str, value: Any) -> None:
        """Define valor de custom field em um card.

        Comentário: requer que o custom field exista no board e que o
        token possua escopo para escrever em custom fields.
        """
        # Estrutura do valor no Trello varia por tipo; usamos `text`
        json_body: Dict[str, Any] = {"value": {"text": str(value)}}
        try:
            self._request(
                "PUT",
                f"/cards/{card_id}/customField/{cf_id}/item",
                json=json_body,
            )
        except Exception as exc:
            # Silencia erro de custom field inexistente para robustez
            logger.warning(
                "Falha ao definir custom field {cf} em card {card}: {err}",
                cf=cf_id,
                card=card_id,
                err=str(exc),
            )

    # -------------------------- Extensões de contrato ---------------------
    def ensure_custom_fields(
        self, board_id: str, fields: Dict[str, str]
    ) -> Dict[str, str]:
        """Obtém IDs de custom fields do board por nome.

        Comentário: criação de custom fields via API requer Power-Up.
        Esta implementação apenas retorna existentes e loga ausência.
        """
        mapping: Dict[str, str] = {}
        try:
            existing: List[Dict[str, Any]] = self._request(
                "GET", f"/boards/{board_id}/customFields"
            )
        except Exception as exc:
            logger.warning(
                "Não foi possível listar custom fields do board {board}: {err}",
                board=board_id,
                err=str(exc),
            )
            existing = []

        by_name: Dict[str, str] = {
            str(cf.get("name", "")): str(cf.get("id", "")) for cf in existing
        }
        for name in fields.keys():
            cf_id = by_name.get(name)
            if cf_id:
                mapping[name] = cf_id
            else:
                logger.info(
                    "Custom field ausente no board {board}: {name}",
                    board=board_id,
                    name=name,
                )
        return mapping

    def ensure_labels(
        self, board_id: str, labels: Dict[str, str]
    ) -> Dict[str, str]:
        """Garante que labels existam no board e retorna seus IDs.

        Comentário: tenta criar labels ausentes com cor informada.
        Trello suporta cores como 'red', 'orange', 'yellow', 'green',
        'blue', 'purple', 'pink', 'sky', 'lime', 'black' e 'null'.
        """
        mapping: Dict[str, str] = {}
        try:
            existing: List[Dict[str, Any]] = self._request(
                "GET", f"/boards/{board_id}/labels"
            )
        except Exception as exc:
            logger.warning(
                "Não foi possível listar labels do board {board}: {err}",
                board=board_id,
                err=str(exc),
            )
            existing = []

        by_name: Dict[str, str] = {
            str(lb.get("name", "")): str(lb.get("id", "")) for lb in existing
        }

        for name, color in labels.items():
            lb_id = by_name.get(name)
            if lb_id:
                mapping[name] = lb_id
                continue

            try:
                created = self._request(
                    "POST",
                    "/labels",
                    params={
                        "name": name,
                        "color": color,
                        "idBoard": board_id,
                    },
                )
                mapping[name] = str(created.get("id", ""))
                self._log(
                    "label criada: {name} ({color}) -> {id}",
                    name=name,
                    color=color,
                    id=mapping[name],
                )
            except Exception as exc:
                logger.info(
                    "Label ausente e não criada no board {board}: {name} "
                    "({color}) erro: {err}",
                    board=board_id,
                    name=name,
                    color=color,
                    err=str(exc),
                )

        return mapping

    def set_card_cover_color(
        self,
        card_id: str,
        color: str,
        brightness: Optional[str] = None,
        size: Optional[str] = None,
    ) -> bool:
        """Define a capa (cover) do card com uma cor sólida.

        Comentário: Trello aceita atualização de `cover` via
        ``PUT /cards/{id}`` passando um objeto `cover` no corpo JSON
        (documentado pela Atlassian). As cores válidas incluem
        'red', 'orange', 'yellow', 'green', 'blue', 'purple',
        'pink', 'sky', 'lime', 'black' e 'null'.

        Args:
            card_id: ID do card no Trello.
            color: Cor suportada pelo Trello.
            brightness: Opcional, 'light' ou 'dark'.
            size: Opcional, 'normal' ou 'full'.

        Returns:
            bool: ``True`` em caso de sucesso.
        """
        # Comentário: alguns workspaces não aplicam alterações via
        # endpoint ``/cards/{id}/cover``. Para máxima compatibilidade
        # usamos ``PUT /cards/{id}`` com objeto `cover`.
        cover_body: Dict[str, Any] = {"color": color}
        # Define padrões sensatos para visibilidade da capa
        cover_body["brightness"] = brightness or "light"
        if size is not None:
            cover_body["size"] = size

        data = self._request(
            "PUT",
            f"/cards/{card_id}",
            json={"cover": cover_body},
        )
        self._log(
            "capa do card atualizada: card={card} color={color}",
            card=data.get("id", card_id),
            color=color,
        )
        return True

    def register_webhook(
        self, model_id: str, callback_url: str, description: str
    ) -> str:
        """Registra webhook no Trello para um `model` (board/list/card).

        Returns:
            str: ID do webhook criado.
        """
        params = {
            "description": description,
            "callbackURL": callback_url,
            "idModel": model_id,
        }
        data = self._request("POST", "/webhooks", params=params)
        webhook_id = data.get("id", "")
        self._log(
            "webhook registrado: model={model} -> {webhook}",
            model=model_id,
            webhook=webhook_id,
        )
        return webhook_id

    def delete_webhook(self, webhook_id: str) -> bool:
        """Remove um webhook existente.

        Returns:
            bool: `True` se removido com sucesso.
        """
        self._request("DELETE", f"/webhooks/{webhook_id}")
        self._log(f"webhook removido: {webhook_id}")
        return True

    def search_items(
        self, board_id: str, query: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Busca cards via API do Trello.

        Comentário: usa endpoint de busca global do Trello. Para escopar
        ao board, concatenamos `idBoards`.
        """
        params: Dict[str, Any] = {
            "query": query.get("query", ""),
            "idBoards": board_id,
            "modelTypes": "cards",
            "card_board": True,
            "partial": True,
        }
        data = self._request("GET", "/search", params=params)
        cards = data.get("cards", [])
        if not isinstance(cards, list):
            return []
        return cards
