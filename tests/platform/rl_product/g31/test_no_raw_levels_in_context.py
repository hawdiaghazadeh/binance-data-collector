"""G31 — context path must not carry raw price levels."""

from __future__ import annotations

import pytest

from quant_platform.rl_product.perception._helpers import HintEnvelope, make_hint


def test_hint_envelope_rejects_raw_level_metadata():
    with pytest.raises(ValueError, match="raw level"):
        HintEnvelope(family="smc", name="bos_p", value=0.5, metadata={"level": 42000.0})


def test_hint_envelope_rejects_large_price_metadata():
    with pytest.raises(ValueError, match="raw price"):
        HintEnvelope(family="rtm", name="sd_strength", value=0.5, metadata={"zone": 50000})


def test_make_hint_allows_safe_metadata():
    env = make_hint("ict", "session_p", 0.8, session="london")
    assert env.value == 0.8
    assert env.metadata["session"] == "london"
