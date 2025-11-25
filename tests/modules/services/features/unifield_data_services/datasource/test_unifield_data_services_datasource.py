
import unittest
from unittest.mock import MagicMock, patch

from smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter import (
    ClicupUnifiedDataService,
)
from smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter import (
    TrelloUnifiedDataService,
)
from smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.unifield_data_services_datasource import (
    UnifieldDataServicesDatasource,
    _InMemoryUnifiedDataService,
)
from smart_core_assistant_painel.modules.services.utils.erros import (
    UnifieldDataServicesError,
)
from smart_core_assistant_painel.modules.services.utils.parameters import (
    UnifieldDataServicesParameters,
)


class TestUnifieldDataServicesDatasource(unittest.TestCase):
    def setUp(self):
        self.datasource = UnifieldDataServicesDatasource()
        self.params = UnifieldDataServicesParameters(
            data_source_id="test_source",
            error=UnifieldDataServicesError("Test Error"),
        )

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.unifield_data_services_datasource.TrelloUnifiedDataService")
    def test_call_trello(self, mock_trello):
        self.params.provider = "trello"
        service = self.datasource(self.params)
        mock_trello.assert_called_once_with(params=self.params)
        self.assertEqual(service, mock_trello.return_value)

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.unifield_data_services_datasource.ClicupUnifiedDataService")
    def test_call_clickup(self, mock_clickup):
        self.params.provider = "clickup"
        service = self.datasource(self.params)
        mock_clickup.assert_called_once_with(params=self.params)
        self.assertEqual(service, mock_clickup.return_value)

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.unifield_data_services_datasource.ClicupUnifiedDataService")
    def test_call_clicup_alt_spelling(self, mock_clickup):
        self.params.provider = "clicup"
        service = self.datasource(self.params)
        mock_clickup.assert_called_once_with(params=self.params)
        self.assertEqual(service, mock_clickup.return_value)

    def test_call_in_memory_fallback(self):
        self.params.provider = "unknown_provider"
        service = self.datasource(self.params)
        self.assertIsInstance(service, _InMemoryUnifiedDataService)

    @patch("smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.unifield_data_services_datasource.logger")
    def test_observability(self, mock_logger):
        self.params.enable_observability = True
        self.params.provider = "unknown"
        self.datasource(self.params)
        mock_logger.info.assert_called()


class TestInMemoryUnifiedDataService(unittest.TestCase):
    def setUp(self):
        self.params = UnifieldDataServicesParameters(
            data_source_id="default_source",
            error=UnifieldDataServicesError("Test Error"),
            enable_observability=True,
        )
        self.service = _InMemoryUnifiedDataService(self.params)

    def test_create_container(self):
        cid = self.service.create_container("test_container")
        self.assertTrue(isinstance(cid, str))
        container = self.service.get_container(cid)
        self.assertIsNotNone(container)
        self.assertEqual(container["name"], "test_container")

    def test_add_data_source(self):
        cid = self.service.create_container("test_container")
        ds_id = "my_data_source"
        link_id = self.service.add_data_source(cid, ds_id, position=1.0)

        container = self.service.get_container(cid)
        self.assertEqual(len(container["data_sources"]), 1)
        self.assertEqual(container["data_sources"][0]["data_source_id"], ds_id)

        ds_info = self.service.get_data_source(ds_id)
        self.assertEqual(ds_info["container_id"], cid)

    def test_add_data_source_implicit_container(self):
        cid = "non_existent"
        self.service.add_data_source(cid, "ds1")
        container = self.service.get_container(cid)
        self.assertIsNotNone(container)
        self.assertEqual(container["name"], "implicit")

    def test_update_schema(self):
        version = self.service.update_schema("ds1", {"field": "type"})
        self.assertTrue(isinstance(version, str))
        # No direct getter for schemas exposed, but we assume it works if no error

    def test_create_and_get_item(self):
        payload = {"key": "value"}
        item_id = self.service.create_item("ds1", payload)
        item = self.service.get_item("ds1", item_id)
        self.assertEqual(item, payload)

    def test_update_item(self):
        item_id = self.service.create_item("ds1", {"key": "v1"})
        self.service.update_item("ds1", item_id, {"key": "v2"})
        item = self.service.get_item("ds1", item_id)
        self.assertEqual(item["key"], "v2")

    def test_add_relation_property(self):
        prop_id = self.service.add_relation_property("ds1", "rel1", "target1")
        self.assertTrue(isinstance(prop_id, str))

    def test_append_block(self):
        cid = self.service.create_container("c1")
        blk = {"type": "text"}
        bid = self.service.append_block(cid, blk)

        container = self.service.get_container(cid)
        self.assertEqual(len(container["blocks"]), 1)
        self.assertEqual(container["blocks"][0]["id"], bid)
