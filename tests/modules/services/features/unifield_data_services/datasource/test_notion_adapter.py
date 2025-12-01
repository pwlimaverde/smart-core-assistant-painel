
import asyncio
import sys
import unittest
from unittest.mock import MagicMock, Mock, patch

from notion_py_client.notion_client import APIResponseError

from smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.notion_adapter import (
    NotionUnifiedDataService,
)
from smart_core_assistant_painel.modules.services.utils.parameters import (
    UnifieldDataServicesParameters,
)
from smart_core_assistant_painel.modules.services.utils.erros import (
    UnifieldDataServicesError,
)

class TestNotionUnifiedDataService(unittest.TestCase):
    def setUp(self):
        self.mock_params = UnifieldDataServicesParameters(
            data_source_id="test_ds_id",
            provider="notion",
            root_container_name="root",
            enable_observability=True,
            error=UnifieldDataServicesError("Test Error"),
        )

        # Mock NotionAsyncClient
        self.mock_client_patcher = patch(
            "smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.notion_adapter.NotionAsyncClient"
        )
        self.mock_client_cls = self.mock_client_patcher.start()
        self.mock_client = self.mock_client_cls.return_value

        # Mock decouple.config
        self.mock_config_patcher = patch(
            "smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.notion_adapter.config"
        )
        self.mock_config = self.mock_config_patcher.start()
        self.mock_config.return_value = "fake_token"

        # Mock asyncio loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Mock Django Models
        self.mock_django_models = MagicMock()
        self.mock_notion_db_config = MagicMock()
        self.mock_django_models.NotionDatabaseConfig = self.mock_notion_db_config

        # Patch the module where models are imported
        self.modules_patcher = patch.dict(sys.modules, {
            "smart_core_assistant_painel.app.notion_sync.models": self.mock_django_models
        })
        self.modules_patcher.start()

        self.service = NotionUnifiedDataService(self.mock_params)
        # Replace the service loop with our test loop to avoid issues
        self.service._loop = self.loop

    def tearDown(self):
        self.mock_client_patcher.stop()
        self.mock_config_patcher.stop()
        self.modules_patcher.stop()
        self.loop.close()

    def _async_return(self, value):
        f = asyncio.Future(loop=self.loop)
        f.set_result(value)
        return f

    def test_init_raises_if_no_token(self):
        self.mock_config.side_effect = lambda x, default=None: "" if x == "NOTION_TOKEN" else default
        with self.assertRaises(ValueError):
            NotionUnifiedDataService(self.mock_params)

    def test_create_container(self):
        container_id = self.service.create_container("test_container")
        self.assertTrue(isinstance(container_id, str))
        self.assertTrue(len(container_id) > 0)

    def test_add_data_source(self):
        result = self.service.add_data_source("container_id", "ds_id")
        self.assertEqual(result, "ds_id")

    def test_update_schema(self):
        mock_config_obj = MagicMock()
        self.mock_notion_db_config.objects.filter.return_value.first.return_value = mock_config_obj

        schema = {"prop": "type"}
        version_id = self.service.update_schema("ds_id", schema)

        self.assertTrue(isinstance(version_id, str))
        self.assertEqual(mock_config_obj.notion_schema, schema)
        mock_config_obj.save.assert_called_once()

    def test_update_schema_not_found(self):
        self.mock_notion_db_config.objects.filter.return_value.first.return_value = None
        with self.assertRaises(ValueError):
            self.service.update_schema("ds_id", {})

    def test_create_item_success(self):
        mock_config_obj = MagicMock()
        mock_config_obj.notion_database_id = "db_id"
        mock_config_obj.data_source_id = "ds_id"
        mock_config_obj.notion_schema = {"prop": "type"}
        self.mock_notion_db_config.objects.filter.return_value.first.return_value = mock_config_obj

        # Mock Notion API response for schema check
        self.mock_client.request.side_effect = [
            # First call: get database schema
            self._async_return({"properties": {"prop": {}}}),
            # Second call: create page
            self._async_return({"id": "page_id"})
        ]

        # Mock _run to just execute the coroutine
        self.service._run = lambda coro: self.loop.run_until_complete(coro)

        item_id = self.service.create_item("ds_id", {"prop": "value"})
        self.assertEqual(item_id, "page_id")

    def test_create_item_not_found(self):
        self.mock_notion_db_config.objects.filter.return_value.first.return_value = None
        with self.assertRaises(ValueError):
            self.service.create_item("ds_id", {})

    def test_update_item(self):
        self.service._run = lambda coro: self.loop.run_until_complete(coro)
        self.mock_client.request.return_value = self._async_return({})

        op_id = self.service.update_item("ds_id", "item_id", {"prop": "val"})
        self.assertTrue(isinstance(op_id, str))

        self.mock_client.request.assert_called()

    def test_add_relation_property(self):
        mock_config_obj = MagicMock()
        mock_config_obj.notion_database_id = "db_id"
        self.mock_notion_db_config.objects.filter.return_value.first.return_value = mock_config_obj

        self.service._run = lambda coro: self.loop.run_until_complete(coro)
        self.mock_client.request.return_value = self._async_return({})

        prop_id = self.service.add_relation_property("ds_id", "rel_prop", "target_id")
        self.assertTrue(isinstance(prop_id, str))

    def test_get_container(self):
        result = self.service.get_container("cid")
        self.assertEqual(result, {"id": "cid", "type": "container"})

    def test_get_data_source(self):
        mock_config_obj = MagicMock()
        mock_config_obj.notion_database_id = "db_id"
        mock_config_obj.name = "name"
        mock_config_obj.notion_schema = {}
        self.mock_notion_db_config.objects.filter.return_value.first.return_value = mock_config_obj

        result = self.service.get_data_source("ds_id")
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "ds_id")

    def test_get_item(self):
        self.service._run = lambda coro: self.loop.run_until_complete(coro)
        self.mock_client.request.return_value = self._async_return({"id": "item_id"})

        result = self.service.get_item("ds_id", "item_id")
        self.assertEqual(result["id"], "item_id")

    def test_append_block(self):
        self.service._run = lambda coro: self.loop.run_until_complete(coro)
        self.mock_client.request.return_value = self._async_return({})

        block_id = self.service.append_block("cid", {"type": "p"})
        self.assertTrue(isinstance(block_id, str))
