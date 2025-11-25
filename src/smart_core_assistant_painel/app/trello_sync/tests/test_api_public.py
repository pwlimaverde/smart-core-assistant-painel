import json
from typing import Any

from django.test import Client, TestCase
from django.urls import reverse


class WebhookApiTests(TestCase):
    def setUp(self) -> None:
        self.client: Client = Client()

    def test_head_returns_ok(self) -> None:
        url: str = reverse("trello_sync_api:webhook")
        response = self.client.head(url)
        self.assertEqual(response.status_code, 200)

    def test_post_invalid_json_returns_400(self) -> None:
        url: str = reverse("trello_sync_api:webhook")
        response = self.client.post(
            url, data=b"not-json", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_post_valid_payload_returns_200(self) -> None:
        url: str = reverse("trello_sync_api:webhook")
        payload: dict[str, Any] = {
            "action": {"id": "abc123", "type": "updateCard", "data": {}}
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
