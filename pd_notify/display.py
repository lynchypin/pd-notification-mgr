"""Rich table rendering for PagerDuty data."""

from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text


_METHOD_TYPE_LABELS = {
    "email_contact_method": "Email",
    "sms_contact_method": "SMS",
    "phone_contact_method": "Phone",
    "push_notification_contact_method": "Push",
}

_STATUS_COLORS = {
    "match": "green",
    "partial": "yellow",
    "missing": "red",
}

_STATUS_ICONS = {
    "match": "✓",
    "partial": "⚠",
    "missing": "✗",
}


def _default_console(console: Optional[Console]) -> Console:
    return console or Console()


def print_header(console: Optional[Console] = None) -> None:
    console = _default_console(console)
    console.print(Panel.fit(
        "[bold cyan]PagerDuty Notification Manager[/]",
        border_style="cyan",
    ))


def print_error(message: str, console: Optional[Console] = None) -> None:
    console = _default_console(console)
    console.print(f"[bold red]Error:[/] {message}")


def print_success(message: str, console: Optional[Console] = None) -> None:
    console = _default_console(console)
    console.print(f"[bold green]✓[/] {message}")


def render_users_table(users: list[dict], console: Optional[Console] = None) -> None:
    console = _default_console(console)
    table = Table(title="Users", show_lines=False)
    table.add_column("#", style="dim", width=4)
    table.add_column("Name", style="bold")
    table.add_column("Email")
    table.add_column("Role", style="dim")

    for i, user in enumerate(users, 1):
        table.add_row(
            str(i),
            user.get("name", "Unknown"),
            user.get("email", ""),
            user.get("role", ""),
        )

    console.print(table)


def render_notification_rules(
    rules: list[dict], contact_methods: list[dict], console: Optional[Console] = None
) -> None:
    console = _default_console(console)
    cm_map = {cm["id"]: cm for cm in contact_methods}

    table = Table(title="Notification Rules", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Urgency")
    table.add_column("Method Type")
    table.add_column("Contact")
    table.add_column("Delay (min)")

    for i, rule in enumerate(rules, 1):
        cm = rule.get("contact_method", {})
        cm_id = cm.get("id", "")
        cm_detail = cm_map.get(cm_id, cm)
        method_type = _METHOD_TYPE_LABELS.get(cm.get("type", ""), cm.get("type", "Unknown"))
        address = cm_detail.get("address", cm.get("summary", ""))
        urgency_color = "red" if rule.get("urgency") == "high" else "yellow"

        table.add_row(
            str(i),
            f"[{urgency_color}]{rule.get('urgency', 'unknown')}[/]",
            method_type,
            address,
            str(rule.get("start_delay_in_minutes", 0)),
        )

    console.print(table)


def render_contact_methods(methods: list[dict], console: Optional[Console] = None) -> None:
    console = _default_console(console)
    table = Table(title="Contact Methods", show_lines=False)
    table.add_column("#", style="dim", width=4)
    table.add_column("Type")
    table.add_column("Address")
    table.add_column("Label", style="dim")

    for i, method in enumerate(methods, 1):
        method_type = _METHOD_TYPE_LABELS.get(method.get("type", ""), method.get("type", "Unknown"))
        table.add_row(
            str(i),
            method_type,
            method.get("address", ""),
            method.get("label", ""),
        )

    console.print(table)


def render_compliance_report(report: list[dict], console: Optional[Console] = None) -> None:
    console = _default_console(console)
    table = Table(title="Compliance Report", show_lines=False)
    table.add_column("Status", width=6, justify="center")
    table.add_column("User")
    table.add_column("Detail")

    for entry in report:
        status = entry.get("status", "missing")
        color = _STATUS_COLORS.get(status, "white")
        icon = _STATUS_ICONS.get(status, "?")
        table.add_row(
            f"[{color}]{icon}[/]",
            entry.get("name", "Unknown"),
            entry.get("detail", ""),
        )

    console.print(table)
