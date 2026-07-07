from unittest.mock import MagicMock, patch
from pd_notify.bulk import build_compliance_report, apply_bulk_action


def _make_client():
    client = MagicMock()
    return client


class TestBuildComplianceReport:
    def test_user_matches(self):
        client = _make_client()
        users = [{"id": "P1", "name": "Alice", "email": "a@b.com"}]
        client.get_contact_methods.return_value = [
            {"id": "CM1", "type": "sms_contact_method", "address": "+1555"}
        ]
        client.get_notification_rules.return_value = [
            {
                "id": "NR1",
                "urgency": "high",
                "start_delay_in_minutes": 0,
                "contact_method": {"id": "CM1", "type": "sms_contact_method"},
            }
        ]
        report = build_compliance_report(users, client, "sms_contact_method", "high", 0)
        assert len(report) == 1
        assert report[0]["status"] == "match"

    def test_user_partial_different_timing(self):
        client = _make_client()
        users = [{"id": "P1", "name": "Alice", "email": "a@b.com"}]
        client.get_contact_methods.return_value = [
            {"id": "CM1", "type": "sms_contact_method", "address": "+1555"}
        ]
        client.get_notification_rules.return_value = [
            {
                "id": "NR1",
                "urgency": "high",
                "start_delay_in_minutes": 5,
                "contact_method": {"id": "CM1", "type": "sms_contact_method"},
            }
        ]
        report = build_compliance_report(users, client, "sms_contact_method", "high", 0)
        assert report[0]["status"] == "partial"

    def test_user_missing_method_type(self):
        client = _make_client()
        users = [{"id": "P1", "name": "Bob", "email": "b@b.com"}]
        client.get_contact_methods.return_value = [
            {"id": "CM1", "type": "email_contact_method", "address": "b@b.com"}
        ]
        client.get_notification_rules.return_value = []
        report = build_compliance_report(users, client, "sms_contact_method", "high", 0)
        assert report[0]["status"] == "missing"


class TestApplyBulkAction:
    def test_skip_action(self):
        client = _make_client()
        user = {"id": "P1", "name": "Alice"}
        result = apply_bulk_action(client, user, "skip", "sms_contact_method", "high", 0, [], [])
        assert "skip" in result.lower() or "skipped" in result.lower()
        client.create_notification_rule.assert_not_called()

    def test_combine_action_creates_rule(self):
        client = _make_client()
        client.create_notification_rule.return_value = {"id": "NR_NEW"}
        user = {"id": "P1", "name": "Alice"}
        contact_methods = [{"id": "CM1", "type": "sms_contact_method", "address": "+1555"}]
        existing_rules = [
            {
                "id": "NR1",
                "urgency": "high",
                "start_delay_in_minutes": 0,
                "contact_method": {"id": "CM_OLD", "type": "email_contact_method"},
            }
        ]
        result = apply_bulk_action(
            client, user, "combine", "sms_contact_method", "high", 0,
            contact_methods, existing_rules,
        )
        client.create_notification_rule.assert_called_once()
        assert "added" in result.lower() or "created" in result.lower()

    def test_replace_action_deletes_and_creates(self):
        client = _make_client()
        client.create_notification_rule.return_value = {"id": "NR_NEW"}
        user = {"id": "P1", "name": "Alice"}
        contact_methods = [{"id": "CM1", "type": "sms_contact_method", "address": "+1555"}]
        existing_rules = [
            {
                "id": "NR1",
                "urgency": "high",
                "start_delay_in_minutes": 5,
                "contact_method": {"id": "CM_OLD", "type": "email_contact_method"},
            }
        ]
        result = apply_bulk_action(
            client, user, "replace", "sms_contact_method", "high", 0,
            contact_methods, existing_rules,
        )
        client.delete_notification_rule.assert_called()
        client.create_notification_rule.assert_called_once()
