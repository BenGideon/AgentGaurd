from __future__ import annotations

from typing import Any

import requests


class AgentGuardError(Exception):
    def __init__(self, status_code: int, response_text: str):
        self.status_code = status_code
        self.response_text = response_text
        super().__init__(f"AgentGuard request failed ({status_code}): {response_text}")


class AgentGuard:
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = 30

    def list_actions(self) -> Any:
        return self._request("GET", "/actions")

    def call_action(self, action: str, input: dict) -> Any:
        return self._request(
            "POST",
            "/actions/call",
            json={
                "action": action,
                "input": input,
            },
            use_agent_key=True,
        )

    def list_tools(self) -> Any:
        return self._request("POST", "/mcp/tools/list", use_agent_key=True)

    def call_tool(self, name: str, arguments: dict) -> Any:
        return self._request(
            "POST",
            "/mcp/tools/call",
            json={
                "name": name,
                "arguments": arguments,
            },
            use_agent_key=True,
        )

    def get_logs(self) -> Any:
        return self._request("GET", "/logs")

    def _request(
        self,
        method: str,
        path: str,
        json: dict | None = None,
        use_agent_key: bool = False,
    ) -> Any:
        headers = {}
        if use_agent_key:
            headers["x-agent-key"] = self.api_key

        response = requests.request(
            method,
            f"{self.base_url}{path}",
            headers=headers,
            json=json,
            timeout=self.timeout,
        )

        if not 200 <= response.status_code < 300:
            raise AgentGuardError(response.status_code, response.text)

        if not response.content:
            return None

        return response.json()
