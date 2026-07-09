"""tp_sleeve / signal — slope-gated long/flat term-premium construction (SoT).

Bit-for-bit the validated gate rule (`bond_term_premium_gate.build_strategy`):
LONG the front UST 10Y future for month m if the PRIOR month-end curve slope
(DGS10 - DGS2) >= SLOPE_FLOOR, else FLAT. The threshold is frozen (config).

Target is a single-instrument portfolio (one BUY leg on the front contract, or
empty when FLAT), reusing the sleeve-agnostic `carry_sleeve.types` dataclasses so
the validated sizing / risk / reconcile code applies unchanged.
"""

from __future__ import annotations

from collections.abc import Mapping

from carry_sleeve.types import TargetPortfolio, TargetPosition
from tp_sleeve.config import SLOPE_FLOOR

__all__ = [
    "exposure_from_slope",
    "month_end_slopes",
    "prior_month_end_slope",
    "compute_target",
]


def exposure_from_slope(slope: float, floor: float = SLOPE_FLOOR) -> int:
    """1 (LONG) if curve slope (DGS10 - DGS2) >= floor, else 0 (FLAT)."""
    return 1 if float(slope) >= float(floor) else 0


def month_end_slopes(rows: list[Mapping[str, object]]) -> dict[tuple[int, int], float]:
    """Map (year, month) -> slope (dgs10 - dgs2) at the LAST available day.

    `rows` must be dicts with a `date` (datetime.date) and numeric `dgs10`,
    `dgs2`. Used to read the prior month-end slope that drives the next month's
    exposure (tradable lag: month m uses month m-1's end-of-month slope).
    """
    by_month: dict[tuple[int, int], object] = {}
    for r in sorted(rows, key=lambda x: x["date"]):  # type: ignore[index,arg-type]
        d = r["date"]
        by_month[(d.year, d.month)] = r  # type: ignore[union-attr]
    out: dict[tuple[int, int], float] = {}
    for ym, r in by_month.items():
        out[ym] = float(r["dgs10"]) - float(r["dgs2"])  # type: ignore[index]
    return out


def prior_month_end_slope(rows: list[Mapping[str, object]], as_of_ym: str) -> float | None:
    """Slope at the end of the month BEFORE `as_of_ym` (YYYY-MM), or None.

    This is the signal that decides exposure for the `as_of_ym` rebalance month
    (same tradable lag as the validated gate).
    """
    y, m = int(as_of_ym[:4]), int(as_of_ym[5:7])
    prior = (y - 1, 12) if m == 1 else (y, m - 1)
    return month_end_slopes(rows).get(prior)


def compute_target(front_contract: str, exposure: int, as_of: str = "") -> TargetPortfolio:
    """Single-leg target: BUY `front_contract` when LONG, empty when FLAT.

    weight = 1.0 (single instrument) so `carry_sleeve.sizing` puts the whole
    gross budget on this leg; `leg`/`ccy` are descriptive only.
    """
    if exposure not in (0, 1):
        raise ValueError("exposure must be 0 (FLAT) or 1 (LONG)")
    if exposure == 1 and not front_contract:
        raise ValueError("front_contract required when exposure == 1")
    positions: list[TargetPosition] = []
    if exposure == 1:
        positions.append(
            TargetPosition(
                symbol=front_contract,
                side="BUY",
                weight=1.0,
                ccy="UST10Y",
                leg="long",
            )
        )
    return TargetPortfolio(
        as_of=as_of,
        positions=positions,
        longs=["UST10Y"] if exposure == 1 else [],
        shorts=[],
    )
