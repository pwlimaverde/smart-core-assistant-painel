
import unittest
from unittest.mock import Mock, patch

from py_return_success_or_error import SuccessReturn

from smart_core_assistant_painel.modules.services.features.unifield_data_services.domain.interface.unified_data_service import (
    UnifiedDataService,
)
from smart_core_assistant_painel.modules.services.features.unifield_data_services.domain.usecase.unifield_data_services_usecase import (
    UnifieldDataServicesUseCase,
)
from smart_core_assistant_painel.modules.services.utils.erros import (
    UnifieldDataServicesError,
)
from smart_core_assistant_painel.modules.services.utils.parameters import (
    UnifieldDataServicesParameters,
)


class TestUnifieldDataServicesUseCase(unittest.TestCase):
    def setUp(self):
        self.mock_datasource = Mock()
        self.usecase = UnifieldDataServicesUseCase(self.mock_datasource)
        # Using class as parameter.error assuming FeaturesCompose passes class
        # But wait, FeaturesCompose passes INSTANCE.
        # And I fixed the code to handle instance.
        # So I should pass INSTANCE here to match production behavior.
        self.parameters = UnifieldDataServicesParameters(
            data_source_id="test_source",
            error=UnifieldDataServicesError("Test Error"),
        )
        self.mock_service = Mock(spec=UnifiedDataService)

    def test_call_success(self):
        """Testa o caso de sucesso."""
        with patch.object(
            self.usecase,
            "_resultDatasource",
            return_value=SuccessReturn(self.mock_service),
        ):
            result = self.usecase(self.parameters)

            self.assertIsInstance(result, SuccessReturn)
            self.assertEqual(result.result, self.mock_service)
