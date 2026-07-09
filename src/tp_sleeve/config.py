"""tp_sleeve / config — frozen parameters of the term-premium paper sleeve.

The SIGNAL parameter (SLOPE_FLOOR) MUST match the validated gate
(`db/scripts/bond_term_premium_gate.py`, `docs/concepts/bond_term_premium_d1_hypothesis_spec_v1.md`).
Do NOT tune post-hoc (p-hacking guard, ADR-034 §8 / ADR-041).

The EXECUTION parameters (contract multiplier, gross leverage, roll buffer) are
risk/operational knobs, NOT alpha — adjustable with documentation (ADR-041),
unlike the frozen signal.
"""

from __future__ import annotations

from typing import Final

# --- signal (frozen; matches bond_term_premium_gate.SLOPE_FLOOR) --------------
# LONG the UST 10Y future when prior month-end (DGS10 - DGS2) >= SLOPE_FLOOR,
# else FLAT. Upward curve -> positive term-premium + roll-down.
SLOPE_FLOOR: Final[float] = 0.0
REBALANCE_FREQ: Final[str] = "monthly"

# --- instrument: cTrader dated UST 10Y future CFD -----------------------------
# Quarterly contracts (CME-style month codes), e.g. UST10Y_H6 = March 2026.
CONTRACT_PREFIX: Final[str] = "UST10Y"
# Quarterly delivery months -> CME month code (H/M/U/Z = Mar/Jun/Sep/Dec).
QUARTERLY_MONTH_CODE: Final[dict[int, str]] = {3: "H", 6: "M", 9: "U", 12: "Z"}
CODE_TO_MONTH: Final[dict[str, int]] = {v: k for k, v in QUARTERLY_MONTH_CODE.items()}
# The broker symbol uses a single-digit year suffix ("H6"); decode against this
# decade base (good for the 2020s; revisit before 2030).
CONTRACT_DECADE_BASE: Final[int] = 2020

# Roll heuristic (paper, conservative): roll out of the front contract this many
# CALENDAR days before its delivery month begins. Treasury-future OI typically
# rolls ~a week before the delivery month; this avoids holding into expiry/first
# notice. MUST be reconciled against the broker's actual listed expiry before
# any unattended Phase-2 ramp (ADR-041).
ROLL_BUFFER_DAYS: Final[int] = 7

# --- sizing (B-band paper, small size; ADR-041) -------------------------------
# CFD notional of 1.0 lot = price * CONTRACT_MULTIPLIER. The exact contract size
# of the cTrader UST10Y CFD is broker-defined and MUST be confirmed from the
# symbol details before Phase 2 (like carry's LOT_BASE_UNITS). Default mirrors a
# CME 10Y note point value ($1000/point); at Stage 0 (smoke) the sizing is
# clamped to MIN_LOT so this placeholder cannot affect the first paper orders.
CONTRACT_MULTIPLIER: Final[float] = 1000.0
# Single-instrument long/flat sleeve: gross leverage = notional / equity. Smoke
# default tiny; ramp is a documented operational decision (ADR-041), not alpha.
DEFAULT_GROSS_LEVERAGE: Final[float] = 0.02
MIN_LOT: Final[float] = 0.01
LOT_STEP: Final[float] = 0.01
