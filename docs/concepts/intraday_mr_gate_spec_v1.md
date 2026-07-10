# D1 Hypothesis Spec — Short-horizon mean-reversion (1–5 trading days), blind gate v1

- **doc_type:** blind gate spec (risk-premium / sleeve-discovery)
- **artifact_id:** `INTRADAY_MR_GATE_SPEC_V1`
- **created_date_iso:** 2026-07-10
- **canonical_repo:** **TP_sleeve** — this file is SoT
- **fxaiea_data_root:** `~/Dev/Forex/FXAIEA` — harness, models, cTrader data wiring (future step)
- **status:** **LOCKED** — frozen **before** any `build_strategy` / backtest / price load for this spec
- **scope:** `GATE_SPEC_ONLY` (harness + data wiring = **next** step, separate prompt)
- **related:** `ts_momentum_gate_spec_v1.md` (§9.2 **TS_MOMENTUM_FAMILY_CLOSED**), `carry_factor_risk_premium_d1_hypothesis_spec_v1.md`, `bond_term_premium_d1_hypothesis_spec_v1.md`, ADR-039 `channel_capture_gate`, `models/ctrader_asset_swap_scan_v1.json`, `reports/breadth_input_coverage/breadth_input_coverage_latest.json`, `data/crossasset_d1_cache.csv` (path only), `src/detectability_gate/core.py`
- **guard:**
  - `data_purchase = NONE` at spec lock (free / existing repo inputs + cTrader API fetch allowed at harness — not new paid vendors)
  - `P0_CARRY = UNCHANGED`, `CARRY_EXECUTE = 0`
  - **No implicit `financing = 0`** — every cost leg tagged `ASSUMED` or `MEASURED`
  - **Blind PASS ≠ deploy** — `channel_capture_gate` **MEASURED** capture required before any live order permission (§8)

---

## 0. Kanonikus állapot

```text
INTRADAY_MR_GATE_SPEC_V1 = LOCKED (2026-07-10)
canonical_path = TP_sleeve/docs/concepts/intraday_mr_gate_spec_v1.md
verdict_family = INTRADAY_MR_D1_SHORTHOLD_BLIND_GATE
frequency = D1 signal bar; hold 1–5 trading days (not sub-daily)
primary_universe_n = 8  (WTI/BRENT excluded — see §2)
```

---

## 1. Hipotézis (falsifiable)

**Rövid horizontú mean-reversion** likvid cTrader CFD-kon: ha az elmúlt **L = 5** kereskedési nap **z-score-ja** (egyszerű hozam a saját **20 napos** trailing vol skálán) **>|z_entry|**, akkor **1–5 napos** tartású **ellenirányú** pozíció **nettó** portfólió Sharpe-je **≥ 0.40**, bootstrap-robosztus, rezsim-félidőkben pozitív, és **túlél 1.5× költség-stresszt** (§6–§7).

**Őszinte prior:** ALACSONY. Az eddigi **5** blind gate családból **mindegyiknél** a **bootstrap CI** (vagy CI-szerű robusztusság) bukott a havi/napi alacsony effektív **független** mintaszám mellett; a TS momentum család **lezárva** (§9.2 `ts_momentum_gate_spec_v1.md`). Ez a spec **szándékosan** magasabb **trade-számú** obs egységet rögzít (§3–§5), de **nem** ígér automatikus detektálhatóságot **0.40** Sharpe-nál (§1.1).

**Pre-reg fegyelem:** egyetlen **D1 short-hold MR** variáns ezen a frozen univerzumon; bukás → **`INTRADAY_MR_FAMILY_CLOSED`** (harness után, külön FINAL_VERDICT — most **nincs**).

---

### 1.1 Detectability pre-check (informative — **nem** PASS-küszöb)

**Modul:** `fxaiea_data_root/src/detectability_gate/core.py` — `required_years_to_detect(claimed_sharpe, z_multiple=2.0)`:

```text
SE(SR) ≈ sqrt((1 + SR²/2) / T)     (T = effektív év)
Detektálhatóság (z=2):  T ≥ z² · (1 + SR²/2) / SR²
```

**PASS-küszöb (változatlan):** `sharpe_ge_0_40` → ann. Sharpe **≥ 0.40** (§5).

**Effektív idő skála trade-számból (frozen mapping, pre-harness):**

```text
R_portfolio = 120 completed round-trips / calendar year (portfolio-level, all primary legs combined)
T_available = N_trades / R_portfolio        (év-equivalens, NEM “havi hónap”)
```

**Gate ablak (§2.3):** ~**5.8** calendar year D1 span (`2020-08` .. `2026-06`, index/metal D1 cache meta) → **N_trades_expected ≈ R × 5.8 = 696** (felső becslés, ha a stratégia ténylegesen ennyit fordul; harness méri a tényleges `N_trades`).

**Számítás a 0.40 minimumhoz (z = 2.0):**

```text
SR = 0.40  →  T_req(0.40) = 27.0 év   (detectability_gate closed form)
N_trades_req(0.40) = T_req × R = 27.0 × 120 = 3240 completed round-trips
N_trades_expected ≈ 696  →  T_available ≈ 696/120 = 5.8 év
shortfall_trades ≈ 3240 − 696 = 2544 round-trips
is_detectable(0.40) at expected N = false
```

**Minimum detektálható Sharpe ~5.8 év-equivalens ablakon** (`T_req(SR*) = 5.8`):

```text
SR*_min ≈ 1.026   (z = 2.0)
```

**Dokumentált korlátozás:** A magasabb **trade-szám** (vs ~59 havi TSMOM obs) **csökkenti** a bootstrap CI szélességét **ugyanazon calendar ablakban**, de **nem** oldja meg önmagában a **0.40** vs null **27 év-equivalens** detektálhatósági követelményt. A harness **kötelezően** kiírja: `detectability_gate` **a mért Sharpe-pal** (nem a 0.40 küszöbbel), plusz `N_trades`, `R_portfolio`, `N_trades_req_at_0_40`, `is_detectable`.

**Napi MTM alternatíva (informatív):** ~**1461** kereskedési nap ugyanabban az ablakban → `T = 1461/252 ≈ 5.80` év — **ugyanaz** a detektálhatósági plafon; a spec **trade-szám** obs-küszöböt használ PASS-ra (§5).

---

## 2. Instrumentum-univerzum & adatfelbontás (meta only — no prices read at lock)

### 2.1 Kiinduló lista (TS momentum primary 10)

`US500`, `USTEC`, `US30`, `DE30`, `UK100`, `JP225`, `XAUUSD`, `XAGUSD`, `WTI`, `BRENT`.

### 2.2 Elérhető felbontás — repo meta (2026-07-10)

| Forrás | Tartalom | Felbontás | Lefedettség (szöveges meta) |
|--------|----------|-----------|-----------------------------|
| `data/crossasset_d1_cache.csv` | index / metal / commodity CFD | **D1** closes | ~**1499** nap / szimbólum, ~**2020-08 → 2026-06** (TSMOM harness coverage report) |
| `reports/breadth_input_coverage/breadth_input_coverage_latest.json` | **FX** carry H1 | **H1** | **2010-01-01 .. 2026-06-01**, 7 USD pár — **nem** tartalmazza a fenti 10 CFD index/energia listát |
| `data/tsdb_window_eurusd_m15.csv` | EURUSD | **M15** | létezik — **EURUSD ∉** frozen primary 10 |
| `src/ctrader_execution/session.py` | cTrader Open API | **M1..D1** trendbars (`period` enum: **1=M1**, 7=M15, 9=H1, **12=D1**) | **API képesség**; index/M1 **nincs** bulk cache-elve a repóban |
| TSMOM harness `instrument_coverage` | WTI, BRENT | D1 | **~1** hónap a `2020-08..2026-06` gate ablakban — **kieső** |

**Következtetés (frozen döntés, nem előny-optimalizálás):** valódi **napon belüli (M1/M5) VWAP MR** a teljes 10-es univerzumon **nincs MEASURED bulk history** a repóban; csak **harness-time cTrader M1 fetch** lenne, ami e spec lock pillanatában **nincs auditálva**. Ezért a horizont **D1 short-hold MR** (§3), **nem** 5–30 perces intraday.

### 2.3 Primary gate universe (frozen, **8** instruments)

| # | Symbol | Osztály | Adat a gate ablakban |
|---|--------|---------|---------------------|
| 1 | `US500` | index | D1 cache, ~71/71 hó |
| 2 | `USTEC` | index | D1 cache, ~70/71 hó (2020-08 hiány) |
| 3 | `US30` | index | D1 cache |
| 4 | `DE30` | index | D1 cache (2026-02..06 hiány → skip hónapok) |
| 5 | `UK100` | index | D1 cache |
| 6 | `JP225` | index | D1 cache |
| 7 | `XAUUSD` | metal | D1 cache |
| 8 | `XAGUSD` | metal | D1 cache |

**Kizárva primary-ból (data meta, nem universe-swap eredmény után):**

| Symbol | Indok |
|--------|--------|
| `WTI`, `BRENT` | TSMOM harness: gyakorlatilag **nincs** D1 a gate ablakban; cTrader fetch **194** nap — nem elég a §5 `min_completed_trades` |
| `EURUSD` | nincs a TS 10 listában; H1/M15 külön sín — **secondary report only** |

**Universe lock rule:** hiányzó nap/hó → instrumentum **kihagyva** az adott döntési napon; **nincs** szimbólum-csere.

**Gate calendar (frozen):** **`2020-08-01` .. `2026-06-30`** kereskedési napok (D1); warmup **20 + 5** nap (§3) → első trade-dátum meta ~**2020-09** (harness igazolja).

---

## 3. Konstrukció (frozen — single variant)

**Horizont választás (§2.2 alapján):** **1–5 kereskedési nap** tartás, **D1 close** jelzés — **nem** napon belüli.

**Jelzés (minden primary instrumentum `i`, nap `t` D1 close után):**

```text
r5_i(t)   = close(t)/close(t-5) - 1
sigma_i(t) = std( daily_ret_i on [t-20, t-1] )   # 20 nap, csak múlt
z_i(t)    = r5_i(t) / max(sigma_i(t), sigma_floor)
sigma_floor = 0.15% napi   (ASSUMED numerikus stabilitás — frozen)

Entry (MR): if z_i(t) > +z_entry  → open SHORT i; if z_i(t) < -z_entry → open LONG i
z_entry = 1.25   (frozen)

Exit (első teljesülés):
  - time stop: hold = H_max = 5 trading days, OR
  - mean-revert: |z_i| < z_exit with z_exit = 0.25, OR
  - opposite signal: new entry triggers flatten + reverse (turnover számít)

Max 1 nyitott pozíció / instrumentum; portfólió súly: equal-risk
  w_i ∝ sign(position_i) / max(sigma_i(t), sigma_floor); gross norm Σ|w_i| = 1
```

**Turnover / obs számlálás:** minden **completed round-trip** (open→flat) = **1 trade** a §5 `N_trades` és §1.1 `N_trades` számlálóban.

---

## 4. Portfólió hozam & metrikák

**Napi portfólió MTM** (mark-to-market, net költség/financing után, §6) minden kereskedési napon; **trade-szintű** net hozam minden completed round-trip-re (harness mindkettőt naplózza).

**Sharpe a gate PASS-ra (frozen):** **trade-szintű** net hozamokból, annualizálás:

```text
Sharpe_trade = mean(r_trade) / std(r_trade) × sqrt(R_portfolio)
```

ahol `R_portfolio = 120` (§1.1) — **nem** √252 napi, hogy összhangban legyen a detektálhatósági trade-mappinggel.

**Metrikák (gate ablak):** ann. Sharpe (trade), ann. return (arithmetic mean × R_portfolio), max DD (compounded napi MTM), Calmar, subperiod Sharpe (trade) H1/H2 (§5), `N_trades`, per-instrument trade Sharpe.

**Subperiod split (calendar, frozen):**

- **H1:** trades with **entry date** in **`2021-01-01` .. `2023-12-31`**
- **H2:** **`2024-01-01` .. `2026-06-30`**

---

## 5. Gate (pre-reg blind checks — frozen)

**PASS (`INTRADAY_MR_PASS`)** iff **ALL**:

| check_id | rule |
|----------|------|
| `sharpe_ge_0_40` | Trade-szintű ann. Sharpe **≥ 0.40** (§4) |
| `bootstrap_ci_lower_gt_0` | Block bootstrap **95%** CI lower on trade Sharpe **> 0** (§7) |
| `both_subperiods_sharpe_gt_0` | Trade Sharpe **> 0** in **both** H1 and H2 (§4) |
| `calmar_ge_0_30` | Calmar (napi MTM compounded) **≥ 0.30** |
| `min_completed_trades` | **≥ 400** completed round-trips (portfolio, gate ablak) |
| `max_drawdown_limit` | Max DD **≥ −0.35** (35% — frozen; equív. risk cap) |
| `cost_sensitivity_sharpe_ge_0_40` | Trade Sharpe **≥ 0.40** still holds when **all ASSUMED costs × 1.5** (§6) |
| `fraction_instruments_positive_trade_sharpe_ge_0_60` | **≥ 60%** of **8** primary symbols have **individual** trade-level net Sharpe **> 0** |

**FAIL:** `INTRADAY_MR_FAIL_PARK`.

**Explicit:** PASS **nem** deploy / cTrader order permission.

---

## 6. Execution realism & költség (blind — carry lesson)

Minden sor **`provenance`** a harness JSON-ban.

| Component | Treatment | Tag |
|-----------|-----------|-----|
| **Spread + slippage (round-trip)** | **ASSUMED** per asset class, **one-way equivalent × 2** per round-trip: index **12 bps/side** (24 bp RT), metal **10 bps/side**, commodity **15 bps/side** (commodity not in primary) | **ASSUMED** — **magasabb** mint havi TSMOM **8 bps/side**, mert rövid hold → magasabb turnover súly |
| **Turnover költség** | `cost = bps_side × 2 × (|Δ gross exposure|)` minden entry/exit/reverse napon | **ASSUMED** |
| **Overnight financing** | Class-level `ctrader_asset_swap_scan_v1.json` `mean_annual_blend_pct` / 252 × napok × |w| | **ASSUMED** (index ≈ −6.1% éves drag) |
| **Financing capture** | Nincs `CAPTURE=1.0`; live csak **MEASURED** `channel_capture_gate` után | deploy guard |
| **Price data** | D1 cache + optional cTrader refetch | **MEASURED** path at harness |

**`cost_sensitivity` check (§5):** ugyanaz a backtest, de minden **ASSUMED** bps leg **×1.5**; a trade Sharpe-nak **≥ 0.40** maradnia kell. Ez **stressz** a saját konzervatív becslésünkre — nem utólagos finomítás.

---

## 7. Bootstrap (frozen — frequency-matched)

**Sorozat:** **trade-szintű** net hozamok (completed round-trips), időrendben.

**Miért NEM 6 hónapos block:** a havi TSMOM-nál **6 hó** ≈ 6 független havi obs; itt **1–5 napos** tartás → trade-ek **~2–5 nap** távolságra; az autocorrelation **~1–3 hét** skálán van.

**Frozen block:** **`B = 25` completed trades** (~5 hét portfolio aktivitás `R=120`/év mellett).

**Method:** block bootstrap on trade returns; **5000** resamples; **seed = 20260602**; **95%** CI (0.025, 0.975) on **trade Sharpe** (§4 formula).

---

## 8. Channel capture & deploy guard (ADR-039)

```text
Blind gate PASS  →  research artifact only
Live / deploy    →  requires channel_capture_gate PASS (MEASURED financing capture)
                     on ctrader_demo_icmarkets (or successor channel id) BEFORE orders
Harness MUST fail closed if ASSUMED capture used for deploy claims.
```

---

## 9. Lock record

```text
LOCKED_BY = maintainer pre-reg (spec-only step)
LOCKED_AT = 2026-07-10
NO_BACKTEST_BEFORE_LOCK = true
THRESHOLDS_TUNED_ON_DATA = false
SHARPE_PASS_THRESHOLD = 0.40
HORIZON_CHOICE = D1_1to5d_MR  (rejected: M1 intraday on full universe — no bulk MEASURED M1 in repo)
```

---

## 10. Future artifacts (not part of this commit)

```text
Harness (next): ~/Dev/Forex/FXAIEA/db/scripts/intraday_mr_gate.py
Outputs:        ~/Dev/Forex/FXAIEA/models/intraday_mr_gate_v1.json
                ~/Dev/Forex/FXAIEA/docs/reports/intraday_mr_gate_report_v1.md
```

---

## References (external)

- Lo & MacKinlay (1988) contrarian/mean-reversion; short-horizon reversal literature (context only).
- Moskowitz TSMOM **closed** on same broad cTrader universe — do not re-open TSMOM params.
