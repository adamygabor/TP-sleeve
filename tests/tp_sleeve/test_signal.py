"""Tests for tp_sleeve.signal — slope-gated long/flat term-premium signal (SoT)."""

from __future__ import annotations

from datetime import date

import pytest

from tp_sleeve.signal import (
    compute_target,
    exposure_from_slope,
    month_end_slopes,
    prior_month_end_slope,
)


def test_exposure_long_when_slope_positive():
    assert exposure_from_slope(0.5) == 1


def test_exposure_flat_when_slope_negative():
    assert exposure_from_slope(-0.1) == 0


def test_exposure_long_at_zero_boundary():
    # floor is inclusive (>= 0), matching bond_term_premium_gate.SLOPE_FLOOR.
    assert exposure_from_slope(0.0) == 1


def test_compute_target_long_single_leg():
    t = compute_target("UST10Y_H6", 1, as_of="2026-02")
    assert len(t.positions) == 1
    p = t.positions[0]
    assert (p.symbol, p.side, p.weight, p.leg) == ("UST10Y_H6", "BUY", 1.0, "long")
    assert t.longs == ["UST10Y"] and t.shorts == []


def test_compute_target_flat_is_empty():
    t = compute_target("UST10Y_H6", 0, as_of="2026-02")
    assert t.positions == [] and t.longs == []


def test_compute_target_rejects_bad_exposure():
    with pytest.raises(ValueError):
        compute_target("UST10Y_H6", 2)


def test_compute_target_long_requires_contract():
    with pytest.raises(ValueError):
        compute_target("", 1)


def _row(d: date, dgs10: float, dgs2: float) -> dict:
    return {"date": d, "dgs10": dgs10, "dgs2": dgs2}


def test_month_end_slopes_uses_last_day():
    rows = [
        _row(date(2026, 1, 5), 4.0, 4.2),  # earlier Jan
        _row(date(2026, 1, 30), 4.3, 4.1),  # Jan month-end -> +0.2
        _row(date(2026, 2, 27), 4.5, 4.0),  # Feb month-end -> +0.5
    ]
    s = month_end_slopes(rows)
    assert s[(2026, 1)] == pytest.approx(0.2)
    assert s[(2026, 2)] == pytest.approx(0.5)


def test_prior_month_end_slope_lag():
    rows = [
        _row(date(2026, 1, 30), 4.3, 4.5),  # Jan end -> -0.2 (inverted)
        _row(date(2026, 2, 27), 4.5, 4.0),  # Feb end -> +0.5
    ]
    # March rebalance uses February's month-end slope.
    assert prior_month_end_slope(rows, "2026-03") == pytest.approx(0.5)
    # February rebalance uses January's month-end slope.
    assert prior_month_end_slope(rows, "2026-02") == pytest.approx(-0.2)


def test_prior_month_end_slope_year_boundary_and_missing():
    rows = [_row(date(2025, 12, 31), 4.4, 4.0)]  # Dec 2025 end -> +0.4
    assert prior_month_end_slope(rows, "2026-01") == pytest.approx(0.4)
    assert prior_month_end_slope(rows, "2027-06") is None
