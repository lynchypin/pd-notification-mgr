# tests/test_cli.py
from unittest.mock import patch, MagicMock
from pd_notify.cli import main


class TestCLI:
    @patch("pd_notify.cli.menus")
    @patch("pd_notify.cli.display")
    @patch("pd_notify.cli.PagerDutyClient")
    def test_main_exit_immediately(self, mock_client_cls, mock_display, mock_menus):
        mock_menus.prompt_api_token.return_value = "test-token"
        mock_menus.main_menu.return_value = "exit"
        main()
        mock_menus.prompt_api_token.assert_called_once()
        mock_display.print_header.assert_called_once()

    @patch("pd_notify.cli.menus")
    @patch("pd_notify.cli.display")
    @patch("pd_notify.cli.PagerDutyClient")
    def test_main_list_all_users_then_back(self, mock_client_cls, mock_display, mock_menus):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.list_users.return_value = [
            {"id": "P1", "name": "Alice", "email": "a@b.com", "role": "admin"}
        ]
        mock_client.get_contact_methods.return_value = []
        mock_client.get_notification_rules.return_value = []
        mock_menus.prompt_api_token.return_value = "test-token"
        mock_menus.main_menu.side_effect = ["all_users", "exit"]
        mock_menus.select_user.return_value = None
        main()
        mock_client.list_users.assert_called_once()

    @patch("pd_notify.cli.menus")
    @patch("pd_notify.cli.display")
    @patch("pd_notify.cli.PagerDutyClient")
    def test_main_list_by_team(self, mock_client_cls, mock_display, mock_menus):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.list_teams.return_value = [{"id": "T1", "name": "Engineering"}]
        mock_client.list_team_members.return_value = [
            {"user": {"id": "P1", "name": "Alice", "email": "a@b.com", "role": "user"}}
        ]
        mock_menus.prompt_api_token.return_value = "test-token"
        mock_menus.main_menu.side_effect = ["by_team", "exit"]
        mock_menus.select_team.return_value = {"id": "T1", "name": "Engineering"}
        mock_menus.select_user.return_value = None
        main()
        mock_client.list_teams.assert_called_once()
        mock_client.list_team_members.assert_called_once_with("T1")
