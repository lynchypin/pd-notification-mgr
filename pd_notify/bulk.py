"""Bulk notification rule operations and compliance reporting."""

from pd_notify.api import PagerDutyClient


def build_compliance_report(
    users: list[dict],
    client: PagerDutyClient,
    method_type: str,
    urgency: str,
    delay: int,
) -> list[dict]:
    report = []
    for user in users:
        user_id = user["id"]
        contact_methods = client.get_contact_methods(user_id)
        notification_rules = client.get_notification_rules(user_id)

        has_method_type = any(cm["type"] == method_type for cm in contact_methods)
        matching_rules = [
            r for r in notification_rules
            if r["contact_method"]["type"] == method_type and r["urgency"] == urgency
        ]

        if not has_method_type:
            report.append({
                "user": user,
                "name": user.get("name", user_id),
                "status": "missing",
                "detail": f"No {_type_label(method_type)} contact method configured",
                "matching_rules": [],
                "contact_methods": contact_methods,
            })
        elif any(r["start_delay_in_minutes"] == delay for r in matching_rules):
            report.append({
                "user": user,
                "name": user.get("name", user_id),
                "status": "match",
                "detail": f"Already has {_type_label(method_type)} rule at {delay} min",
                "matching_rules": matching_rules,
                "contact_methods": contact_methods,
            })
        elif matching_rules:
            current_delays = [r["start_delay_in_minutes"] for r in matching_rules]
            report.append({
                "user": user,
                "name": user.get("name", user_id),
                "status": "partial",
                "detail": f"Has {_type_label(method_type)} but timing differs ({current_delays} min)",
                "matching_rules": matching_rules,
                "contact_methods": contact_methods,
            })
        else:
            report.append({
                "user": user,
                "name": user.get("name", user_id),
                "status": "partial",
                "detail": f"Has {_type_label(method_type)} contact method but no {urgency} urgency rule",
                "matching_rules": [],
                "contact_methods": contact_methods,
            })

    return report


def apply_bulk_action(
    client: PagerDutyClient,
    user: dict,
    action: str,
    method_type: str,
    urgency: str,
    delay: int,
    contact_methods: list[dict],
    existing_rules: list[dict],
) -> str:
    user_id = user["id"]

    if action == "skip" or action == "keep":
        return f"Skipped {user.get('name', user_id)}"

    target_cm = next(
        (cm for cm in contact_methods if cm["type"] == method_type),
        None,
    )
    if not target_cm:
        return f"No {_type_label(method_type)} contact method available for {user.get('name', user_id)}"

    if action == "replace":
        rules_to_delete = [r for r in existing_rules if r["urgency"] == urgency]
        for rule in rules_to_delete:
            client.delete_notification_rule(user_id, rule["id"])

    rule_payload = {
        "notification_rule": {
            "type": "assignment_notification_rule",
            "urgency": urgency,
            "start_delay_in_minutes": delay,
            "contact_method": {
                "id": target_cm["id"],
                "type": target_cm["type"],
            },
        }
    }
    client.create_notification_rule(user_id, rule_payload)

    if action == "replace":
        return f"Replaced {urgency} rules and added new rule for {user.get('name', user_id)}"
    return f"Added new rule for {user.get('name', user_id)}"


def _type_label(method_type: str) -> str:
    labels = {
        "email_contact_method": "Email",
        "sms_contact_method": "SMS",
        "phone_contact_method": "Phone",
        "push_notification_contact_method": "Push",
    }
    return labels.get(method_type, method_type)
