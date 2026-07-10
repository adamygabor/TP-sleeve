# D1 Hypothesis Spec — Multi-Asset Time-Series Momentum (12-1 monthly), blind gate v1

- **doc_type:** blind gate spec (risk-premium / sleeve-discovery)
- **artifact_id:** `TS_MOMENTUM_GATE_SPEC_V1`
- **created_date_iso:** 2026-07-10
- **canonical_repo:** **TP_sleeve** — this file is SoT; do not fork under FXAIEA
- **fxaiea_data_root:** `~/Dev/Forex/FXAIEA` — `models/`, `reports/`, gate harness scripts until migrated
- **status:** **LOCKED** — frozen **before** any `build_strategy` / backtest / price load for this spec
- **scope:** `GATE_SPEC_ONLY` (harness + data wiring = **next** step, separate prompt)
- **methodology anchor:** Moskowitz, Ooi & Pedersen (2012), *Time Series Momentum* — 12-month lookback, 1-month holding, vol-scaled portfolio (40% annual vol target convention)
- **related (under `fxaiea_data_root`):** `docs/concepts/cross_asset_tsmom12_risk_premium_d1_hypothesis_spec_v1.md` (daily 252d variant, **different** frequency/cost/gate family), `carry_factor_risk_premium_d1_hypothesis_spec_v1.md`, `bond_term_premium_d1_hypothesis_spec_v1.md`, `models/ctrader_asset_swap_scan_v1.json`, `reports/breadth_input_coverage/breadth_input_coverage_latest.json`
- **guard:**
  - `data_purchase = NONE` (free / existing repo inputs only)
  - `P0_CARRY = UNCHANGED`, `CARRY_EXECUTE = 0`
  - **No implicit `financing = 0`** — every cost leg tagged `ASSUMED` or `MEASURED` (§6)

---

## 0. Kanonikus állapot

```text
TS_MOMENTUM_GATE_SPEC_V1 = LOCKED (2026-07-10, REVISED same day pre-harness)
canonical_path = TP_sleeve/docs/concepts/ts_momentum_gate_spec_v1.md
usable_window = 2021-08 .. 2026-06 (N_usable = 59)
verdict_family = TS_MOMENTUM_RP_BLIND_GATE
frequency = MONTHLY (MOP holding period)
variants = A_fix_weight | B_vol_targeted (both mandatory in harness)
```

---

## 1. Hipotézis (falsifiable)

Klasszikus **time-series momentum** több, egymástól független eszközön (nem cross-sectional rank): az elmúlt **12 hónap** összesített hozamának előjele prediktív a **következő 1 hónap** irányára. A portfólió szintű, költség- és finanszírozás-nettó Sharpe **≥ 0.40**, bootstrap-robosztus, és **nem** magyarázható kizárólag vol-scaling trükkel (A vs B dominance check, §5).

**Őszinte prior:** ALACSONY–KÖZEPES. A repóban már volt sikertelen gyors TSMOM variáns (`cross_asset_tsmom12` napi 252d kontextus, §0 a régi specben). Ez a spec **MOP havi** magot követi — utolsó, vakon rögzített momentum-család-variáns ezen az univerzumon, ha bukik → **TS_MOMENTUM_FAMILY_CLOSED** (nem lazítunk **Sharpe**-küszöböt; lásd §1.1 detectability).

### 1.1 Detectability pre-check (informative — **nem** PASS-küszöb)

**Modul (normatív formula):** `fxaiea_data_root/src/detectability_gate/core.py` — `required_years_to_detect(claimed_sharpe, z_multiple=2.0)`:

```text
SE(SR) ≈ sqrt((1 + SR²/2) / T)     (T = évek, i.i.d. hozam-approximáció)
Detektálhatóság (z=2):  T ≥ z² · (1 + SR²/2) / SR²
```

**PASS-küszöb (változatlan):** `sharpe_ge_0_40` → claimed ann. Sharpe **≥ 0.40** (§5).

**Usable history a gate ablakra (§2.2):** `N_usable = 59` havi portfólió obs → `T_available = N_usable / 12 = 4.916666…` év.

**Számítás a 0.40 minimumhoz (z = 2.0):**

```text
SR = 0.40  →  SR² = 0.16
T_req(0.40) = 2² · (1 + 0.16/2) / 0.16
            = 4 · 1.08 / 0.16
            = 27.0 év
T_available = 59/12 = 4.916667 év
shortfall   = T_req − T_available = 22.083333 év
is_detectable(0.40) = false
```

**Minimum detektálható Sharpe ezen az ablakon** (ugyanaz a modul, inverz: `T_req(SR*) = T_available`):

```text
SR*_min ≈ 1.17108   (z = 2.0, T = 59/12 év)
```

**Dokumentált korlátozás (nem küszöb-lazítás):** Ez a gate **csak akkor** ad statisztikailag védhető PASS-t a **pontbecslés + bootstrap** értelmében (§5, §7), ha a valós net Sharpe **lényegesen meghaladja** a **0.40** minimum PASS-kritériumot: a fenti i.i.d.-approximáció szerint **~27 év** kellene ahhoz, hogy a **0.40** éves Sharpe **2σ** pontossággal elkülönüljön a nullától, míg csak **~4.92 év** áll rendelkezésre. A **`sharpe_ge_0_40` küszöb nem csökken**; a harness **kötelezően** kiírja a detectability blokkot az artifactban (`detectability_gate` mező, `claimed_sharpe=0.40`, `available_years`, `required_years`, `is_detectable`, `min_detectable_sharpe_at_available_years`).

---

## 2. Instrumentum-univerzum (cTrader CFD, pre-reg frozen)

**Forrás a szimbólum-listához (NEM árfolyam):** `fxaiea_data_root/models/ctrader_asset_swap_scan_v1.json` (`doc_type: ctrader_asset_swap_scan`, 2026-06-03) — `asset_class` mezők: `index`, `metal`, `commodity`, `bond`; FX külön a carry H1 fájlokból.

**Historikus lefedettség (csak dátum-meta, NEM hozamérték):**

| Meta forrás | Tartomány (szöveges) |
|-------------|----------------------|
| `fxaiea_data_root/reports/breadth_input_coverage/breadth_input_coverage_latest.json` → FX H1 | **2010-01-01 .. 2026-06-01** (7 USD pár, közös ablak) |
| `cross_asset_tsmom12_risk_premium_d1_hypothesis_spec_v1.md` §2 → `data/crossasset_d1_cache.csv` | **~2020-08 .. 2026** (~5.8 év, 13 sym, D1) |
| Journal / ADR (cTrader dated UST) | **UST10Y_*** kontraktusok **rövid** per-leg history; hosszú continuous **csak** splice-pipeline-nal (harness **ASSUMED** roll, §6) |

### 2.1 Primary universe (10 instruments, 4 asset classes)

Mind **cTrader-en listázott** continuous vagy spot CFD (nem month-code kontraktus), kivéve ahol jelezve:

| # | Symbol | Asset class | cTrader scan | Hist. coverage (gate ablak) |
|---|--------|-------------|--------------|-----------------------------|
| 1 | `US500` | equity index | `index` | D1 cache **2020-08+** (primary) |
| 2 | `USTEC` | equity index | `index` | D1 cache **2020-08+** |
| 3 | `US30` | equity index | `index` | D1 cache **2020-08+** |
| 4 | `DE30` | equity index | `index` | D1 cache **2020-08+** |
| 5 | `UK100` | equity index | `index` | D1 cache **2020-08+** |
| 6 | `JP225` | equity index | `index` | D1 cache **2020-08+** |
| 7 | `XAUUSD` | metal | `metal` | D1 cache **2020-08+** |
| 8 | `XAGUSD` | metal | `metal` | D1 cache **2020-08+** |
| 9 | `WTI` | commodity | `commodity` | D1 cache **2020-08+** |
| 10 | `BRENT` | commodity | `commodity` | D1 cache **2020-08+** |

**Bond osztály (11. láb, opcionális splice — harness kötelezően kezeli):**

| # | Symbol | Asset class | Megjegyzés |
|---|--------|-------------|------------|
| 11 | `UST10Y` (dated chain H/M/U/Z) | bond | cTrader scan: `UST10Y_*`, **swap=0 MEASURED** (scan); **continuous history ASSUMED** splice + roll cost (§6); **nem** része a `min_59_monthly_obs` portfólió ablaknak, amíg splice nincs MEASURED |

**FX kiegészítő (rezsim-diverzifikáció, carry-től független TSMOM):**

| # | Symbol | Asset class | Hist. |
|---|--------|-------------|-------|
| 12 | `EURUSD` | fx | H1 **2010-01+** → monthly agg (hosszabb ablak robustness **secondary report only**, gate primary = 2020-08+) |

### 2.2 Gate primary window — naptári ablak vs usable hónapok (frozen, rev. 2026-07-10)

**Döntés (adat-elérhetőség, nem PASS-optimalizálás):** a korai spec **összekeverte** a naptári hónapokat a **használható** portfólió obs-okkal, és a §4 split **lehetetlen dátumokat** tartalmazott. A primary 10 instrumentum D1 cache-je **nem** megy **2020-08** előtt (`cross_asset_tsmom12` meta, `data_purchase = NONE` → **nem** tolható vissza). Előre **2026-06**-ig toldjuk a naptári véget (ugyanazon cache ~2020-08→~2026 span), **nem** 2026-07-ig: a **60.** usable hónap **2026-07** lenne, ami **túlnyúlik** a pre-reg meta „~2026 / ~5.8 év” végén; **59** usable hónap **igazolható**, **60** nem — ezért a obs-küszöb **`min_59_monthly_obs`**, **nem** hallgatólagos `min_60` és **nem** alacsonyabb `min_48` (ami **eldobná** a 2026-01..2026-06 elérhető adatot).

**Naptári gate ablak (frozen):** **`2020-08` .. `2026-06`** (hónap-granularitás, mindkét végpont **inkluzív**).

**Warmup (frozen, §3):** 12 hónap lookback → az első hónap, amelyre `mom_i(t)` a teljes `R_i(t-12,t-1)` ablakkal számolható, **`t = 2021-08`** (a `2020-08`..`2021-07` naptári hónapok **adatpuffer**, nem gate obs).

**Usable portfólió hónapok (metrika- és gate-obs):** rebalance hónapok **`2021-08` .. `2026-06`**, mindkét végpont inkluzív.

**Számítás (mutatott lépések):**

```text
calendar_start     = 2020-08
calendar_end       = 2026-06
warmup_months      = 12
first_usable_month = calendar_start + warmup_months = 2021-08
last_usable_month  = calendar_end = 2026-06

N_usable = count_months_inclusive(2021-08, 2026-06)
         = (2026 − 2021) × 12 + (6 − 8) + 1
         = 5 × 12 + (−2) + 1
         = 59
```

**Ellenőrzés (összhang):** naptári hónapok `2020-08`..`2026-06` → **71** hó; warmup-puffer **12** hó → **71 − 12 = 59** usable (ugyanaz).

**Gate check (§5):** `min_59_monthly_obs` — **≥ 59** havi portfólió obs a fenti usable ablakon (variant **B**).

**Secondary extended window (non-gate):** `2010-01` .. `2026-06` csak `EURUSD` (H1) + dokumentáció; **nem** lazítja a PASS-t.

**Universe lock rule:** ezen szimbólumok **fixek**; hiányzó hónap → instrumentum kihagyva az adott hónapban (nincs universe-swap eredmény után).

---

## 3. Konstrukció (frozen — **két** variáns kötelező)

Közös időzítés (mindkét variáns):

- **Lookback:** **12 hónap** (MOP eredeti specifikáció; havi close-to-close).
- **Holding / rebalance:** **1 hónap** — jelet csak **hónap elején** (első kereskedési nap) frissítjük, a hónap során tartjuk.
- **Jel (instrumentum `i`, hónap `t`):**  
  `mom_i(t) = sign( R_i(t-12, t-1) )`  
  ahol `R_i` = **12 hónapos** összesített egyszerű hozam **záróárakból**, **csak `t-1`-ig** ismert adattal (nincs lookahead).
- **Pozíció:** long if `mom_i=+1`, short if `mom_i=-1`, flat if `mom_i=0` (nulla hozam abban az eszközben; ritka, de engedett).

### 3.1 Variant **A — fix-weight momentum** (`A_fix_weight`)

- **Cél:** tiszta **momentum-jel** teszt, vol-scaling **nélkül** (Quantpedia/MOP kritika: hozam nagy része lehet vol-targeting artefaktum).
- **Súlyok:** minden aktív instrumentumra **egyenlő abszolút súly**; gross exposure **normalizálva** `Σ|w_i| = 1` minden rebalance napon.
- **Nincs** 40% vol-target skála.

### 3.2 Variant **B — vol-targeted momentum** (`B_vol_targeted`, MOP convention)

- **Realized vol:** `σ_i` = **ex-post** havi return szórás az utolsó **12 hónapban** (trailing, `t-1`-ig), annualizálva `×√12`.
- **Nyers súly:** `w̃_i = mom_i / max(σ_i, σ_floor)` ; **`σ_floor = 1%` havi** (ASSUMED numerikus stabilitás — frozen).
- **Portfólió vol-target:** skálázás úgy, hogy a **portfólió ex-ante** annualized vol cél **`σ_target = 40%`** (MOP konvenció). Implementáció: havi portfólió vol becslés az előző 12 hó ex-post portfólió hozamából; skála `min(cap, σ_target / σ_port)` with **`cap = 3.0`** (ASSUMED leverage cap, frozen).
- **Gross norm:** `Σ|w_i| = 1` **skálázás után** (MOP-style risk-adjusted weights, majd portfólió szintű vol target).

**Kötelező párhuzamos futtatás:** a blind gate **mind A, mind B** portfólió havi nettó sorozatot állít elő (§5 dominance).

---

## 4. Portfólió hozam (havi, net)

Instrumentum havi nettó (költség + financing után, §6):

- `r_i(t)` = havi net return long/short irány szerint.
- Portfólió: `r_p(t) = Σ w_i(t) · r_i(t)` (A vagy B súlyokkal).

Metrikák (mindkét variánsra külön + **primary PASS = B**, A dominance check):

- Annualized Sharpe (`×√12`, havi obs),
- Ann. return (arithmetic mean × 12 unless harness compounds — **frozen: arithmetic mean** for Sharpe, Calmar on compounded equity curve),
- Max drawdown (compounded),
- Calmar,
- Subperiod Sharpe (**variant B**, net, **usable** ablak felezése, §2.2):
  - **H1:** **`2021-08` .. `2023-12`** (**29** havi obs),
  - **H2:** **`2024-01` .. `2026-06`** (**30** havi obs),
  - Split rule: `N_usable = 59` → `floor(59/2) = 29` első fél, `59 − 29 = 30` második fél; határ **`2023-12` | `2024-01`** (nincs átfedés, nincs hiány).
- Per-instrument Sharpe (full usable window `2021-08`..`2026-06`, net).

---

## 5. Gate (pre-reg blind checks — frozen)

**Primary verdict family:** `TS_MOMENTUM_RP_GATE` on variant **B** (vol-targeted, MOP-standard), unless **A dominance fails** (check 7).

**PASS (`TS_MOMENTUM_RP_PASS`)** iff **ALL**:

| check_id | rule | indok |
|----------|------|-------|
| `sharpe_ge_0_40` | Ann. Sharpe **(B, net)** **≥ 0.40** | Carry / cross-asset RP gate precedens (`carry_factor_risk_premium`, `cross_asset_tsmom12` §5) |
| `bootstrap_ci_lower_gt_0` | Block bootstrap **95%** CI lower bound on Sharpe **(B)** **> 0** | Carry-lánc: block=**6** hó, **5000** resample, seed=**20260602** (`carry_factor_risk_premium_gate.py`, `sleeve_2` bootstrap addendum) |
| `both_subperiods_sharpe_gt_0` | Sharpe **(B)** **> 0** in **both** half-windows (§4, §2.2: H1 `2021-08`..`2023-12`, H2 `2024-01`..`2026-06`) | Rezsim-robosztusság (usable ablak felezése) |
| `calmar_ge_0_30` | Calmar **(B)** **≥ 0.30** | Bond TP blind gate `calmar_ge_0_30` — cross-sleeve konzisztencia |
| `min_59_monthly_obs` | **≥ 59** havi portfólió obs (usable `2021-08`..`2026-06`, B) | §2.2: max igazolható usable count D1 cache meta mellett; **nem** 60 (2026-07 nincs pre-reg adatgaranciában) |
| `fraction_instruments_positive_sharpe_ge_0_60` | **≥ 60%** of primary 10 instruments have **individual** net Sharpe **> 0** (same window) | MOP: 52/58 markets significant at 5% — mini-replikáció breadth-on |
| `momentum_signal_dominance` | **A_sharpe ≥ 0.5 × B_sharpe** (both net, same window) | Anti–vol-scaling artifact: ha csak B erős, A gyenge → gyanús vol-scaling driver (Quantpedia/MOP debate); **0.5** frozen ratio |

**FAIL:** `TS_MOMENTUM_RP_FAIL_PARK` — no threshold relaxation post-hoc.

**Explicit:** PASS **nem** deploy / cTrader order permission; csak research gate artifact.

---

## 6. Költség & financing provenance (no silent zeros)

Minden sor a harnessben **`provenance`** mezővel (artifact JSON):

| Component | Treatment | Tag |
|-----------|-----------|-----|
| **Transaction cost** | **8 bps one-way** × `Σ|Δw_i|` each rebalance month (turnover on weights) | **ASSUMED** (carry/TSMOM precedens: 2 bps/day variant exists; itt konzervatív **8 bps/side** havi rebalance-hez, frozen) |
| **FX / metal / commodity overnight** | Financing from **broker swap model**: commodity/metal **~flat** (scan class mean ≈0); **index swap drag ASSUMED** applied per `ctrader_asset_swap_scan` **class-level** mean annual drag converted to daily/monthly (**ASSUMED** — not per-symbol MEASURED in gate v1) | **ASSUMED** (class aggregate) |
| **Index financing** | Scan: index class mean annual blend **≈ −6.1%** (2026-06 scan) — **must** be subtracted in net series for index legs | **ASSUMED** (class-level; journal #22) |
| **UST10Y dated** | Swap **0** on dated UST (**MEASURED** scan); **roll gap 10 bps** per quarter roll when splice used | **MEASURED** swap + **ASSUMED** roll (TP roll-gap order of magnitude) |
| **Financing capture (FXCarry lesson)** | No `CAPTURE=1.0` implicit edge; if live capture ≠ 1, **diagnostic only** post-gate | N/A at spec |
| **Price / return data** | D1 cache / H1 agg — source path frozen at harness commit | **MEASURED** data path, **ASSUMED** roll/splice where noted |

**Harness hard rule:** `ASSUMED` and `MEASURED` mixed → artifact `cost_model_provenance` block **required**; backtest with **zero** financing **forbidden** unless leg tagged `MEASURED zero` (e.g. UST swap).

---

## 7. Bootstrap (frozen)

- **Method:** block bootstrap on **monthly** portfolio returns (not IID).
- **Block length:** **6** months (carry / `carry_factor_risk_premium_gate` / net carry diagnostic convention).
- **Resamples:** **5000**.
- **Seed:** **20260602**.
- **CI:** **95%** (quantiles **0.025**, **0.975**) on annualized Sharpe.

---

## 8. Verdict & artifacts (future harness — not part of this commit)

```text
Spec (SoT):     TP_sleeve/docs/concepts/ts_momentum_gate_spec_v1.md
Harness (next): ~/Dev/Forex/FXAIEA/db/scripts/ts_momentum_gate.py  # name TBD at implementation
Outputs:        ~/Dev/Forex/FXAIEA/models/ts_momentum_gate_v1.json
                ~/Dev/Forex/FXAIEA/docs/reports/ts_momentum_gate_report_v1.md
```

**Workflow guard (ADR-039 / FXCarry `.cursorrules`):** `channel_capture_gate` / financing **MEASURED** capture is **orthogonal**; this gate may not claim live edge until swap capture measured per channel — spec only defines **ASSUMED** class financing unless superseded.

---

## 9. Lock record

```text
LOCKED_BY = maintainer pre-reg (spec-only step)
LOCKED_AT = 2026-07-10
REVISED_AT = 2026-07-10
REVISION_KIND = blind-phase spec error fix (pre-harness); NOT post-hoc threshold tuning on outcomes
NO_BACKTEST_BEFORE_LOCK = true
THRESHOLDS_TUNED_ON_DATA = false
SHARPE_PASS_THRESHOLD_UNCHANGED = 0.40
```

### 9.1 Changelog (REVISED_AT)

| Mi változott | Miért |
|--------------|--------|
| §2.2 gate ablak **`2020-08`..`2026-06`**, **`N_usable = 59`** | Korai spec 65 naptári hónapot számolt **`2025-12`-ig**, warmup nélkül → tényleges usable **53**; D1 cache **2020-08** előtt nem bővíthető; vége **2026-06**-ig toldva (elérhető span), **59** a max igazolható usable, **60** nem. |
| §5 `min_60_monthly_obs` → **`min_59_monthly_obs`** | Küszöb **a számolt usable obs-hoz** igazodik; **nem** „könnyebb PASS” (59 > 53), és **nem** hamis 60. **`sharpe_ge_0_40` változatlan.** |
| §4 subperiod **`2021-08`..`2023-12` \| `2024-01`..`2026-06`** | Előző split (`2020-08..2017-12`) matematikailag érvénytelen és nem esett a usable ablakra. |
| §1.1 detectability pre-check | `detectability_gate` szerint **0.40** Sharpe **nem** detektálható **~4.92 év** alatt; dokumentált elvárás-korlát harness előtt. |

### 9.2 FINAL_VERDICT (post-harness — family closed)

```text
FINAL_VERDICT_DATE = 2026-07-10
GATE_ARTIFACT = ~/Dev/Forex/FXAIEA/models/ts_momentum_gate_v1.json
GATE_STATUS = TS_MOMENTUM_RP_FAIL_PARK
gate.pass = false
TS_MOMENTUM_FAMILY_CLOSED = true
FAMILY_CLOSE_RULE = spec §1 pre-reg: LAST momentum variant on this universe; no threshold relaxation; no retry on this family
```

**Harness (első ár/hozam futás, frozen küszöbök):** usable **2021-08..2026-06**, **N=59**; primary PASS variáns **B_vol_targeted**.

| check_id | eredmény | szám (B, net, usable ablak) |
|----------|----------|-----------------------------|
| `sharpe_ge_0_40` | PASS | ann. Sharpe **+0.5006** (≥ 0.40) |
| `bootstrap_ci_lower_gt_0` | **FAIL** | bootstrap Sharpe 95% CI alsó **−0.4879** (≤ 0) |
| `both_subperiods_sharpe_gt_0` | **FAIL** | H1 **−0.8202**, H2 **+2.0199** (H1 ≤ 0) |
| `calmar_ge_0_30` | **FAIL** | Calmar **0.2189** (< 0.30) |
| `min_59_monthly_obs` | PASS | **59** obs |
| `fraction_instruments_positive_sharpe_ge_0_60` | PASS | **6/10** = 0.60 |
| `momentum_signal_dominance` | PASS | A **+0.5386** ≥ 0.5×B **+0.2503** |

**Lezárás:** a **3 bukott check** (`bootstrap_ci_lower_gt_0`, `both_subperiods_sharpe_gt_0`, `calmar_ge_0_30`) a pre-reg **§5** szerint **FAIL_PARK**. A **TS momentum család LEZÁRVA** ezen a frozen univerzumon és gate-protokollon — **nincs** küszöb-lazítás, **nincs** további variáns ugyanezen a családon (§1, §0 kontextus: utolsó MOP havi 12-1 variáns).

---

## References (external, not repo data)

- Moskowitz, T. J., Ooi, Y. H., & Pedersen, L. H. (2012). Time series momentum. *Journal of Financial Economics*.
- MOP vol-target **40%** annual portfolio vol convention (implementation detail in variant B, §3.2).
- Quantpedia / practitioner critique: momentum profitability sensitivity to vol scaling — motivates **A vs B** (§3, check `momentum_signal_dominance`).
