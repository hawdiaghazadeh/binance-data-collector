"""Notification delivery helpers (Phase 20)."""

from __future__ import annotations

from typing import Any, Protocol

import httpx


class HttpPoster(Protocol):
    def post(self, url: str, *, json: dict[str, Any]) -> httpx.Response: ...


def build_slack_payload(message: str, *, channel: str = "default") -> dict[str, Any]:
    return {
        "text": message,
        "channel": channel,
    }


def send_slack_message(
    message: str,
    *,
    webhook_url: str | None = None,
    channel: str = "default",
    client: httpx.Client | None = None,
) -> bool:
    if not webhook_url:
        return True

    owns_client = client is None
    http = client or httpx.Client(timeout=10.0)
    try:
        response = http.post(webhook_url, json=build_slack_payload(message, channel=channel))
        response.raise_for_status()
        return True
    except httpx.HTTPError:
        return False
    finally:
        if owns_client:
            http.close()
