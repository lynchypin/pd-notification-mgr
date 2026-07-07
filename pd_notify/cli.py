# pd_notify/cli.py
"""CLI entry point — main menu loop and flow orchestration."""

import sys

from pd_notify.api import PagerDutyClient
from pd_notify import menus, display
from pd_notify.bulk import build_compliance_report, apply_bulk_action


def main() -> None:
    display.print_header()

    token = menus.prompt_api_token()
    if not token:
        display.print_error("No API token provided. Exiting.")
        sys.exit(1)

    client = PagerDutyClient(token)

    if not client.validate_token():
        display.print_error("Invalid API token or insufficient permissions.")
        display.print_error("Ensure your token has full access (admin) permissions.")
        sys.exit(1)

    while True:
        choice = menus.main_menu()

        if choice == "exit":
            break
        elif choice == "all_users":
            _handle_all_users(client)
        elif choice == "by_team":
            _handle_by_team(client)
        elif choice == "bulk_select":
            _handle_bulk_select(client)
        elif choice == "bulk":
            _handle_bulk(client)


def _handle_all_users(client: PagerDutyClient) -> None:
    users = client.list_users()
    if not users:
        display.print_error("No users found.")
        return
    _user_selection_loop(client, users)


def _handle_by_team(client: PagerDutyClient) -> None:
    teams = client.list_teams()
    if not teams:
        display.print_error("No teams found.")
        return

    team = menus.select_team(teams)
    if not team:
        return

    members = client.list_team_members(team["id"])
    user_refs = [m["user"] for m in members if "user" in m]
    if not user_refs:
        display.print_error(f"No members found in team '{team.get('name', team['id'])}'.")
        return

    users = [client.get_user(ref["id"]) for ref in user_refs]
    _user_selection_loop(client, users)


def _user_selection_loop(client: PagerDutyClient, users: list[dict]) -> None:
    while True:
        display.render_users_table(users)
        user = menus.select_user(users)
        if not user:
            break
        _handle_user_detail(client, user)


def _handle_user_detail(client: PagerDutyClient, user: dict) -> None:
    contact_methods = client.get_contact_methods(user["id"])
    notification_rules = client.get_notification_rules(user["id"])

    display.render_notification_rules(notification_rules, contact_methods)
    display.render_contact_methods(contact_methods)

    while True:
        action = menus.user_action_menu()

        if action == "back":
            break
        elif action == "edit":
            _edit_rule(client, user, notification_rules, contact_methods)
            notification_rules = client.get_notification_rules(user["id"])
        elif action == "add":
            _add_rule(client, user, contact_methods)
            notification_rules = client.get_notification_rules(user["id"])
        elif action == "delete":
            _delete_rule(client, user, notification_rules)
            notification_rules = client.get_notification_rules(user["id"])


def _edit_rule(
    client: PagerDutyClient, user: dict, rules: list[dict], contact_methods: list[dict]
) -> None:
    if not rules:
        display.print_error("No rules to edit.")
        return

    rule = menus.select_notification_rule(rules)
    if not rule:
        return

    contact_method = menus.select_contact_method(contact_methods)
    if not contact_method:
        return

    urgency = menus.prompt_urgency()
    delay = menus.prompt_delay()

    payload = {
        "notification_rule": {
            "type": "assignment_notification_rule",
            "urgency": urgency,
            "start_delay_in_minutes": delay,
            "contact_method": {
                "id": contact_method["id"],
                "type": contact_method["type"],
            },
        }
    }

    client.update_notification_rule(user["id"], rule["id"], payload)
    display.print_success(f"Updated rule for {user.get('name', user['id'])}")


def _add_rule(client: PagerDutyClient, user: dict, contact_methods: list[dict]) -> None:
    if not contact_methods:
        display.print_error("No contact methods available. Add a contact method first.")
        return

    contact_method = menus.select_contact_method(contact_methods)
    if not contact_method:
        return

    urgency = menus.prompt_urgency()
    delay = menus.prompt_delay()

    urgencies = ["high", "low"] if urgency == "high_and_low" else [urgency]
    for urg in urgencies:
        payload = {
            "notification_rule": {
                "type": "assignment_notification_rule",
                "urgency": urg,
                "start_delay_in_minutes": delay,
                "contact_method": {
                    "id": contact_method["id"],
                    "type": contact_method["type"],
                },
            }
        }
        client.create_notification_rule(user["id"], payload)

    display.print_success(f"Added notification rule(s) for {user.get('name', user['id'])}")


def _delete_rule(client: PagerDutyClient, user: dict, rules: list[dict]) -> None:
    if not rules:
        display.print_error("No rules to delete.")
        return

    rule = menus.select_notification_rule(rules)
    if not rule:
        return

    if menus.confirm_action(f"Delete this notification rule?"):
        client.delete_notification_rule(user["id"], rule["id"])
        display.print_success("Rule deleted.")


def _handle_bulk_select(client: PagerDutyClient) -> None:
    scope = menus.bulk_select_scope_menu()

    if scope == "team":
        teams = client.list_teams()
        if not teams:
            display.print_error("No teams found.")
            return
        team = menus.select_team(teams)
        if not team:
            return
        members = client.list_team_members(team["id"])
        user_refs = [m["user"] for m in members if "user" in m]
        users = [client.get_user(ref["id"]) for ref in user_refs]
    else:
        users = client.list_users()

    if not users:
        display.print_error("No users found.")
        return

    display.render_users_table(users)
    selected_users = menus.select_users_multi(users)
    if not selected_users:
        return

    method_type = menus.select_contact_method_type()
    urgency = menus.prompt_urgency()
    delay = menus.prompt_delay()

    urgencies = ["high", "low"] if urgency == "high_and_low" else [urgency]

    for urg in urgencies:
        report = build_compliance_report(selected_users, client, method_type, urg, delay)
        display.render_compliance_report([
            {"name": r["name"], "status": r["status"], "detail": r["detail"]}
            for r in report
        ])

        non_match = [r for r in report if r["status"] != "match"]
        if not non_match:
            display.print_success(f"All selected users already comply for {urg} urgency!")
            continue

        if menus.confirm_action(f"Apply changes to {len(non_match)} user(s) for {urg} urgency?"):
            for entry in non_match:
                action = menus.bulk_action_menu(entry["name"])
                result = apply_bulk_action(
                    client, entry["user"], action, method_type, urg, delay,
                    entry["contact_methods"], entry["matching_rules"],
                )
                display.print_success(result)


def _handle_bulk(client: PagerDutyClient) -> None:
    scope = menus.bulk_scope_menu()

    if scope == "team":
        teams = client.list_teams()
        if not teams:
            display.print_error("No teams found.")
            return
        team = menus.select_team(teams)
        if not team:
            return
        members = client.list_team_members(team["id"])
        user_refs = [m["user"] for m in members if "user" in m]
        users = [client.get_user(ref["id"]) for ref in user_refs]
    elif scope == "escalation_policy":
        policies = client.list_escalation_policies()
        if not policies:
            display.print_error("No escalation policies found.")
            return
        policy = menus.select_escalation_policy(policies)
        if not policy:
            return
        user_ids = set()
        for target in policy.get("escalation_rules", []):
            for t in target.get("targets", []):
                if t.get("type") == "user_reference":
                    user_ids.add(t["id"])
        users = [client.get_user(uid) for uid in user_ids]
    else:
        users = client.list_users()

    if not users:
        display.print_error("No users found in selected scope.")
        return

    method_type = menus.select_contact_method_type()
    urgency = menus.prompt_urgency()
    delay = menus.prompt_delay()

    urgencies = ["high", "low"] if urgency == "high_and_low" else [urgency]

    for urg in urgencies:
        report = build_compliance_report(users, client, method_type, urg, delay)
        display.render_compliance_report([
            {"name": r["name"], "status": r["status"], "detail": r["detail"]}
            for r in report
        ])

        non_match = [r for r in report if r["status"] != "match"]
        if not non_match:
            display.print_success(f"All users already comply for {urg} urgency!")
            continue

        if menus.confirm_action(f"Apply changes to {len(non_match)} user(s) for {urg} urgency?"):
            for entry in non_match:
                action = menus.bulk_action_menu(entry["name"])
                result = apply_bulk_action(
                    client, entry["user"], action, method_type, urg, delay,
                    entry["contact_methods"], entry["matching_rules"],
                )
                display.print_success(result)


if __name__ == "__main__":
    main()
