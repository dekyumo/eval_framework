"""HTTP client for the eval workbench REST API (used by the MCP server)."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from src.eval_workbench.services.errors import ServiceError


class ApiClient:
    def __init__(self, base_url: str):
        if not base_url:
            raise ServiceError("EVAL_WORKBENCH_API_URL is required", 400)
        self.base_url = base_url.rstrip("/")

    def get(self, path: str, *, params: dict[str, str] | None = None) -> Any:
        return self._request("GET", path, params=params)

    def post(self, path: str, *, body: dict[str, Any] | None = None) -> Any:
        return self._request("POST", path, body=body)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"error": raw or exc.reason}
            message = payload.get("error", raw or exc.reason)
            raise ServiceError(str(message), exc.code) from exc
        except TimeoutError as exc:
            raise ServiceError(
                f"Eval workbench API timed out at {self.base_url}{path}",
                504,
            ) from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise ServiceError(
                    f"Eval workbench API timed out at {self.base_url}{path}",
                    504,
                ) from exc
            raise ServiceError(
                f"Cannot reach eval workbench API at {self.base_url}: {exc.reason}",
                503,
            ) from exc
        if not raw:
            return None
        return json.loads(raw)
