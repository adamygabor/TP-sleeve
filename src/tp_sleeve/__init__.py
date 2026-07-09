"""tp_sleeve — Term-Premium TRADEABILITY_VALIDATION paper sleeve (ADR-041).

The bond term-premium edge was validated on the FREE FRED proxy
(`bond_term_premium_gate.py`, journal #40: EDGE_TRUE, carry-independent). This
sleeve does NOT re-run that research — it forward-tests the *tradeability* of the
edge on the REAL instrument (cTrader dated UST 10Y future CFD), measuring the
proxy -> real gap (quarterly roll cost + CFD financing) that a backtest cannot.

Single source of truth for sizing / risk / reconcile is the validated
`carry_sleeve` library (sleeve-agnostic), reused here unchanged; only the signal
(slope -> long/flat), the dated-future contract roll, and a thin tp-labelled
executor are new. Phase 1 = dry-run (no orders); Phase 2 = gated paper orders.
"""
