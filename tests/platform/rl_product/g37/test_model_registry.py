"""G37 — model registry."""

from __future__ import annotations

from quant_platform.rl_product.inference.model_registry import ModelRegistry


def test_model_registry_roundtrip():
    registry = ModelRegistry()
    record = registry.register(
        "btc_v1",
        "/tmp/policy.pt",
        metadata={"graph_schema_hash": "abc123", "schema_version": "1.0"},
    )
    assert record.model_id == "btc_v1"
    assert registry.get("btc_v1").graph_schema_hash == "abc123"
    assert len(registry.list_models()) == 1
    registry.remove("btc_v1")
    assert registry.list_models() == []
