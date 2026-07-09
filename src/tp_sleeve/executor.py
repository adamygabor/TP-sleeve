"""tp_sleeve / executor — Phase 2 reconcile for the single-instrument TP sleeve.

Reuses the validated, sleeve-agnostic CLOSE-FIRST planner
(``carry_sleeve.executor.plan_reconcile`` only — no shared order gate).

Order gate is **local**: ``FXAIEA_TP_ALLOW_CTRADER_ORDERS`` (not carry ``FXCARRY_*``,
not legacy v7 ``FXAIEA_ALLOW_*``). The quarterly roll needs no special code: a changed
front contract appears as CLOSE(old) + OPEN(new) in the reconcile plan.

With ``allow_orders=False`` (default) this is a pure dry plan (no broker calls).
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import Any

from carry_sleeve.executor import ReconcilePlan, plan_reconcile
from ctrader_execution.volume_codec import lots_to_proto_volume_for_lot_size

TP_ORDER_GATE_ENV = "FXAIEA_TP_ALLOW_CTRADER_ORDERS"
ORDER_GATE_VALUE = "I_UNDERSTAND_THIS_CAN_PLACE_BROKER_ORDERS"

__all__ = [
    "TP_ORDER_GATE_ENV",
    "ORDER_GATE_VALUE",
    "plan_reconcile",
    "order_gate_open",
    "TpExecutor",
]


def order_gate_open(env: dict[str, str] | None = None) -> bool:
    """TP sleeve gate — ``FXAIEA_TP_ALLOW_CTRADER_ORDERS`` only."""
    src = env if env is not None else os.environ
    return src.get(TP_ORDER_GATE_ENV, "") == ORDER_GATE_VALUE


class TpExecutor:
    """Apply a ReconcilePlan via CTraderOrderManager (CLOSE-FIRST, gated, tp meta).

    `order_manager` must expose `close_position(position_id, volume_lots,
    protocol_volume=...)` and `submit_order(OrderCommand)` (same contract as the
    carry executor).

    The dated UST10Y future CFD has a broker `lotSize` (10_000) ≠ the FX scale
    (10_000_000) the default `lots_to_proto_volume` is hardcoded to. To avoid a
    1000× over-sizing on OPEN orders, `lot_size_resolver(symbol)` must return the
    broker `ProtoOASymbol.lotSize`; the executor then sends an explicit
    `protocol_volume = round(lots * lotSize)`. CLOSE orders already carry the
    broker-correct `protocol_volume` from the live position snapshot.
    """

    def __init__(
        self,
        order_manager: Any,
        *,
        inter_order_sleep_sec: float = 0.0,
        sleep_fn: Callable[[float], None] | None = None,
        lot_size_resolver: Callable[[str], int | None] | None = None,
    ) -> None:
        self._om = order_manager
        self._gap = float(inter_order_sleep_sec)
        self._sleep = sleep_fn or time.sleep
        self._lot_size_resolver = lot_size_resolver

    def _open_protocol_volume(self, symbol: str, lots: float) -> int:
        """Broker-correct ProtoOA volume for an OPEN; fail-fast if lotSize unknown."""
        lot_size = self._lot_size_resolver(symbol) if self._lot_size_resolver else None
        if not lot_size or int(lot_size) <= 0:
            raise ValueError(
                f"cannot size OPEN for {symbol}: broker lotSize unknown — refusing to "
                "fall back to the FX scale (10_000_000) which would 1000x over-size a "
                "dated UST10Y future (lotSize=10_000). Provide lot_size_resolver."
            )
        return lots_to_proto_volume_for_lot_size(lots, int(lot_size))

    def apply(self, plan: ReconcilePlan, *, allow_orders: bool = False) -> list[dict]:
        """Execute (or dry-plan) the reconcile. CLOSE first, then OPEN.

        allow_orders=False (default): no broker calls; returns intended ops.
        allow_orders=True: requires the order gate to be open, else raises.
        """
        if not allow_orders:
            return self._dry(plan)
        if not order_gate_open():
            raise PermissionError(
                f"order gate closed: set {TP_ORDER_GATE_ENV}={ORDER_GATE_VALUE} to place orders"
            )
        from ctrader_execution.models import OrderCommand, OrderCommandType  # lazy

        results: list[dict] = []
        for i, c in enumerate(plan.closes):
            self._om.close_position(c.position_id, c.lots, protocol_volume=c.protocol_volume)
            results.append(
                {
                    "op": "CLOSE",
                    "symbol": c.symbol,
                    "position_id": c.position_id,
                    "lots": c.lots,
                    "sent": True,
                }
            )
            if self._gap > 0 and (i < len(plan.closes) - 1 or plan.opens):
                self._sleep(self._gap)
        for j, o in enumerate(plan.opens):
            proto_vol = self._open_protocol_volume(o.symbol, o.lots)
            cmd = OrderCommand(
                command_type=OrderCommandType.SUBMIT_MARKET_ORDER,
                symbol=o.symbol,
                action=o.side,
                volume_lots=o.lots,
                stop_loss_pips=o.stop_loss_pips,
                protocol_volume=proto_vol,
                metadata={"sleeve": "tp", "leg": o.leg},
            )
            rec = self._om.submit_order(cmd)
            results.append(
                {
                    "op": "OPEN",
                    "symbol": o.symbol,
                    "side": o.side,
                    "lots": o.lots,
                    "protocol_volume": proto_vol,
                    "stop_loss_pips": o.stop_loss_pips,
                    "order_ref": getattr(rec, "order_ref", ""),
                    "sent": True,
                }
            )
            if self._gap > 0 and j < len(plan.opens) - 1:
                self._sleep(self._gap)
        return results

    @staticmethod
    def _dry(plan: ReconcilePlan) -> list[dict]:
        out: list[dict] = []
        for c in plan.closes:
            out.append(
                {
                    "op": "CLOSE",
                    "symbol": c.symbol,
                    "position_id": c.position_id,
                    "lots": c.lots,
                    "sent": False,
                }
            )
        for o in plan.opens:
            out.append(
                {
                    "op": "OPEN",
                    "symbol": o.symbol,
                    "side": o.side,
                    "lots": o.lots,
                    "stop_loss_pips": o.stop_loss_pips,
                    "sent": False,
                }
            )
        return out
