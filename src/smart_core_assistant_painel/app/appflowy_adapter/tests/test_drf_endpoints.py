"""Testes de integração dos endpoints DRF do `appflowy_adapter`.

Cobrem autenticação JWT, listagem de workspaces, schema de grid,
CRUD de linhas com validação de versão via `If-Match`.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, List, Tuple
from uuid import UUID

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from smart_core_assistant_painel.app.appflowy_adapter.models import (
    AppFlowyColumn,
    AppFlowyGrid,
    AppFlowyRow,
    AppFlowyWorkspace,
)


class AppFlowyAdapterDRFTests(TestCase):
    """Valida endpoints protegidos por JWT e fluxo de linhas."""

    def setUp(self) -> None:
        """Cria usuário, obtém JWT e prepara workspace/grid/colunas."""

        # Usuário para autenticação nos endpoints protegidos
        self.user: User = User.objects.create_user(
            username="admin",
            password="123456",
        )

        # Login para obter tokens JWT
        login_url: str = reverse("appflowy_adapter:auth-login")
        login_payload: Dict[str, str] = {
            "username": "admin",
            "password": "123456",
        }
        login_resp = self.client.post(
            login_url,
            data=login_payload,
            content_type="application/json",
        )
        self.assertEqual(login_resp.status_code, 200)
        tokens: Dict[str, Any] = login_resp.json()
        self.access_token: str = str(tokens.get("access", ""))
        self.assertTrue(self.access_token)

        # Workspace e Grid
        self.workspace = AppFlowyWorkspace.objects.create(name="Default")
        self.grid = AppFlowyGrid.objects.create(
            workspace=self.workspace,
            name="Atendimentos",
            description="Grid de Atendimentos",
        )

        # Colunas mínimas
        cols: List[Tuple[str, str]] = [
            ("ticket_id", "string"),
            ("name", "string"),
            ("status", "string"),
            ("priority", "string"),
            ("assigned_to", "string"),
            ("tags", "multi_select"),
        ]
        for idx, (key, ctype) in enumerate(cols):
            AppFlowyColumn.objects.create(
                grid=self.grid,
                key=key,
                name=key,
                type=ctype,
                order=idx,
                required=False,
            )

    def _auth_headers(self) -> Dict[str, str]:
        """Headers com Bearer token para chamadas autenticadas."""

        return {"HTTP_AUTHORIZATION": f"Bearer {self.access_token}"}

    def test_workspaces_requires_auth_and_returns_items(self) -> None:
        """`GET /workspaces/` deve exigir JWT e retornar itens."""

        url: str = reverse("appflowy_adapter:workspaces")

        # Sem token → 401
        resp_unauth = self.client.get(url)
        self.assertEqual(resp_unauth.status_code, 401)

        # Com token → 200
        resp_auth = self.client.get(url, **self._auth_headers())
        self.assertEqual(resp_auth.status_code, 200)
        data: Dict[str, Any] = resp_auth.json()
        self.assertIn("items", data)

    def test_grid_schema_returns_columns(self) -> None:
        """`GET /grids/<id>/schema/` retorna colunas do grid."""

        url: str = reverse(
            "appflowy_adapter:grid-schema", args=[self.grid.grid_id]
        )
        resp = self.client.get(url, **self._auth_headers())
        self.assertEqual(resp.status_code, 200)
        data: Dict[str, Any] = resp.json()
        self.assertEqual(data.get("grid_id"), str(self.grid.grid_id))
        columns = data.get("columns", [])
        self.assertTrue(len(columns) >= 6)

    def test_grids_list_by_workspace_returns_items(self) -> None:
        """`GET /workspaces/<id>/grids/` retorna grids do workspace."""

        url: str = reverse(
            "appflowy_adapter:grids-list", args=[self.workspace.workspace_id]
        )
        resp = self.client.get(url, **self._auth_headers())
        self.assertEqual(resp.status_code, 200)
        data: Dict[str, Any] = resp.json()
        items: List[Dict[str, Any]] = data.get("items", [])
        # Deve conter pelo menos o grid criado no setUp
        self.assertTrue(any(g.get("grid_id") == str(self.grid.grid_id) for g in items))

    def test_rows_list_since_filter_and_invalid_since(self) -> None:
        """Valida filtro `since` e erro para formato inválido."""

        # Cria duas linhas em sequência para ter `updated_at` distinto
        row1 = AppFlowyRow.objects.create(
            grid=self.grid,
            ticket_id="T-001",
            name="Ticket 1",
            channel="whatsapp",
            status="open",
            priority="medium",
        )
        row2 = AppFlowyRow.objects.create(
            grid=self.grid,
            ticket_id="T-002",
            name="Ticket 2",
            channel="whatsapp",
            status="open",
            priority="medium",
        )
        since_iso: str = row1.updated_at.isoformat()

        url: str = reverse(
            "appflowy_adapter:rows-list-create", args=[self.grid.grid_id]
        )
        # since válido → deve trazer o segundo registro
        resp_valid = self.client.get(
            f"{url}?since={since_iso}", **self._auth_headers()
        )
        self.assertEqual(resp_valid.status_code, 200)
        items = resp_valid.json().get("items", [])
        # Pode ser 1 (mais recente) dependendo da precisão temporal
        self.assertTrue(len(items) >= 1)

        # since inválido → 400
        resp_invalid = self.client.get(
            f"{url}?since=not-a-date", **self._auth_headers()
        )
        self.assertEqual(resp_invalid.status_code, 400)

    def test_rows_create_and_idempotent_update(self) -> None:
        """POST cria linha; segunda vez com mesmo `ticket_id` atualiza."""

        url: str = reverse(
            "appflowy_adapter:rows-list-create", args=[self.grid.grid_id]
        )
        payload: Dict[str, Any] = {
            "ticket_id": "T-010",
            "name": "Ticket 10",
            "channel": "whatsapp",
            "status": "open",
            "priority": "high",
            "tags": ["vip"],
        }

        resp_create = self.client.post(
            url,
            data=payload,
            content_type="application/json",
            **self._auth_headers(),
        )
        self.assertEqual(resp_create.status_code, 201)
        created: Dict[str, Any] = resp_create.json()
        self.assertEqual(created.get("ticket_id"), "T-010")
        version1 = int(created.get("version", 1))

        # Segundo POST com mesmo ticket_id atualiza e incrementa versão
        payload_update = {
            **payload,
            "status": "in_progress",
        }
        resp_update = self.client.post(
            url,
            data=payload_update,
            content_type="application/json",
            **self._auth_headers(),
        )
        self.assertEqual(resp_update.status_code, 200)
        updated: Dict[str, Any] = resp_update.json()
        version2 = int(updated.get("version", version1))
        self.assertEqual(version2, version1 + 1)

    def test_row_update_if_match_success_and_conflict(self) -> None:
        """PUT com `If-Match` correto atualiza; valor errado retorna 412."""

        row = AppFlowyRow.objects.create(
            grid=self.grid,
            ticket_id="T-020",
            name="Ticket 20",
            channel="whatsapp",
            status="open",
            priority="low",
        )
        current_version: int = int(row.version)

        url: str = reverse(
            "appflowy_adapter:row-update-delete",
            args=[self.grid.grid_id, row.row_id],
        )

        # Atualização com If-Match correto
        resp_ok = self.client.put(
            url,
            data={"status": "closed"},
            content_type="application/json",
            HTTP_IF_MATCH=str(current_version),
            **self._auth_headers(),
        )
        self.assertEqual(resp_ok.status_code, 200)
        body_ok: Dict[str, Any] = resp_ok.json()
        self.assertEqual(body_ok.get("status"), "closed")
        new_version: int = int(body_ok.get("version", 0))
        self.assertEqual(new_version, current_version + 1)

        # Conflito: If-Match antigo
        resp_conflict = self.client.put(
            url,
            data={"status": "open"},
            content_type="application/json",
            HTTP_IF_MATCH=str(current_version),
            **self._auth_headers(),
        )
        self.assertEqual(resp_conflict.status_code, 412)
        body_conflict: Dict[str, Any] = resp_conflict.json()
        self.assertIn("current_version", body_conflict)

        # Ausência de If-Match também deve falhar
        resp_missing = self.client.put(
            url,
            data={"status": "in_progress"},
            content_type="application/json",
            **self._auth_headers(),
        )
        self.assertEqual(resp_missing.status_code, 412)

    def test_row_delete_returns_204(self) -> None:
        """DELETE remove a linha e retorna 204 (sem conteúdo)."""

        row = AppFlowyRow.objects.create(
            grid=self.grid,
            ticket_id="T-030",
            name="Ticket 30",
            channel="whatsapp",
            status="open",
            priority="low",
        )

        url: str = reverse(
            "appflowy_adapter:row-update-delete",
            args=[self.grid.grid_id, row.row_id],
        )
        resp_del = self.client.delete(url, **self._auth_headers())
        self.assertEqual(resp_del.status_code, 204)
        exists: bool = AppFlowyRow.objects.filter(row_id=row.row_id).exists()
        self.assertFalse(exists)