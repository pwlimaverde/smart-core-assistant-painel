
import unittest
from unittest.mock import MagicMock, patch

from py_return_success_or_error import ErrorReturn, SuccessReturn

from smart_core_assistant_painel.modules.services.features.features_compose import (
    FeaturesCompose,
)
from smart_core_assistant_painel.modules.services.utils.erros import (
    SetEnvironRemoteError,
    UnifieldDataServicesError,
)


class TestFeaturesCompose(unittest.TestCase):
    @patch("smart_core_assistant_painel.modules.services.features.features_compose.SERVICEHUB")
    @patch("smart_core_assistant_painel.modules.services.features.features_compose.SetEnvironRemoteUseCase")
    @patch("smart_core_assistant_painel.modules.services.features.features_compose.SetEnvironRemoteFirebaseDatasource")
    def test_set_environ_remote_success(self, mock_datasource, mock_usecase_cls, mock_servicehub):
        mock_usecase = mock_usecase_cls.return_value
        mock_usecase.return_value = SuccessReturn(None)

        FeaturesCompose.set_environ_remote()

        mock_usecase.assert_called_once()
        mock_servicehub.reload_config.assert_called_once()

    @patch("smart_core_assistant_painel.modules.services.features.features_compose.SERVICEHUB")
    @patch("smart_core_assistant_painel.modules.services.features.features_compose.SetEnvironRemoteUseCase")
    @patch("smart_core_assistant_painel.modules.services.features.features_compose.SetEnvironRemoteFirebaseDatasource")
    def test_set_environ_remote_failure(self, mock_datasource, mock_usecase_cls, mock_servicehub):
        mock_usecase = mock_usecase_cls.return_value
        error_instance = SetEnvironRemoteError("Error")
        mock_usecase.return_value = ErrorReturn(error_instance)

        with self.assertRaises(SetEnvironRemoteError):
            FeaturesCompose.set_environ_remote()

        mock_servicehub.reload_config.assert_not_called()

    @patch("smart_core_assistant_painel.modules.services.features.features_compose.SERVICEHUB")
    @patch("smart_core_assistant_painel.modules.services.features.features_compose.UnifieldDataServicesUseCase")
    @patch("smart_core_assistant_painel.modules.services.features.features_compose.UnifieldDataServicesDatasource")
    def test_unifield_data_services_success(self, mock_datasource, mock_usecase_cls, mock_servicehub):
        mock_usecase = mock_usecase_cls.return_value
        mock_service = MagicMock()
        mock_usecase.return_value = SuccessReturn(mock_service)

        FeaturesCompose.unifield_data_services()

        mock_usecase.assert_called_once()
        mock_servicehub.set_unified_data_service.assert_called_once_with(mock_service)

    @patch("smart_core_assistant_painel.modules.services.features.features_compose.SERVICEHUB")
    @patch("smart_core_assistant_painel.modules.services.features.features_compose.UnifieldDataServicesUseCase")
    @patch("smart_core_assistant_painel.modules.services.features.features_compose.UnifieldDataServicesDatasource")
    def test_unifield_data_services_failure(self, mock_datasource, mock_usecase_cls, mock_servicehub):
        mock_usecase = mock_usecase_cls.return_value
        error_instance = UnifieldDataServicesError("Error")
        mock_usecase.return_value = ErrorReturn(error_instance)

        with self.assertRaises(UnifieldDataServicesError):
            FeaturesCompose.unifield_data_services()

        mock_servicehub.set_unified_data_service.assert_not_called()
