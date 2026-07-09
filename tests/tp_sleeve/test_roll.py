"""Tests for tp_sleeve.roll — dated UST10Y future selection + quarterly roll."""

from __future__ import annotations

from datetime import date

import pytest

from tp_sleeve.roll import (
    contract_symbol,
    needs_roll,
    parse_contract,
    select_front_contract,
    upcoming_quarterly,
)


def test_contract_symbol_quarterly():
    assert contract_symbol(2026, 3) == "UST10Y_H6"
    assert contract_symbol(2026, 12) == "UST10Y_Z6"


def test_contract_symbol_rejects_non_quarterly():
    with pytest.raises(ValueError):
        contract_symbol(2026, 4)


def test_parse_contract_roundtrip():
    assert parse_contract("UST10Y_H6") == (2026, 3)
    assert parse_contract("UST10Y_Z6") == (2026, 12)
    y, m = parse_contract(contract_symbol(2027, 9))
    assert (y, m) == (2027, 9)


def test_parse_contract_rejects_bad_inputs():
    for bad in ("EURUSD", "UST10Y_", "UST10Y_X6", "UST10Y_HZ"):
        with pytest.raises(ValueError):
            parse_contract(bad)


def test_upcoming_quarterly_from_midmonth():
    ups = upcoming_quarterly(date(2026, 1, 15), count=4)
    assert ups == [(2026, 3), (2026, 6), (2026, 9), (2026, 12)]


def test_select_front_far_from_delivery():
    # Mid-Jan: March delivery is ~45d away (> 7d buffer) -> front is H6.
    assert select_front_contract(date(2026, 1, 15)) == "UST10Y_H6"


def test_select_front_rolls_within_buffer():
    # Feb 25: March 1 is 4 days away (<= 7d buffer) -> rolled to June (M6).
    assert select_front_contract(date(2026, 2, 25)) == "UST10Y_M6"


def test_select_front_crosses_year_boundary():
    # Late Dec 2026: Dec delivery already started -> next is March 2027 (H7).
    assert select_front_contract(date(2026, 12, 28)) == "UST10Y_H7"


def test_needs_roll():
    assert needs_roll(None, "UST10Y_H6") is False
    assert needs_roll("UST10Y_H6", "UST10Y_H6") is False
    assert needs_roll("UST10Y_H6", "UST10Y_M6") is True
