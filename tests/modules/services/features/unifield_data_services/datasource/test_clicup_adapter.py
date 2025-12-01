
import unittest
from unittest.mock import MagicMock, patch

from smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter import (
    ClicupUnifiedDataService,
)
from smart_core_assistant_painel.modules.services.utils.erros import (
    UnifieldDataServicesError,
)
from smart_core_assistant_painel.modules.services.utils.parameters import (
    UnifieldDataServicesParameters,
)


class TestClicupUnifiedDataService(unittest.TestCase):
    def setUp(self):
        self.params = UnifieldDataServicesParameters(
            data_source_id="default_list",
            error=UnifieldDataServicesError("Test Error"),
            enable_observability=True,
        )

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.config")
    def test_init_success(self, mock_config):
        mock_config.return_value = "test_token"
        service = ClicupUnifiedDataService(self.params)
        self.assertEqual(service._headers["Authorization"], "Bearer test_token")

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.config")
    def test_init_missing_token(self, mock_config):
        mock_config.return_value = ""
        with self.assertRaises(ValueError):
            ClicupUnifiedDataService(self.params)

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.config")
    def test_request_methods(self, mock_config, mock_requests):
        mock_config.return_value = "token"
        service = ClicupUnifiedDataService(self.params)

        # Mock response
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"key": "val"}
        mock_resp.content = b"content"
        mock_requests.get.return_value = mock_resp
        mock_requests.post.return_value = mock_resp
        mock_requests.put.return_value = mock_resp
        mock_requests.delete.return_value = mock_resp

        # Test GET
        res = service._request("GET", "/path")
        mock_requests.get.assert_called_with(
            "https://api.clickup.com/api/v2/path",
            headers={"Authorization": "Bearer token"},
            params=None,
            json=None,
            timeout=30
        )
        self.assertEqual(res, {"key": "val"})

        # Test POST
        service._request("POST", "/path", json={"a": 1})
        mock_requests.post.assert_called_with(
            "https://api.clickup.com/api/v2/path",
            headers={"Authorization": "Bearer token"},
            params=None,
            json={"a": 1},
            timeout=30
        )

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.config")
    def test_get_team_id(self, mock_config, mock_requests):
        # Case 1: Configured in env
        mock_config.side_effect = lambda key, default="": "team_env" if key == "CLICKUP_TEAM_ID" else "token"
        service = ClicupUnifiedDataService(self.params)
        self.assertEqual(service._get_team_id(), "team_env")

        # Case 2: Fetch from API
        mock_config.side_effect = lambda key, default="": "" if key == "CLICKUP_TEAM_ID" else "token"
        service = ClicupUnifiedDataService(self.params)

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.content = b"ok"
        mock_resp.json.return_value = {"teams": [{"id": "team_api"}]}
        mock_requests.get.return_value = mock_resp

        self.assertEqual(service._get_team_id(), "team_api")

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.config")
    def test_create_container(self, mock_config, mock_requests):
        mock_config.return_value = "token"
        service = ClicupUnifiedDataService(self.params)
        service._team_id = "team1"

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.content = b"ok"
        mock_resp.json.return_value = {"id": "space1"}
        mock_requests.post.return_value = mock_resp

        res = service.create_container("My Space")
        self.assertEqual(res, "space1")
        mock_requests.post.assert_called()

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.config")
    def test_add_data_source(self, mock_config, mock_requests):
        mock_config.return_value = "token"
        service = ClicupUnifiedDataService(self.params)

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.content = b"ok"
        mock_resp.json.return_value = {"id": "list1"}
        mock_requests.post.return_value = mock_resp

        res = service.add_data_source("space1", "My List")
        self.assertEqual(res, "list1")

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.config")
    def test_create_item(self, mock_config, mock_requests):
        mock_config.return_value = "token"
        service = ClicupUnifiedDataService(self.params)

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.content = b"ok"
        mock_resp.json.return_value = {"id": "task1"}
        mock_requests.post.return_value = mock_resp

        res = service.create_item("list1", {"name": "Task Name", "description": "Desc"})
        self.assertEqual(res, "task1")
        # Verify normalization
        args, kwargs = mock_requests.post.call_args
        self.assertEqual(kwargs['json']['name'], "Task Name")

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.config")
    def test_set_task_assignees_post_success(self, mock_config, mock_requests):
        mock_config.return_value = "token"
        service = ClicupUnifiedDataService(self.params)

        # Mock get_task_details (current assignees)
        mock_resp_get = MagicMock()
        mock_resp_get.ok = True
        mock_resp_get.content = b"ok"
        mock_resp_get.json.return_value = {"assignees": [{"id": "user1"}]}
        mock_requests.get.return_value = mock_resp_get

        # Mock post (add/remove)
        mock_resp_post = MagicMock()
        mock_resp_post.ok = True
        mock_resp_post.content = b"ok"
        mock_requests.post.return_value = mock_resp_post

        # Target: user2 (add user2, remove user1)
        # First GET (initial) -> user1
        # POST add user2
        # POST remove user1
        # Second GET (verification) -> user2

        mock_resp_verify = MagicMock()
        mock_resp_verify.ok = True
        mock_resp_verify.content = b"ok"
        mock_resp_verify.json.return_value = {"assignees": [{"id": "user2"}]}

        # Use side_effect for get: first call return initial, second return verify
        mock_requests.get.side_effect = [mock_resp_get, mock_resp_verify]

        success = service.set_task_assignees("task1", ["user2"])
        self.assertTrue(success)
        self.assertEqual(mock_requests.post.call_count, 2) # Add and Remove

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.config")
    def test_upload_attachment(self, mock_config, mock_requests):
        mock_config.return_value = "token"
        service = ClicupUnifiedDataService(self.params)

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.content = b"ok"
        mock_resp.json.return_value = {"id": "att1"}
        mock_requests.post.return_value = mock_resp

        res = service.upload_attachment("task1", "file.txt", b"content")
        self.assertEqual(res, "att1")
        mock_requests.post.assert_called()
        args, kwargs = mock_requests.post.call_args
        self.assertIn("files", kwargs)

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.config")
    def test_list_spaces(self, mock_config, mock_requests):
        mock_config.return_value = "token"
        service = ClicupUnifiedDataService(self.params)
        service._team_id = "team1"

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"spaces": [{"id": "s1"}]}
        mock_requests.get.return_value = mock_resp

        res = service.list_spaces()
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["id"], "s1")

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.config")
    def test_delete_item_success(self, mock_config, mock_requests):
        mock_config.return_value = "token"
        service = ClicupUnifiedDataService(self.params)
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_requests.delete.return_value = mock_resp

        self.assertTrue(service.delete_item("task1"))

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.config")
    def test_delete_item_failure(self, mock_config, mock_requests):
        mock_config.return_value = "token"
        service = ClicupUnifiedDataService(self.params)
        mock_requests.delete.side_effect = Exception("Error")

        self.assertFalse(service.delete_item("task1"))

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.config")
    def test_ensure_space_by_name_exists(self, mock_config, mock_requests):
        mock_config.return_value = "token"
        service = ClicupUnifiedDataService(self.params)
        service._team_id = "team1"

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"spaces": [{"id": "s1", "name": "Existing Space"}]}
        mock_requests.get.return_value = mock_resp

        res = service.ensure_space_by_name("Existing Space")
        self.assertEqual(res, "s1")
        # Should NOT call create (POST)
        mock_requests.post.assert_not_called()

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.config")
    def test_ensure_space_by_name_create(self, mock_config, mock_requests):
        mock_config.return_value = "token"
        service = ClicupUnifiedDataService(self.params)
        service._team_id = "team1"

        # List spaces returns empty or different names
        mock_resp_list = MagicMock()
        mock_resp_list.ok = True
        mock_resp_list.json.return_value = {"spaces": []}

        # Create space returns id
        mock_resp_create = MagicMock()
        mock_resp_create.ok = True
        mock_resp_create.content = b"ok"
        mock_resp_create.json.return_value = {"id": "s2"}

        mock_requests.get.return_value = mock_resp_list
        mock_requests.post.return_value = mock_resp_create

        res = service.ensure_space_by_name("New Space")
        self.assertEqual(res, "s2")
        mock_requests.post.assert_called()

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.config")
    def test_folders_operations(self, mock_config, mock_requests):
        mock_config.return_value = "token"
        service = ClicupUnifiedDataService(self.params)

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"folders": [{"id": "f1", "name": "Folder1"}], "id": "f2"}
        mock_resp.content = b"ok"
        mock_requests.get.return_value = mock_resp
        mock_requests.post.return_value = mock_resp
        mock_requests.delete.return_value = mock_resp

        self.assertEqual(len(service.list_folders("s1")), 1)
        self.assertEqual(service.find_folder_by_name("s1", "Folder1")["id"], "f1")
        self.assertEqual(service.create_folder("s1", "Folder2"), "f2")
        self.assertTrue(service.delete_folder("f1"))

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.config")
    def test_list_operations(self, mock_config, mock_requests):
        mock_config.return_value = "token"
        service = ClicupUnifiedDataService(self.params)

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"lists": [{"id": "l1", "name": "List1"}], "id": "l2"}
        mock_resp.content = b"ok"
        mock_requests.get.return_value = mock_resp
        mock_requests.post.return_value = mock_resp
        mock_requests.delete.return_value = mock_resp

        self.assertEqual(service.add_list_to_folder("f1", "L2"), "l2")
        self.assertEqual(len(service.list_folder_lists("f1")), 1)
        self.assertEqual(service.find_list_in_folder_by_name("f1", "List1")["id"], "l1")
        self.assertTrue(service.delete_list("l1"))

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.config")
    def test_members_operations(self, mock_config, mock_requests):
        mock_config.return_value = "token"
        service = ClicupUnifiedDataService(self.params)
        service._team_id = "t1"

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"members": [{"user": {"id": "m1", "email": "e@e.com"}}]}
        mock_requests.get.return_value = mock_resp
        mock_requests.delete.return_value = mock_resp

        self.assertTrue(service.remove_member("m1"))
        self.assertEqual(len(service.list_team_members()), 1)
        self.assertEqual(len(service.list_list_members("l1")), 1)
        self.assertIsNotNone(service.find_member_by_email("e@e.com"))

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.config")
    def test_custom_fields(self, mock_config, mock_requests):
        mock_config.return_value = "token"
        service = ClicupUnifiedDataService(self.params)

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"fields": [{"id": "cf1"}]}
        mock_requests.get.return_value = mock_resp
        mock_requests.post.return_value = mock_resp

        self.assertEqual(len(service.get_list_custom_fields("l1")), 1)
        self.assertTrue(service.set_task_custom_field("t1", "cf1", "val"))

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.config")
    def test_misc_methods(self, mock_config, mock_requests):
        mock_config.return_value = "token"
        service = ClicupUnifiedDataService(self.params)
        service._team_id = "t1"

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"id": "1", "lists": [{"id": "l1"}]}
        mock_resp.content = b"ok"
        mock_requests.get.return_value = mock_resp
        mock_requests.post.return_value = mock_resp
        mock_requests.put.return_value = mock_resp

        self.assertEqual(service.update_schema("l1", {}), "schema-l1")
        self.assertEqual(service.update_item("l1", "t1", {}), "1")
        self.assertIsNotNone(service.add_relation_property("t1", "rel", "id"))
        self.assertIsNotNone(service.add_comment("t1", "msg"))
        self.assertIsNotNone(service.get_container("s1"))
        self.assertIsNotNone(service.get_data_source("l1"))
        self.assertIsNotNone(service.get_item("l1", "t1"))
        self.assertIsNotNone(service.append_block("s1", {}))
        self.assertEqual(len(service.list_items("l1")), 0) # mocked response structure might not match tasks list perfectly if reused
        self.assertEqual(len(service.list_data_sources("s1")), 1)

        with self.assertRaises(NotImplementedError):
            service.set_data_source_position("l1", 1)
