# tests/test_integration.py
import os
import pytest
from pd_notify.api import PagerDutyClient


pytestmark = pytest.mark.skipif(
    not os.environ.get("PAGERDUTY_API_TOKEN"),
    reason="PAGERDUTY_API_TOKEN not set — skipping integration tests",
)


class TestIntegration:
    @pytest.fixture
    def client(self):
        return PagerDutyClient(os.environ["PAGERDUTY_API_TOKEN"])

    def test_list_users(self, client):
        users = client.list_users()
        assert isinstance(users, list)
        if users:
            assert "id" in users[0]
            assert "name" in users[0]

    def test_list_teams(self, client):
        teams = client.list_teams()
        assert isinstance(teams, list)

    def test_get_contact_methods_for_first_user(self, client):
        users = client.list_users()
        if users:
            methods = client.get_contact_methods(users[0]["id"])
            assert isinstance(methods, list)

    def test_get_notification_rules_for_first_user(self, client):
        users = client.list_users()
        if users:
            rules = client.get_notification_rules(users[0]["id"])
            assert isinstance(rules, list)
