
import unittest
from unittest.mock import MagicMock, patch

from smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter import (
    TrelloUnifiedDataService,
)
from smart_core_assistant_painel.modules.services.utils.erros import (
    UnifieldDataServicesError,
)
from smart_core_assistant_painel.modules.services.utils.parameters import (
    UnifieldDataServicesParameters,
)


class TestTrelloUnifiedDataService(unittest.TestCase):
    def setUp(self):
        self.params = UnifieldDataServicesParameters(
            data_source_id="default_list",
            error=UnifieldDataServicesError("Test Error"),
            enable_observability=True,
        )

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_init_success(self, mock_config):
        mock_config.side_effect = lambda key, default="": "test_val"
        service = TrelloUnifiedDataService(self.params)
        self.assertEqual(service._api_key, "test_val")
        self.assertEqual(service._token, "test_val")

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_init_missing_credentials(self, mock_config):
        mock_config.return_value = ""
        with self.assertRaises(ValueError):
            TrelloUnifiedDataService(self.params)

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_request_methods(self, mock_config, mock_requests):
        mock_config.return_value = "val"
        service = TrelloUnifiedDataService(self.params)

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"key": "val"}
        mock_requests.get.return_value = mock_resp

        # Test GET
        res = service._request("GET", "/path", params={"q": 1})
        mock_requests.get.assert_called()
        args, kwargs = mock_requests.get.call_args
        self.assertIn("key", kwargs["params"])
        self.assertIn("token", kwargs["params"])
        self.assertEqual(kwargs["params"]["q"], 1)
        self.assertEqual(res, {"key": "val"})

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_normalize_query_params(self, mock_config, mock_requests):
        mock_config.return_value = "val"
        service = TrelloUnifiedDataService(self.params)

        res = service._normalize_query_params({"a": True, "b": False, "c": None, "d": 1})
        self.assertEqual(res, {"a": "true", "b": "false", "d": 1})

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_create_container(self, mock_config, mock_requests):
        mock_config.return_value = "val"
        service = TrelloUnifiedDataService(self.params)

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"id": "board1"}
        mock_requests.post.return_value = mock_resp

        res = service.create_container("My Board")
        self.assertEqual(res, "board1")
        mock_requests.post.assert_called()

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_add_data_source(self, mock_config, mock_requests):
        mock_config.return_value = "val"
        service = TrelloUnifiedDataService(self.params)

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"id": "list1"}
        mock_requests.post.return_value = mock_resp

        res = service.add_data_source("board1", "My List")
        self.assertEqual(res, "list1")

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_create_item(self, mock_config, mock_requests):
        mock_config.return_value = "val"
        service = TrelloUnifiedDataService(self.params)

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"id": "card1"}
        mock_requests.post.return_value = mock_resp

        payload = {"name": "Card", "desc": "Desc", "idMembers": ["m1"], "custom_fields": {"cf1": "val1"}}
        # Need to mock _set_custom_field logic or verify call order if it's mocked out?
        # It calls _request internally for custom fields.

        # To test _set_custom_field calls, we can mock _request but create_item calls _request too.

        res = service.create_item("list1", payload)
        self.assertEqual(res, "card1")
        self.assertEqual(mock_requests.post.call_count, 1) # create card
        self.assertEqual(mock_requests.put.call_count, 1) # set custom field

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_invite_member_to_board(self, mock_config, mock_requests):
        mock_config.return_value = "val"
        service = TrelloUnifiedDataService(self.params)

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"id": "mem1"}
        mock_requests.put.return_value = mock_resp

        res = service.invite_member_to_board("board1", "email@test.com")
        self.assertEqual(res["id"], "mem1")

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_archive_item(self, mock_config, mock_requests):
        mock_config.return_value = "val"
        service = TrelloUnifiedDataService(self.params)

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"id": "card1", "closed": True}
        mock_requests.put.return_value = mock_resp

        res = service.archive_item("card1")
        self.assertTrue(res)
        mock_requests.put.assert_called()
        args, kwargs = mock_requests.put.call_args
        self.assertIn("/cards/card1/closed", args[0])
        self.assertEqual(kwargs["params"]["value"], "true") # normalized
