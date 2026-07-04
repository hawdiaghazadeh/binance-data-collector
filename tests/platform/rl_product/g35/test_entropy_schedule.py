"""G35 — entropy schedule."""

from __future__ import annotations

import pytest

from quant_platform.rl_product.training.entropy_schedule import EntropySchedule


def test_entropy_annealing():
    sched = EntropySchedule(start=0.01, end=0.001, min_coef=0.0005, total_steps=100)
    assert sched.coef_at(0) == 0.01
    mid = sched.coef_at(50)
    assert 0.001 < mid < 0.01
    assert sched.coef_at(100) == pytest.approx(0.001)
    assert sched.coef_at(200) >= 0.0005
