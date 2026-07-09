"""Tests for tp_sleeve.executor — reconcile reuse (roll) + gated dry/apply."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from ctrader_execution.volume_codec import lots_to_proto_volume_for_lot_size
from carry_sleeve.executor import ORDER_GATE_ENV as CARRY_ORDER_GATE_ENV
from tp_sleeve.executor import (
    ORDER_GATE_VALUE,
    TP_ORDER_GATE_ENV,
    TpExecutor,
    order_gate_open,
    plan_reconcile,
)
from tp_sleeve.signal import compute_target

_GATE_ENV = TP_ORDER_GATE_ENV


@dataclass
class _Pos:
    symbol: str
    position_id: str
    direction: str
    volume_lots: float
    protocol_volume: int = 0


class _FakeOM:
    """Minimal order-manager double: records submit/close calls."""

    def __init__(self) -> None:
        self.submitted: list = []
        self.closed: list = []

    def submit_order(self, command):
        self.submitted.append(command)

        class _Rec:
            order_ref = "ref123"

        return _Rec()

    def close_position(self, position_id, volume_lots, *, protocol_volume=0):
        self.closed.append((position_id, volume_lots, protocol_volume))


def _long_target(symbol: str, lots: float):
    t = compute_target(symbol, 1, as_of="2026-02")
    t.positions[0].lots = lots
    return t


def test_open_when_flat_account():
    plan = plan_reconcile(_long_target("UST10Y_H6", 1.0), [])
    assert not plan.closes
    assert len(plan.opens) == 1
    assert (plan.opens[0].symbol, plan.opens[0].side, plan.opens[0].lots) == (
        "UST10Y_H6",
        "BUY",
        1.0,
    )


def test_flat_target_closes_held_position():
    held = [_Pos("UST10Y_H6", "p1", "BUY", 1.0)]
    plan = plan_reconcile(compute_target("UST10Y_H6", 0), held)
    assert len(plan.closes) == 1 and plan.closes[0].symbol == "UST10Y_H6"
    assert not plan.opens
    assert plan.decisions[0].action == "CLOSE"


def test_quarterly_roll_closes_old_opens_new():
    # Held the March contract; front rolled to June -> close H6, open M6.
    held = [_Pos("UST10Y_H6", "p1", "BUY", 1.0)]
    plan = plan_reconcile(_long_target("UST10Y_M6", 1.0), held)
    assert [c.symbol for c in plan.closes] == ["UST10Y_H6"]
    assert [o.symbol for o in plan.opens] == ["UST10Y_M6"]


def test_noop_when_already_holding_front():
    held = [_Pos("UST10Y_H6", "p1", "BUY", 1.0)]
    plan = plan_reconcile(_long_target("UST10Y_H6", 1.0), held)
    assert not plan.closes and not plan.opens
    assert plan.decisions[0].action == "NOOP"


def test_dry_apply_sends_nothing():
    plan = plan_reconcile(_long_target("UST10Y_H6", 1.0), [])
    out = TpExecutor(order_manager=None).apply(plan, allow_orders=False)
    assert out and all(op["sent"] is False for op in out)


def test_apply_requires_open_gate(monkeypatch):
    monkeypatch.delenv(TP_ORDER_GATE_ENV, raising=False)
    monkeypatch.delenv("FXAIEA_ALLOW_CTRADER_ORDERS", raising=False)
    plan = plan_reconcile(_long_target("UST10Y_H6", 1.0), [])
    with pytest.raises(PermissionError):
        TpExecutor(order_manager=None).apply(plan, allow_orders=True)


def test_order_gate_tp_canonical():
    assert order_gate_open({TP_ORDER_GATE_ENV: ORDER_GATE_VALUE}) is True


def test_order_gate_rejects_legacy_v7_name():
    assert order_gate_open({"FXAIEA_ALLOW_CTRADER_ORDERS": ORDER_GATE_VALUE}) is False


def test_order_gate_rejects_carry_key():
    assert order_gate_open({CARRY_ORDER_GATE_ENV: ORDER_GATE_VALUE}) is False


def test_lots_to_proto_volume_for_lot_size():
    # broker lotSize 10_000 (UST10Y) -> volume = round(lots * lotSize)
    assert lots_to_proto_volume_for_lot_size(1.0, 10_000) == 10_000
    assert lots_to_proto_volume_for_lot_size(0.03, 10_000) == 300
    # FX scale parity: lotSize 10_000_000, 0.01 lot -> 100_000 (= lots_to_proto_volume)
    assert lots_to_proto_volume_for_lot_size(0.01, 10_000_000) == 100_000
    # guard: non-positive lotSize -> 0 (caller must fail-fast, not FX-fallback)
    assert lots_to_proto_volume_for_lot_size(0.03, 0) == 0


def test_apply_open_sends_symbol_specific_protocol_volume(monkeypatch):
    monkeypatch.setenv(_GATE_ENV, ORDER_GATE_VALUE)
    om = _FakeOM()
    plan = plan_reconcile(_long_target("UST10Y_H6", 0.03), [])
    ex = TpExecutor(om, lot_size_resolver={"UST10Y_H6": 10_000}.get)
    out = ex.apply(plan, allow_orders=True)
    assert len(om.submitted) == 1
    cmd = om.submitted[0]
    # 0.03 lot * 10_000 lotSize = 300 broker units (NOT FX 300_000)
    assert cmd.protocol_volume == 300
    assert cmd.volume_lots == 0.03
    assert cmd.metadata["sleeve"] == "tp"
    assert out[0]["protocol_volume"] == 300


def test_apply_open_fail_fast_when_lot_size_unknown(monkeypatch):
    monkeypatch.setenv(_GATE_ENV, ORDER_GATE_VALUE)
    om = _FakeOM()
    plan = plan_reconcile(_long_target("UST10Y_H6", 0.03), [])
    # no resolver -> must refuse (would 1000x over-size via FX fallback)
    with pytest.raises(ValueError, match="lotSize"):
        TpExecutor(om).apply(plan, allow_orders=True)
    assert not om.submitted


def test_apply_roll_close_uses_snapshot_volume(monkeypatch):
    monkeypatch.setenv(_GATE_ENV, ORDER_GATE_VALUE)
    om = _FakeOM()
    held = [_Pos("UST10Y_H6", "p1", "BUY", 0.03, protocol_volume=300)]
    plan = plan_reconcile(_long_target("UST10Y_M6", 0.03), held)
    ex = TpExecutor(om, lot_size_resolver={"UST10Y_M6": 10_000}.get)
    ex.apply(plan, allow_orders=True)
    # close uses the live snapshot's broker protocol_volume (300), not recomputed
    assert om.closed == [("p1", 0.03, 300)]
    # open sizes the NEW front from lotSize
    assert om.submitted[0].symbol == "UST10Y_M6"
    assert om.submitted[0].protocol_volume == 300
