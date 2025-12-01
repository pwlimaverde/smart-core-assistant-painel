
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

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_set_data_source_position(self, mock_config, mock_requests):
        mock_config.return_value = "val"
        service = TrelloUnifiedDataService(self.params)
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"id": "list1", "pos": 2.5}
        mock_requests.put.return_value = mock_resp

        self.assertTrue(service.set_data_source_position("list1", 2.5))
        mock_requests.put.assert_called()

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_update_schema(self, mock_config, mock_requests):
        mock_config.return_value = "val"
        service = TrelloUnifiedDataService(self.params)

        version = service.update_schema("list1", {"field": "type"})
        self.assertEqual(version, "schema-list1")

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_update_item(self, mock_config, mock_requests):
        mock_config.return_value = "val"
        service = TrelloUnifiedDataService(self.params)
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"id": "card1"}
        mock_requests.put.return_value = mock_resp

        payload = {"name": "New Name", "custom_fields": {"cf1": "v1"}}
        res = service.update_item("list1", "card1", payload)
        self.assertEqual(res, "card1")
        # Should call put for card update and put for custom field
        self.assertEqual(mock_requests.put.call_count, 2)

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_get_board_members(self, mock_config, mock_requests):
        mock_config.return_value = "val"
        service = TrelloUnifiedDataService(self.params)
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = [{"id": "m1"}]
        mock_requests.get.return_value = mock_resp

        res = service.get_board_members("board1")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["id"], "m1")

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_add_remove_member_card(self, mock_config, mock_requests):
        mock_config.return_value = "val"
        service = TrelloUnifiedDataService(self.params)
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {}
        mock_requests.post.return_value = mock_resp
        mock_requests.delete.return_value = mock_resp

        self.assertTrue(service.add_member_to_card("card1", "m1"))
        mock_requests.post.assert_called()

        self.assertTrue(service.remove_member_from_card("card1", "m1"))
        mock_requests.delete.assert_called()

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_remove_member_from_board(self, mock_config, mock_requests):
        mock_config.return_value = "val"
        service = TrelloUnifiedDataService(self.params)
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_requests.delete.return_value = mock_resp

        self.assertTrue(service.remove_member_from_board("board1", "m1"))
        mock_requests.delete.assert_called()

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_add_relation_property(self, mock_config, mock_requests):
        mock_config.return_value = "val"
        service = TrelloUnifiedDataService(self.params)
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"id": "action1"}
        mock_requests.post.return_value = mock_resp

        res = service.add_relation_property("card1", "Rel", "Target")
        self.assertEqual(res, "action1")

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_get_methods(self, mock_config, mock_requests):
        mock_config.return_value = "val"
        service = TrelloUnifiedDataService(self.params)
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"id": "obj1"}
        mock_requests.get.return_value = mock_resp

        self.assertEqual(service.get_container("b1")["id"], "obj1")
        self.assertEqual(service.get_data_source("l1")["id"], "obj1")
        self.assertEqual(service.get_item("l1", "c1")["id"], "obj1")

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_append_block(self, mock_config, mock_requests):
        mock_config.return_value = "val"
        service = TrelloUnifiedDataService(self.params)

        # Mock list lists
        mock_resp_list = MagicMock()
        mock_resp_list.ok = True
        mock_resp_list.json.return_value = [{"id": "list1"}]

        # Mock create card
        mock_resp_card = MagicMock()
        mock_resp_card.ok = True
        mock_resp_card.json.return_value = {"id": "card1"}

        mock_requests.get.return_value = mock_resp_list
        mock_requests.post.return_value = mock_resp_card

        res = service.append_block("board1", {"title": "T", "text": "Txt"})
        self.assertEqual(res, "card1")

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_append_block_no_lists(self, mock_config, mock_requests):
        mock_config.return_value = "val"
        service = TrelloUnifiedDataService(self.params)

        # Mock list lists returns empty
        mock_resp_list = MagicMock()
        mock_resp_list.ok = True
        mock_resp_list.json.return_value = []

        # Mock create list
        mock_resp_create_list = MagicMock()
        mock_resp_create_list.ok = True
        mock_resp_create_list.json.return_value = {"id": "new_list"}

        # Mock create card
        mock_resp_card = MagicMock()
        mock_resp_card.ok = True
        mock_resp_card.json.return_value = {"id": "card1"}

        # Configure side_effect for request methods
        # GET lists -> empty
        # POST list -> new_list
        # POST card -> card1

        # It's easier to mock _request if needed, but here we mock requests directly
        # Calls:
        # 1. GET /boards/container_id/lists
        # 2. POST /lists (add_data_source)
        # 3. POST /cards (create_item)

        # We need side_effects on requests methods
        mock_requests.get.return_value = mock_resp_list

        def post_side_effect(url, **kwargs):
            if "/lists" in url:
                return mock_resp_create_list
            if "/cards" in url:
                return mock_resp_card
            return MagicMock(ok=True, json=lambda: {})

        mock_requests.post.side_effect = post_side_effect

        res = service.append_block("board1", {"title": "T"})
        self.assertEqual(res, "card1")

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_list_items_and_datasources(self, mock_config, mock_requests):
        mock_config.return_value = "val"
        service = TrelloUnifiedDataService(self.params)
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = [{"id": "1"}]
        mock_requests.get.return_value = mock_resp

        self.assertEqual(len(service.list_items("l1")), 1)
        self.assertEqual(len(service.list_data_sources("b1")), 1)

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_archive_container_datasource(self, mock_config, mock_requests):
        mock_config.return_value = "val"
        service = TrelloUnifiedDataService(self.params)
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"id": "1"}
        mock_requests.put.return_value = mock_resp

        self.assertTrue(service.archive_container("b1"))
        self.assertTrue(service.archive_data_source("l1"))

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_ensure_custom_fields(self, mock_config, mock_requests):
        mock_config.return_value = "val"
        service = TrelloUnifiedDataService(self.params)

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = [{"name": "F1", "id": "id1"}]
        mock_requests.get.return_value = mock_resp

        mapping = service.ensure_custom_fields("b1", {"F1": "text", "F2": "text"})
        self.assertEqual(mapping["F1"], "id1")
        self.assertNotIn("F2", mapping)

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_ensure_labels(self, mock_config, mock_requests):
        mock_config.return_value = "val"
        service = TrelloUnifiedDataService(self.params)

        # Mock existing labels
        mock_resp_get = MagicMock()
        mock_resp_get.ok = True
        mock_resp_get.json.return_value = [{"name": "L1", "id": "id1"}]
        mock_requests.get.return_value = mock_resp_get

        # Mock create label
        mock_resp_post = MagicMock()
        mock_resp_post.ok = True
        mock_resp_post.json.return_value = {"id": "id2", "name": "L2"}
        mock_requests.post.return_value = mock_resp_post

        mapping = service.ensure_labels("b1", {"L1": "green", "L2": "red"})
        self.assertEqual(mapping["L1"], "id1")
        self.assertEqual(mapping["L2"], "id2")

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_set_card_cover_color(self, mock_config, mock_requests):
        mock_config.return_value = "val"
        service = TrelloUnifiedDataService(self.params)
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {}
        mock_requests.put.return_value = mock_resp

        self.assertTrue(service.set_card_cover_color("c1", "blue"))

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_webhooks(self, mock_config, mock_requests):
        mock_config.return_value = "val"
        service = TrelloUnifiedDataService(self.params)

        mock_resp_post = MagicMock()
        mock_resp_post.ok = True
        mock_resp_post.json.return_value = {"id": "w1"}
        mock_requests.post.return_value = mock_resp_post

        mock_resp_del = MagicMock()
        mock_resp_del.ok = True
        mock_requests.delete.return_value = mock_resp_del

        self.assertEqual(service.register_webhook("m1", "url", "desc"), "w1")
        self.assertTrue(service.delete_webhook("w1"))

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.requests")
    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter.config")
    def test_search_items(self, mock_config, mock_requests):
        mock_config.return_value = "val"
        service = TrelloUnifiedDataService(self.params)

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"cards": [{"id": "c1"}]}
        mock_requests.get.return_value = mock_resp

        res = service.search_items("b1", {"query": "q"})
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["id"], "c1")
