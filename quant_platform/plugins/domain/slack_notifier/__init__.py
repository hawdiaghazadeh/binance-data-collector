"""Slack notification plugin (Phase 20)."""

from __future__ import annotations

from typing import Any

import httpx

from quant_platform.core.plugin import PluginMetadata
from quant_platform.observability.notification import send_slack_message

PLUGIN_METADATA = PluginMetadata(
    name="slack_notifier",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Slack webhook notification delivery",
    input_types=["message"],
    output_types=["notification_result"],
    registry_group="platform.notifications",
)


class SlackNotification:
    def __init__(
        self,
        *,
        webhook_url: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self._webhook_url = webhook_url
        self._client = client

    def send(self, message: str, *, channel: str = "default") -> bool:
        return send_slack_message(
            message,
            webhook_url=self._webhook_url,
            channel=channel,
            client=self._client,
        )


def factory(
    *,
    webhook_url: str | None = None,
    client: httpx.Client | None = None,
    config: dict | None = None,
    **kwargs,
) -> SlackNotification:
    if config:
        webhook_url = config.get("webhook_url", webhook_url)
        client = config.get("client", client)
    return SlackNotification(webhook_url=webhook_url, client=client)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
