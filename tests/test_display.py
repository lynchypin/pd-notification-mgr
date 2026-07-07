from io import StringIO
from unittest.mock import patch
from pd_notify.display import (
    render_users_table,
    render_notification_rules,
    render_contact_methods,
    render_compliance_report,
    print_header,
)
from rich.console import Console


def _capture_output(func, *args):
    console = Console(file=StringIO(), force_terminal=True, width=120)
    func(*args, console=console)
    return console.file.getvalue()


class TestDisplay:
    def test_render_users_table(self):
        users = [
            {"id": "P1", "name": "Alice Smith", "email": "alice@example.com", "role": "admin"},
            {"id": "P2", "name": "Bob Jones", "email": "bob@example.com", "role": "user"},
        ]
        output = _capture_output(render_users_table, users)
        assert "Alice Smith" in output
        assert "Bob Jones" in output
        assert "alice@example.com" in output

    def test_render_notification_rules(self):
        rules = [
            {
                "id": "NR1",
                "urgency": "high",
                "start_delay_in_minutes": 0,
                "contact_method": {"id": "CM1", "type": "email_contact_method", "summary": "alice@example.com"},
            },
        ]
        contact_methods = [
            {"id": "CM1", "type": "email_contact_method", "address": "alice@example.com"},
        ]
        output = _capture_output(render_notification_rules, rules, contact_methods)
        assert "high" in output
        assert "email" in output.lower()

    def test_render_contact_methods(self):
        methods = [
            {"id": "CM1", "type": "email_contact_method", "address": "alice@example.com", "label": "Work"},
            {"id": "CM2", "type": "sms_contact_method", "address": "+15551234567", "label": "Mobile"},
        ]
        output = _capture_output(render_contact_methods, methods)
        assert "alice@example.com" in output
        assert "+15551234567" in output

    def test_render_compliance_report(self):
        report = [
            {"name": "Alice", "status": "match", "detail": "Already has SMS rule at 0 min"},
            {"name": "Bob", "status": "partial", "detail": "Has SMS but timing differs (5 min)"},
            {"name": "Carol", "status": "missing", "detail": "No SMS contact method"},
        ]
        output = _capture_output(render_compliance_report, report)
        assert "Alice" in output
        assert "Bob" in output
        assert "Carol" in output

    def test_print_header(self):
        output = _capture_output(print_header)
        assert "PagerDuty" in output or "Notification" in output
