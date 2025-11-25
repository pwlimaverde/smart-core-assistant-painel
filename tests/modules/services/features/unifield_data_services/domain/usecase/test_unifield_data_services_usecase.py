
import unittest
from unittest.mock import Mock, patch

from py_return_success_or_error import ErrorReturn, SuccessReturn

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

    def test_call_error_from_datasource(self):
        """Testa o caso de erro retornado pelo datasource."""
        error_msg = "Datasource error"
        with patch.object(
            self.usecase,
            "_resultDatasource",
            return_value=ErrorReturn(error_msg),
        ):
            result = self.usecase(self.parameters)

            self.assertIsInstance(result, ErrorReturn)
            self.assertIsInstance(result.result, UnifieldDataServicesError)
            self.assertIn(
                "Erro ao executar unifield_data_services: Datasource error",
                result.result.message,
            )

    def test_call_unexpected_return(self):
        """Testa o caso de retorno inesperado do datasource."""
        with patch.object(
            self.usecase,
            "_resultDatasource",
            return_value="unexpected string",
        ):
            result = self.usecase(self.parameters)

            self.assertIsInstance(result, ErrorReturn)
            self.assertIsInstance(result.result, UnifieldDataServicesError)
            self.assertEqual(
                result.result.message, "Tipo de retorno inesperado do datasource."
            )
