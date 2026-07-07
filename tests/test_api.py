# tests/test_api.py
import httpx
import pytest
from unittest.mock import patch, MagicMock
from pd_notify.api import PagerDutyClient


def _mock_response(json_data, status_code=200):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


class TestPagerDutyClient:
    def test_init_sets_headers(self):
        client = PagerDutyClient("test-token")
        assert client.token == "test-token"
        assert client.base_url == "https://api.pagerduty.com"

    @patch("httpx.Client.request")
    def test_list_users_single_page(self, mock_request):
        mock_request.return_value = _mock_response({
            "users": [
                {"id": "P1", "name": "Alice", "email": "alice@example.com"}
            ],
            "more": False,
            "offset": 0,
            "limit": 100,
        })
        client = PagerDutyClient("test-token")
        users = client.list_users()
        assert len(users) == 1
        assert users[0]["name"] == "Alice"

    @patch("httpx.Client.request")
    def test_list_users_pagination(self, mock_request):
        page1 = _mock_response({
            "users": [{"id": f"P{i}", "name": f"User{i}"} for i in range(100)],
            "more": True,
            "offset": 0,
            "limit": 100,
        })
        page2 = _mock_response({
            "users": [{"id": "P100", "name": "User100"}],
            "more": False,
            "offset": 100,
            "limit": 100,
        })
        mock_request.side_effect = [page1, page2]
        client = PagerDutyClient("test-token")
        users = client.list_users()
        assert len(users) == 101

    @patch("httpx.Client.request")
    def test_get_contact_methods(self, mock_request):
        mock_request.return_value = _mock_response({
            "contact_methods": [
                {"id": "CM1", "type": "email_contact_method", "address": "alice@example.com"},
                {"id": "CM2", "type": "sms_contact_method", "address": "+15551234567"},
            ],
            "more": False,
        })
        client = PagerDutyClient("test-token")
        methods = client.get_contact_methods("P1")
        assert len(methods) == 2
        assert methods[1]["type"] == "sms_contact_method"

    @patch("httpx.Client.request")
    def test_get_notification_rules(self, mock_request):
        mock_request.return_value = _mock_response({
            "notification_rules": [
                {
                    "id": "NR1",
                    "urgency": "high",
                    "start_delay_in_minutes": 0,
                    "contact_method": {"id": "CM1", "type": "email_contact_method"},
                }
            ],
            "more": False,
        })
        client = PagerDutyClient("test-token")
        rules = client.get_notification_rules("P1")
        assert len(rules) == 1
        assert rules[0]["urgency"] == "high"

    @patch("httpx.Client.request")
    def test_create_notification_rule(self, mock_request):
        mock_request.return_value = _mock_response({
            "notification_rule": {
                "id": "NR2",
                "urgency": "low",
                "start_delay_in_minutes": 5,
                "contact_method": {"id": "CM2", "type": "sms_contact_method"},
            }
        }, status_code=201)
        client = PagerDutyClient("test-token")
        rule = client.create_notification_rule("P1", {
            "notification_rule": {
                "urgency": "low",
                "start_delay_in_minutes": 5,
                "contact_method": {"id": "CM2", "type": "sms_contact_method"},
            }
        })
        assert rule["id"] == "NR2"

    @patch("httpx.Client.request")
    def test_delete_notification_rule(self, mock_request):
        mock_request.return_value = _mock_response({}, status_code=204)
        mock_request.return_value.raise_for_status = MagicMock()
        client = PagerDutyClient("test-token")
        client.delete_notification_rule("P1", "NR1")
        mock_request.assert_called_once()

    @patch("httpx.Client.request")
    def test_rate_limit_retry(self, mock_request):
        rate_limited = MagicMock(spec=httpx.Response)
        rate_limited.status_code = 429
        rate_limited.headers = {"Retry-After": "1"}
        rate_limited.raise_for_status.side_effect = httpx.HTTPError(
            "429", request=MagicMock(), response=rate_limited
        )
        success = _mock_response({"users": [], "more": False})
        mock_request.side_effect = [rate_limited, success]
        client = PagerDutyClient("test-token")
        users = client.list_users()
        assert users == []
        assert mock_request.call_count == 2
