"""PagerDuty REST API client with pagination and retry."""

import time
from typing import Optional
import httpx


class PagerDutyClient:
    def __init__(self, api_token: str):
        self.token = api_token
        self.base_url = "https://api.pagerduty.com"
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Token token={api_token}",
                "Content-Type": "application/json",
                "Accept": "application/vnd.pagerduty+json;version=2",
            },
            timeout=30.0,
        )

    def _paginate(self, endpoint: str, resource_key: str, params: Optional[dict] = None) -> list[dict]:
        results = []
        offset = 0
        limit = 100
        while True:
            request_params = {"limit": limit, "offset": offset}
            if params:
                request_params.update(params)
            response = self._request("GET", endpoint, params=request_params)
            data = response.json()
            results.extend(data.get(resource_key, []))
            if not data.get("more", False):
                break
            offset += limit
        return results

    def _request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        max_retries = 3
        last_exception = None
        for attempt in range(max_retries):
            try:
                response = self._client.request(method, endpoint, **kwargs)
                response.raise_for_status()
                return response
            except httpx.HTTPError as e:
                if hasattr(e, 'response') and e.response.status_code == 429:
                    last_exception = e
                    retry_after = int(e.response.headers.get("Retry-After", 2 ** attempt))
                    time.sleep(retry_after)
                    continue
                raise
        if last_exception:
            raise last_exception

    def list_users(self) -> list[dict]:
        return self._paginate("/users", "users")

    def get_user(self, user_id: str) -> dict:
        response = self._request("GET", f"/users/{user_id}")
        return response.json()["user"]

    def list_teams(self) -> list[dict]:
        return self._paginate("/teams", "teams")

    def list_team_members(self, team_id: str) -> list[dict]:
        return self._paginate(f"/teams/{team_id}/members", "members")

    def list_escalation_policies(self) -> list[dict]:
        return self._paginate("/escalation_policies", "escalation_policies")

    def get_contact_methods(self, user_id: str) -> list[dict]:
        return self._paginate(f"/users/{user_id}/contact_methods", "contact_methods")

    def get_notification_rules(self, user_id: str) -> list[dict]:
        return self._paginate(f"/users/{user_id}/notification_rules", "notification_rules")

    def create_notification_rule(self, user_id: str, rule: dict) -> dict:
        response = self._request("POST", f"/users/{user_id}/notification_rules", json=rule)
        return response.json()["notification_rule"]

    def update_notification_rule(self, user_id: str, rule_id: str, rule: dict) -> dict:
        response = self._request("PUT", f"/users/{user_id}/notification_rules/{rule_id}", json=rule)
        return response.json()["notification_rule"]

    def delete_notification_rule(self, user_id: str, rule_id: str) -> None:
        self._request("DELETE", f"/users/{user_id}/notification_rules/{rule_id}")

    def create_contact_method(self, user_id: str, method: dict) -> dict:
        response = self._request("POST", f"/users/{user_id}/contact_methods", json=method)
        return response.json()["contact_method"]

    def validate_token(self) -> bool:
        """Lightweight token validation—checks if token has access to the API."""
        try:
            response = self._request("GET", "/users", params={"limit": 1})
            return response.status_code == 200
        except Exception:
            return False
