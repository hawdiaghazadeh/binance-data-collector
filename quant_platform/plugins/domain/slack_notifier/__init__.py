"""Reference domain plugin: slack_notifier."""

from __future__ import annotations

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("slack_notifier", "platform.notifications")


class SlackNotification:

    def send(self, message: str, *, channel: str = "default") -> bool:
        return True


def factory(**kwargs) -> SlackNotification:
    return SlackNotification()


attach_factory_metadata(factory, PLUGIN_METADATA)
