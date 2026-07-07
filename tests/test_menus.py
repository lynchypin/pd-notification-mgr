# tests/test_menus.py
from unittest.mock import patch, MagicMock
import os
from pd_notify.menus import (
    prompt_api_token,
    main_menu,
    select_user,
    select_team,
    select_escalation_policy,
    user_action_menu,
    select_contact_method,
    prompt_urgency,
    prompt_delay,
    confirm_action,
    bulk_scope_menu,
    bulk_action_menu,
)


class TestMenus:
    @patch.dict(os.environ, {"PAGERDUTY_API_TOKEN": "env-token"})
    def test_prompt_api_token_from_env(self):
        token = prompt_api_token(use_env=True)
        assert token == "env-token"

    @patch("pd_notify.menus._inquire")
    def test_prompt_api_token_interactive(self, mock_inquire):
        mock_inquire.return_value = "typed-token"
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("PAGERDUTY_API_TOKEN", None)
            token = prompt_api_token(use_env=True)
        assert token == "typed-token"

    @patch("pd_notify.menus._inquire")
    def test_main_menu(self, mock_inquire):
        mock_inquire.return_value = "all_users"
        result = main_menu()
        assert result == "all_users"

    @patch("pd_notify.menus._inquire")
    def test_select_user(self, mock_inquire):
        users = [
            {"id": "P1", "name": "Alice", "email": "alice@example.com"},
            {"id": "P2", "name": "Bob", "email": "bob@example.com"},
        ]
        mock_inquire.return_value = "P1"
        result = select_user(users)
        assert result == users[0]

    @patch("pd_notify.menus._inquire")
    def test_select_user_back(self, mock_inquire):
        users = [
            {"id": "P1", "name": "Alice", "email": "alice@example.com"},
            {"id": "P2", "name": "Bob", "email": "bob@example.com"},
        ]
        mock_inquire.return_value = None
        result = select_user(users)
        assert result is None

    @patch("pd_notify.menus._inquire")
    def test_select_team(self, mock_inquire):
        teams = [
            {"id": "T1", "name": "Engineering"},
            {"id": "T2", "name": "Support"},
        ]
        mock_inquire.return_value = "T1"
        result = select_team(teams)
        assert result == teams[0]

    @patch("pd_notify.menus._inquire")
    def test_select_team_back(self, mock_inquire):
        teams = [
            {"id": "T1", "name": "Engineering"},
            {"id": "T2", "name": "Support"},
        ]
        mock_inquire.return_value = None
        result = select_team(teams)
        assert result is None

    @patch("pd_notify.menus._inquire")
    def test_select_escalation_policy(self, mock_inquire):
        policies = [
            {"id": "EP1", "name": "Default"},
            {"id": "EP2", "name": "Urgent"},
        ]
        mock_inquire.return_value = "EP2"
        result = select_escalation_policy(policies)
        assert result == policies[1]

    @patch("pd_notify.menus._inquire")
    def test_select_escalation_policy_back(self, mock_inquire):
        policies = [
            {"id": "EP1", "name": "Default"},
            {"id": "EP2", "name": "Urgent"},
        ]
        mock_inquire.return_value = None
        result = select_escalation_policy(policies)
        assert result is None

    @patch("pd_notify.menus._inquire")
    def test_user_action_menu(self, mock_inquire):
        mock_inquire.return_value = "edit"
        result = user_action_menu()
        assert result == "edit"

    @patch("pd_notify.menus._inquire")
    def test_select_contact_method(self, mock_inquire):
        methods = [
            {"id": "CM1", "type": "email_contact_method", "address": "a@b.com"},
            {"id": "CM2", "type": "sms_contact_method", "address": "+1555"},
        ]
        mock_inquire.return_value = "CM2"
        result = select_contact_method(methods)
        assert result == methods[1]

    @patch("pd_notify.menus._inquire")
    def test_prompt_urgency(self, mock_inquire):
        mock_inquire.return_value = "high"
        result = prompt_urgency()
        assert result == "high"

    @patch("pd_notify.menus._inquire")
    def test_prompt_delay(self, mock_inquire):
        mock_inquire.return_value = "5"
        result = prompt_delay()
        assert result == 5

    @patch("pd_notify.menus._inquire")
    def test_confirm_action(self, mock_inquire):
        mock_inquire.return_value = True
        result = confirm_action("Delete this rule?")
        assert result is True

    @patch("pd_notify.menus._inquire")
    def test_bulk_scope_menu(self, mock_inquire):
        mock_inquire.return_value = "team"
        result = bulk_scope_menu()
        assert result == "team"

    @patch("pd_notify.menus._inquire")
    def test_bulk_action_menu(self, mock_inquire):
        mock_inquire.return_value = "combine"
        result = bulk_action_menu("Alice")
        assert result == "combine"
