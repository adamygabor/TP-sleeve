# Workspace kanon — TP_sleeve (2026-07-10)

**Cursor multi-root SoT:** nyisd a `TP_sleeve.code-workspace` fájlt (TP sleeve + FXCarry + FXAIEA Dev).

| Szerep | Útvonal |
|--------|---------|
| **Kanonikus workspace / beszélgetés-spec** | Google Drive `…/Forex/Robot/TP_sleeve` |
| **TP ops kód** | `TP_sleeve/src/tp_sleeve/` |
| **Carry + cTrader közös lib** | sibling `FXCarry/` |
| **Gates, mixed policy, journal, D1 cache** | `~/Dev/Forex/FXAIEA` (implementáció; nem Drive) |

## Ebből a szál-ból rögzített artefaktok

### Spec (SoT itt, TP_sleeve)

- `docs/concepts/ts_momentum_gate_spec_v1.md` — LOCKED, harness még nincs

### Bond TP portfolio candidate (kód + model FXAIEA Dev)

- Gate script: `FXAIEA/db/scripts/sleeve_2_bond_tp_portfolio_candidate_gate.py`
- Governance truth: `FXAIEA/models/sleeve_2_bond_tp_portfolio_candidate_gate_v3_ci_gated.json` → **`gate.pass = false`** (CI checks)
- Policy: `FXAIEA/src/mixed_portfolio_policy/gate_status.py` + `autonomous_paper.py`
- Journal: `FXAIEA/docs/reports/fxaiea_journal_v1.md` (#114)

### Net carry forrás (FXCarry)

- `FXCarry/db/scripts/carry_gate_net_of_swap_markup.py` — portfolio gate `--net-carry` PYTHONPATH-hoz

### Autonomous paper snapshot (FXAIEA)

- `FXAIEA/logs/mixed_policy_autonomous/autonomous_paper_latest.json` — carry-only budget when v3 fail

## Következő lépés (felhasználói prompt)

Blind `ts_momentum_gate.py` a fenti LOCKED spec alapján; spec olvasása **mindig** TP_sleeve-ből.
