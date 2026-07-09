# TP sleeve

Standalone **bond term-premium (UST 10Y dated future)** paper sleeve (ADR-041): signal, quarterly roll, and gated cTrader executor — split from [FXAIEA](https://github.com/adamygabor/FXAIEA). Reuses the validated sleeve-agnostic library in sibling [FXCarry](https://github.com/adamygabor/FXCarry) (`carry_sleeve`, `ctrader_execution`).

## Layout

- `src/tp_sleeve/` — slope signal, contract roll, executor (SoT for TP-specific logic)
- `tests/tp_sleeve/` — unit tests (offline)

## Quick start

```bash
cd "/path/to/TP_sleeve"
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-ctrader-runtime.txt
.venv/bin/pip install -e ../FXCarry
.venv/bin/pip install -e .
cp env.example .env   # fill CTRADER_* and optional TP_*
make test-tp
```

Offline tests (no broker):

```bash
make test-tp
```

## Order gate (Phase 2 only)

`TP_EXECUTE=1` **and** `FXAIEA_TP_ALLOW_CTRADER_ORDERS=I_UNDERSTAND_THIS_CAN_PLACE_BROKER_ORDERS` (TP-local gate; not shared with carry `FXCARRY_*`).

## FXAIEA / FXCarry

- Research gate (FRED proxy): FXAIEA `bond_term_premium_gate.py` (journal #40).
- Shared sizing / reconcile: install editable **FXCarry** (`carry_sleeve`).
- TP **ops** will live in this repo as they are migrated from FXAIEA.
