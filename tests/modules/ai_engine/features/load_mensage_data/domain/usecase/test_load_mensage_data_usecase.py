import unittest

from py_return_success_or_error import ErrorReturn, SuccessReturn

from smart_core_assistant_painel.modules.ai_engine.features.load_mensage_data.domain.usecase.load_mensage_data_usecase import (
    LoadMensageDataUseCase,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    DataMensageParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.erros import DataMessageError


class TestLoadMensageDataUseCase(unittest.TestCase):
    def setUp(self):
        self.use_case = LoadMensageDataUseCase()

    # Tests for normalize_phone
    def test_normalize_phone_standard(self):
        self.assertEqual(
            self.use_case.normalize_phone("55 11 99999-9999"), "5511999999999"
        )

    def test_normalize_phone_with_plus_and_parens(self):
        self.assertEqual(
            self.use_case.normalize_phone("+55(11)99999-9999"), "5511999999999"
        )

    def test_normalize_phone_no_special_chars(self):
        self.assertEqual(
            self.use_case.normalize_phone("5511999999999"), "5511999999999"
        )

    def test_normalize_phone_duplicate_country_code(self):
        self.assertEqual(
            self.use_case.normalize_phone("555511999999999"), "5511999999999"
        )

    def test_normalize_phone_empty_string(self):
        self.assertEqual(self.use_case.normalize_phone(""), "")

    def test_normalize_phone_none(self):
        self.assertEqual(self.use_case.normalize_phone(None), "")

    def test_normalize_phone_with_non_digits(self):
        self.assertEqual(
            self.use_case.normalize_phone("abc55def11ghi99999jkl9999"), "5511999999999"
        )

    # Tests for __call__ method
    def _create_base_payload(self):
        return {
            "instance": "test_instance",
            "apikey": "test_api_key",
            "data": {
                "key": {
                    "remoteJid": "5511987654321@s.whatsapp.net",
                    "fromMe": False,
                    "id": "MSG_ID_123",
                },
                "pushName": "Test User",
                "messageTimestamp": 1678886400,
                "message": {},
            },
        }

    def test_call_missing_instance(self):
        payload = self._create_base_payload()
        del payload["instance"]
        params = DataMensageParameters(data=payload, error=DataMessageError)
        result = self.use_case(params)
        self.assertIsInstance(result, ErrorReturn)
        self.assertIn("Campo 'instance' não encontrado", result.error.message)

    def test_call_missing_data_section(self):
        payload = self._create_base_payload()
        del payload["data"]
        params = DataMensageParameters(data=payload, error=DataMessageError)
        result = self.use_case(params)
        self.assertIsInstance(result, ErrorReturn)
        self.assertIn("Campo 'data' não encontrado", result.error.message)

    def test_call_missing_key_section(self):
        payload = self._create_base_payload()
        del payload["data"]["key"]
        params = DataMensageParameters(data=payload, error=DataMessageError)
        result = self.use_case(params)
        self.assertIsInstance(result, ErrorReturn)
        self.assertIn("Campo 'key' não encontrado", result.error.message)

    def test_call_missing_remote_jid(self):
        payload = self._create_base_payload()
        del payload["data"]["key"]["remoteJid"]
        params = DataMensageParameters(data=payload, error=DataMessageError)
        result = self.use_case(params)
        self.assertIsInstance(result, ErrorReturn)
        self.assertIn("Campo 'remoteJid' não encontrado", result.error.message)

    def test_call_missing_message_section(self):
        payload = self._create_base_payload()
        del payload["data"]["message"]
        params = DataMensageParameters(data=payload, error=DataMessageError)
        result = self.use_case(params)
        self.assertIsInstance(result, ErrorReturn)
        self.assertIn("Campo 'message' não encontrado", result.error.message)

    def test_call_conversation_message(self):
        payload = self._create_base_payload()
        payload["data"]["message"] = {"conversation": "Hello World"}
        params = DataMensageParameters(data=payload, error=DataMessageError)

        result = self.use_case(params)

        self.assertIsInstance(result, SuccessReturn)
        message_data = result.unwrap()
        self.assertEqual(message_data.instance, "test_instance")
        self.assertEqual(message_data.numero_telefone, "5511987654321")
        self.assertEqual(message_data.from_me, False)
        self.assertEqual(message_data.conteudo, "Hello World")
        self.assertEqual(message_data.message_type, "conversation")
        self.assertEqual(message_data.message_id, "MSG_ID_123")
        self.assertEqual(message_data.nome_perfil_whatsapp, "Test User")
        self.assertEqual(message_data.metadados["messageTimestamp"], 1678886400)

    def test_call_extended_text_message(self):
        payload = self._create_base_payload()
        payload["data"]["message"] = {
            "extendedTextMessage": {"text": "This is an extended message"}
        }
        params = DataMensageParameters(data=payload, error=DataMessageError)

        result = self.use_case(params)

        self.assertIsInstance(result, SuccessReturn)
        message_data = result.unwrap()
        self.assertEqual(message_data.conteudo, "This is an extended message")
        self.assertEqual(message_data.message_type, "extendedTextMessage")

    def test_call_image_message(self):
        payload = self._create_base_payload()
        payload["data"]["message"] = {
            "imageMessage": {
                "caption": "Beautiful view",
                "mimetype": "image/jpeg",
                "url": "http://example.com/image.jpg",
                "fileLength": 12345,
            }
        }
        params = DataMensageParameters(data=payload, error=DataMessageError)

        result = self.use_case(params)

        self.assertIsInstance(result, SuccessReturn)
        message_data = result.unwrap()
        self.assertEqual(message_data.conteudo, "Beautiful view")
        self.assertEqual(message_data.message_type, "imageMessage")
        self.assertEqual(message_data.metadados["mimetype"], "image/jpeg")
        self.assertEqual(message_data.metadados["url"], "http://example.com/image.jpg")
        self.assertEqual(message_data.metadados["fileLength"], 12345)

    def test_call_missing_instance(self):
        payload = self._create_base_payload()
        del payload["instance"]
        params = DataMensageParameters(data=payload, error=DataMessageError("Erro de validacao"))
        result = self.use_case(params)
        self.assertIsInstance(result, ErrorReturn)
        self.assertIn("Campo 'instance' não encontrado", result.error.message)

    def test_call_missing_data_section(self):
        payload = self._create_base_payload()
        del payload["data"]
        params = DataMensageParameters(data=payload, error=DataMessageError("Erro de validacao"))
        result = self.use_case(params)
        self.assertIsInstance(result, ErrorReturn)
        self.assertIn("Campo 'data' não encontrado", result.error.message)

    def test_call_missing_key_section(self):
        payload = self._create_base_payload()
        del payload["data"]["key"]
        params = DataMensageParameters(data=payload, error=DataMessageError("Erro de validacao"))
        result = self.use_case(params)
        self.assertIsInstance(result, ErrorReturn)
        self.assertIn("Campo 'key' não encontrado", result.error.message)

    def test_call_missing_remote_jid(self):
        payload = self._create_base_payload()
        del payload["data"]["key"]["remoteJid"]
        params = DataMensageParameters(data=payload, error=DataMessageError("Erro de validacao"))
        result = self.use_case(params)
        self.assertIsInstance(result, ErrorReturn)
        self.assertIn("Campo 'remoteJid' não encontrado", result.error.message)

    def test_call_missing_message_section(self):
        payload = self._create_base_payload()
        del payload["data"]["message"]
        params = DataMensageParameters(data=payload, error=DataMessageError("Erro de validacao"))
        result = self.use_case(params)
        self.assertIsInstance(result, ErrorReturn)
        self.assertIn("Campo 'message' não encontrado", result.error.message)

    def test_call_conversation_message(self):
        payload = self._create_base_payload()
        payload["data"]["message"] = {"conversation": "Hello World"}
        params = DataMensageParameters(data=payload, error=DataMessageError("Erro de validacao"))

        result = self.use_case(params)

        self.assertIsInstance(result, SuccessReturn)
        message_data = result.unwrap()
        self.assertEqual(message_data.instance, "test_instance")
        self.assertEqual(message_data.numero_telefone, "5511987654321")
        self.assertEqual(message_data.from_me, False)
        self.assertEqual(message_data.conteudo, "Hello World")
        self.assertEqual(message_data.message_type, "conversation")
        self.assertEqual(message_data.message_id, "MSG_ID_123")
        self.assertEqual(message_data.nome_perfil_whatsapp, "Test User")
        self.assertEqual(message_data.metadados["messageTimestamp"], 1678886400)

    def test_call_extended_text_message(self):
        payload = self._create_base_payload()
        payload["data"]["message"] = {
            "extendedTextMessage": {"text": "This is an extended message"}
        }
        params = DataMensageParameters(data=payload, error=DataMessageError("Erro de validacao"))

        result = self.use_case(params)

        self.assertIsInstance(result, SuccessReturn)
        message_data = result.unwrap()
        self.assertEqual(message_data.conteudo, "This is an extended message")
        self.assertEqual(message_data.message_type, "extendedTextMessage")

    def test_call_image_message(self):
        payload = self._create_base_payload()
        payload["data"]["message"] = {
            "imageMessage": {
                "caption": "Beautiful view",
                "mimetype": "image/jpeg",
                "url": "http://example.com/image.jpg",
                "fileLength": 12345,
            }
        }
        params = DataMensageParameters(data=payload, error=DataMessageError("Erro de validacao"))

        result = self.use_case(params)

        self.assertIsInstance(result, SuccessReturn)
        message_data = result.unwrap()
        self.assertEqual(message_data.conteudo, "Beautiful view")
        self.assertEqual(message_data.message_type, "imageMessage")
        self.assertEqual(message_data.metadados["mimetype"], "image/jpeg")
        self.assertEqual(message_data.metadados["url"], "http://example.com/image.jpg")
        self.assertEqual(message_data.metadados["fileLength"], 12345)


if __name__ == "__main__":
    unittest.main()
