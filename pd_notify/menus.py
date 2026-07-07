# pd_notify/menus.py
"""Interactive menu prompts using InquirerPy."""

import os
from typing import Optional
from InquirerPy import inquirer


_METHOD_TYPE_LABELS = {
    "email_contact_method": "Email",
    "sms_contact_method": "SMS",
    "phone_contact_method": "Phone",
    "push_notification_contact_method": "Push",
}


def _inquire(prompt_instance):
    """Execute an InquirerPy prompt. Wrapped for testability."""
    return prompt_instance.execute()


def prompt_api_token(use_env: bool = True) -> str:
    if use_env:
        token = os.environ.get("PAGERDUTY_API_TOKEN")
        if token:
            return token
    prompt = inquirer.secret(
        message="Enter your PagerDuty API token:",
        validate=lambda x: len(x) > 0,
        invalid_message="Token cannot be empty",
        transformer=lambda _: "****",
    )
    return _inquire(prompt)


def main_menu() -> str:
    prompt = inquirer.select(
        message="What would you like to do?",
        choices=[
            {"name": "List all users", "value": "all_users"},
            {"name": "List users by team", "value": "by_team"},
            {"name": "Bulk update selected users", "value": "bulk_select"},
            {"name": "Bulk set notification rules (by scope)", "value": "bulk"},
            {"name": "Exit", "value": "exit"},
        ],
    )
    return _inquire(prompt)


def select_user(users: list[dict]) -> Optional[dict]:
    choices = [
        {"name": f"{u.get('name', u['id'])} ({u.get('email', '')})", "value": u["id"]}
        for u in users
    ]
    choices.append({"name": "← Back", "value": None})
    prompt = inquirer.select(message="Select a user:", choices=choices)
    selected_id = _inquire(prompt)
    if selected_id is None:
        return None
    return next(u for u in users if u["id"] == selected_id)


def select_users_multi(users: list[dict]) -> list[dict]:
    choices = [
        {"name": f"{u.get('name', u['id'])} ({u.get('email', '')})", "value": u["id"]}
        for u in users
    ]
    prompt = inquirer.checkbox(
        message="Select users (space to toggle, enter to confirm):",
        choices=choices,
        validate=lambda result: len(result) > 0,
        invalid_message="Select at least one user",
    )
    selected_ids = _inquire(prompt)
    return [u for u in users if u["id"] in selected_ids]


def bulk_select_scope_menu() -> str:
    prompt = inquirer.select(
        message="Select users from:",
        choices=[
            {"name": "All users", "value": "all_users"},
            {"name": "A specific team", "value": "team"},
        ],
    )
    return _inquire(prompt)


def select_team(teams: list[dict]) -> Optional[dict]:
    choices = [
        {"name": t.get("name", t["id"]), "value": t["id"]}
        for t in teams
    ]
    choices.append({"name": "← Back", "value": None})
    prompt = inquirer.select(message="Select a team:", choices=choices)
    selected_id = _inquire(prompt)
    if selected_id is None:
        return None
    return next(t for t in teams if t["id"] == selected_id)


def select_escalation_policy(policies: list[dict]) -> Optional[dict]:
    choices = [
        {"name": p.get("name", p["id"]), "value": p["id"]}
        for p in policies
    ]
    choices.append({"name": "← Back", "value": None})
    prompt = inquirer.select(message="Select an escalation policy:", choices=choices)
    selected_id = _inquire(prompt)
    if selected_id is None:
        return None
    return next(p for p in policies if p["id"] == selected_id)


def user_action_menu() -> str:
    prompt = inquirer.select(
        message="Action:",
        choices=[
            {"name": "Edit existing rule", "value": "edit"},
            {"name": "Add new rule", "value": "add"},
            {"name": "Delete rule", "value": "delete"},
            {"name": "← Back", "value": "back"},
        ],
    )
    return _inquire(prompt)


def select_notification_rule(rules: list[dict]) -> Optional[dict]:
    choices = []
    for r in rules:
        cm = r.get("contact_method", {})
        method_type = _METHOD_TYPE_LABELS.get(cm.get("type", ""), cm.get("type", ""))
        label = f"{r['urgency']} | {method_type} | {r['start_delay_in_minutes']} min delay"
        choices.append({"name": label, "value": r["id"]})
    choices.append({"name": "← Back", "value": None})
    prompt = inquirer.select(message="Select a rule:", choices=choices)
    selected_id = _inquire(prompt)
    if selected_id is None:
        return None
    return next(r for r in rules if r["id"] == selected_id)


def select_contact_method(methods: list[dict]) -> Optional[dict]:
    choices = []
    for m in methods:
        method_type = _METHOD_TYPE_LABELS.get(m.get("type", ""), m.get("type", ""))
        label = f"{method_type}: {m.get('address', '')}"
        choices.append({"name": label, "value": m["id"]})
    choices.append({"name": "← Back", "value": None})
    prompt = inquirer.select(message="Select a contact method:", choices=choices)
    selected_id = _inquire(prompt)
    if selected_id is None:
        return None
    return next(m for m in methods if m["id"] == selected_id)


def prompt_urgency() -> str:
    prompt = inquirer.select(
        message="Urgency level:",
        choices=[
            {"name": "High", "value": "high"},
            {"name": "Low", "value": "low"},
            {"name": "Both (high and low)", "value": "high_and_low"},
        ],
    )
    return _inquire(prompt)


def prompt_delay() -> int:
    prompt = inquirer.select(
        message="Delay before notification (minutes):",
        choices=[
            {"name": "0 (immediate)", "value": "0"},
            {"name": "1 minute", "value": "1"},
            {"name": "2 minutes", "value": "2"},
            {"name": "3 minutes", "value": "3"},
            {"name": "5 minutes", "value": "5"},
            {"name": "10 minutes", "value": "10"},
            {"name": "15 minutes", "value": "15"},
            {"name": "30 minutes", "value": "30"},
        ],
    )
    return int(_inquire(prompt))


def confirm_action(message: str) -> bool:
    prompt = inquirer.confirm(message=message, default=False)
    return _inquire(prompt)


def bulk_scope_menu() -> str:
    prompt = inquirer.select(
        message="Apply rules to:",
        choices=[
            {"name": "Users in a specific team", "value": "team"},
            {"name": "Users in an escalation policy", "value": "escalation_policy"},
            {"name": "All users (org-wide)", "value": "org_wide"},
        ],
    )
    return _inquire(prompt)


def bulk_action_menu(user_name: str) -> str:
    prompt = inquirer.select(
        message=f"Action for {user_name}:",
        choices=[
            {"name": "Skip (leave as-is)", "value": "skip"},
            {"name": "Keep current rules", "value": "keep"},
            {"name": "Add new rule alongside existing", "value": "combine"},
            {"name": "Replace rules of same urgency", "value": "replace"},
        ],
    )
    return _inquire(prompt)


def select_contact_method_type() -> str:
    prompt = inquirer.select(
        message="Contact method type:",
        choices=[
            {"name": "SMS", "value": "sms_contact_method"},
            {"name": "Phone call", "value": "phone_contact_method"},
            {"name": "Email", "value": "email_contact_method"},
            {"name": "Push notification", "value": "push_notification_contact_method"},
        ],
    )
    return _inquire(prompt)
