# D1 Hypothesis Spec — Cross-sectional FX carry (pair-ranked tertiles), blind gate v1

- **doc_type:** blind gate spec (risk-premium / sleeve-discovery)
- **artifact_id:** `CROSS_SECTIONAL_FX_CARRY_GATE_SPEC_V1`
- **created_date_iso:** 2026-07-10
- **canonical_repo:** **TP_sleeve** — this file is SoT; do not fork under FXAIEA
- **fxaiea_data_root:** `~/Dev/Forex/FXAIEA` — `data/2010-2026/`, `db/scripts/fetch_fred_rates.py`, harness (future)
- **fxcarry_data_root:** `~/Library/CloudStorage/.../FXCarry` (or local clone) — `src/channel_gate/cip.py`, `src/carry_sleeve/`, cTrader swap capture
- **status:** **LOCKED** — frozen **before** harness / backtest / **rate or price load for this gate**
- **scope:** `GATE_SPEC_ONLY` (harness + H1 backfill for Tier B = **next** step)
- **related:** `carry_factor_risk_premium_d1_hypothesis_spec_v1.md` (D1 #4, **different** construction — §10), `carry_rate_differential_d1_hypothesis_spec_v1.md` (D1 #3, pair-sign timing), `ts_momentum_gate_spec_v1.md` (gate check precedens), `intraday_mr_gate_spec_v1.md`, ADR-039 `channel_capture_gate`, `models/ctrader_asset_swap_scan_v1.json`, `reports/breadth_input_coverage/breadth_input_coverage_latest.json`, `src/detectability_gate/core.py`
- **guard:**
  - `data_purchase = NONE` (FRED public CSV + existing repo paths; cTrader H1 fetch allowed at harness)
  - `P0_CARRY = UNCHANGED`, `CARRY_EXECUTE = 0` — **nem** nyitja újra a D1 #4 deploy / `carry_factor_risk_premium_gate` családot
  - **No implicit `financing = 0`** — párszintű swap provenance `ASSUMED` | `MEASURED` (§6)
  - **Blind PASS ≠ deploy** — `channel_capture_gate` **MEASURED** capture továbbra is kötelező live order előtt

---

## 0. Kanonikus állapot

```text
CROSS_SECTIONAL_FX_CARRY_GATE_SPEC_V1 = LOCKED (2026-07-10)
canonical_path = TP_sleeve/docs/concepts/cross_sectional_fx_carry_gate_spec_v1.md
verdict_family = CROSS_SECTIONAL_FX_CARRY_RP_BLIND_GATE
frequency = MONTHLY rebalance
N_PLANNED = 41   (Tier B frozen pair universe, §2)
rank_key = pair_carry_diff_annual_pct (FRED 3M, tradable lag)
bucket_rule = TERTILE long top / short bottom / flat middle
```

---

## 1. Hipotézis (falsifiable)

**Keresztmetszeti FX carry** széles cTrader FX univerzumon: minden hónap elején a párokat **kamatkülönbség szerint rangsoroljuk** (nem deviza-szintű aggregált faktor); a **felső tercil** párokat **long**, az **alsó tercil** párokat **short**, a középső **flat**. Long és short láb **egyenlő súlyú**, **dollar-neutral** portfólió havi nettó Sharpe-je **≥ 0.40**, bootstrap-robosztus, subperiod- és breadth-kontraktok teljesülnek (§5).

**Őszinte prior:** KÖZEPES — a carry prémium irodalma erős, de a D1 #4 **7-devizás** faktor ugyanezen FRED-jellel **standalone FAIL** (Sharpe 0.282). Ez a spec **breadth-et** növel (41 pár), **más** statisztikai konstrukció (§10); **nem** garantál PASS-t.

### 1.1 Detectability pre-check (informative — **nem** PASS-küszöb)

**Modul:** `fxaiea_data_root/src/detectability_gate/core.py` — `required_years_to_detect`, `evaluate_detectability` (`z_multiple=2.0`).

**PASS-küszöb (változatlan):** `sharpe_ge_0_40` → ann. Sharpe **≥ 0.40** (§5).

**Effektív idő skála (havi portfólió obs, frozen):** `T_available = N_gate_months / 12`.

**MEASURED lefedettség-számítás (spec-fázis, 2026-07-10 — nem feltételezett 7-pár ablak):**

1. **FX ár (H1 → D1):** `fxaiea_data_root/data/2010-2026/{PAIR}_Hourly_Bid_*.csv` — fájl első/utolsó időbélyeg **meta** (hozam **nem** olvasva).
2. **Kamat (havi):** `fred_3m_rates.csv` sor-szám meta → **197** hónap, **2010-01 .. 2026-05** (8 G10, repo-ban MEASURED fetch út); Tier B **SEK/NOK/DKK** sorok harness prep **kötelező** (§2.2), spec-fázisban **még nincs** CSV-ben.
3. **Közös ablak a *jelenleg cache-elt* Tier B részhalmazra:** a 41 párból **11**-hez van H1 fájl; e 11 páros **hónap-metszet** (mind a 11 fájlban megjelenő `YYYY-MM`):

```text
N_common_H1_11 = 198 hónap
first_common     = 2010-01
last_common      = 2026-06
T_available      = 198 / 12 = 16.5 év
```

4. **41-pár teljes univerzum:** **30** párhoz **nincs** H1 cache (2026-07-10). A **41-pár közös** gate-hónap-szám **nem** extrapolálható a régi 7 USD-pár `breadth_input_coverage` meta alapján — a harness **kötelezően** újraszámolja H1 backfill után.

**Számítás a 0.40 minimumhoz (`evaluate_detectability(0.40, 16.5)`):**

```text
T_req(0.40) = 27.0 év
T_available = 16.5 év
shortfall   = 10.5 év
is_detectable(0.40) = false
```

**Minimum detektálható Sharpe ezen a MEASURED 11-pár közös ablakon** (`T_req(SR*) = 16.5`):

```text
SR*_min ≈ 0.525   (z = 2.0)
```

**Következmény (nem küszöb-lazítás):** A teljes **41-pár** gate csak akkor ad **hosszabb** `T_available`-t, ha a backfill után a **közös** FX+rate hónapok száma nő; jelenlegi **MEASURED** alsó korlát **16.5 év** → **0.40** Sharpe **2σ** detektálhatósága **nem** teljesül. A harness **kötelezően** kiírja: `detectability_gate` (`claimed_sharpe=0.40`, `available_years`, `required_years`, `is_detectable`, `min_detectable_sharpe_at_available_years`, `coverage_basis` = `measured_h1_intersection_11_of_41` | `measured_full_41_post_backfill`).

---

## 2. Instrumentum-univerzum (cTrader FX, pre-reg frozen)

### 2.1 Forrás: 63 élő cTrader FX szimbólum

- **Lista forrás (NEM árfolyam):** `fxaiea_data_root/models/ctrader_asset_swap_scan_v1.json` (`symbol_counts.fx = 63`, scan **2026-06-03**) és/vagy `FXCarry/db/scripts/diag_ctrader_symbols.py` (`asset_class == fx`).
- **Teljes 63-as lista (abc, frozen referencia):**  
  `AUDCAD, AUDCHF, AUDDKK, AUDJPY, AUDNZD, AUDSGD, AUDUSD, CADCHF, CADJPY, CHFJPY, CHFSGD, EURAUD, EURCAD, EURCHF, EURCZK, EURDKK, EURGBP, EURHUF, EURJPY, EURMXN, EURNOK, EURNZD, EURPLN, EURSEK, EURSGD, EURTRY, EURUSD, EURZAR, GBPAUD, GBPCAD, GBPCHF, GBPDKK, GBPJPY, GBPNOK, GBPNZD, GBPSEK, GBPSGD, GBPTRY, GBPUSD, GBPZAR, NOKJPY, NOKSEK, NZDCAD, NZDCHF, NZDJPY, NZDSGD, NZDUSD, SEKJPY, SGDJPY, USDCAD, USDCHF, USDCNH, USDCZK, USDDKK, USDHUF, USDJPY, USDMXN, USDNOK, USDPLN, USDSEK, USDSGD, USDTRY, USDZAR`.

### 2.2 Kamat-adat eligibility (meta only — **nincs** rate érték olvasás spec-fázisban)

**MEASURED deposit-rate út (pre-reg):**

| Tier | Devizák | Forrás / repo állapot |
|------|---------|------------------------|
| **A** | USD, EUR, JPY, GBP, AUD, NZD, CHF, CAD | `fetch_fred_rates.py` → `IR3TIB01{US,EZ,JP,GB,AU,NZ,CH,CA}M156N` → `fred_3m_rates.csv` (**in-repo**) |
| **B** | SEK, NOK, DKK | Ugyanaz az OECD **IR3TIB01** család, FRED public CSV: `IR3TIB01SEM156N`, `IR3TIB01NOM156N`, `IR3TIB01DKM156N` — **nincs** még a fetch scriptben; harness prep **kötelező** kiterjesztés (`fetch_fred_rates.py` vagy sibling), audit ugyanazzal a protokollal mint Tier A |
| **— (excluded pre-reg)** | PLN, HUF, CZK, MXN, ZAR, TRY, SGD, CNH | **Nincs** rögzített MEASURED 3M bankközi sor a repóban; külön adat-ADR nélkül **nem** kerülnek a frozen univerzumba |

**Pár eligibility:** mindkét láb devizája ∈ **Tier A ∪ Tier B** (11 deviza). Ebből a 63-ból **41** pár (Tier **B** univerzum, frozen).

**Carry rank proxy (frozen, egyenértékű inputokkal):**  
`carry(pair, m) = rate(base, m−1) − rate(quote, m−1)` (éves %, tradable lag), ahol `BASE`/`QUOTE` = 6-char pair split.  
`channel_gate.cip.pair_diff_carry_bp_per_year` / `cip_theoretical_carry_bp_per_year` **ugyanazokból** a MEASURED deposit rate-ekből származik — **nem** külön rank_key.

### 2.3 Frozen gate univerzum — **41 pár** (`N_PLANNED = 41`)

```text
AUDCAD, AUDCHF, AUDDKK, AUDJPY, AUDNZD, AUDUSD, CADCHF, CADJPY, CHFJPY,
EURAUD, EURCAD, EURCHF, EURDKK, EURGBP, EURJPY, EURNOK, EURNZD, EURSEK, EURUSD,
GBPAUD, GBPCAD, GBPCHF, GBPDKK, GBPJPY, GBPNOK, GBPNZD, GBPSEK, GBPUSD,
NOKJPY, NOKSEK, NZDCAD, NZDCHF, NZDJPY, NZDUSD, SEKJPY,
USDCAD, USDCHF, USDDKK, USDJPY, USDNOK, USDSEK
```

**Tier A-only részhalmaz (28 pár):** mindkét láb G10 — ha Tier B rate fetch **blokkol**, harness **FAIL** `breadth` / `data_prep` (nincs univerzum-szűkítés post-hoc).

**Kizárt 22 pár (ok — nincs MEASURED mindkét láb pre-reg):**  
`AUDSGD, CHFSGD, EURCZK, EURHUF, EURMXN, EURPLN, EURSGD, EURTRY, EURZAR, GBPSGD, GBPTRY, GBPZAR, NZDSGD, SGDJPY, USDCNH, USDCZK, USDHUF, USDMXN, USDPLN, USDSGD, USDTRY, USDZAR`.

**H1 ár cache (2026-07-10 meta):** a 41-ből **11** pár: `AUDJPY, AUDUSD, EURGBP, EURJPY, EURUSD, GBPJPY, GBPUSD, NZDUSD, USDCAD, USDCHF, USDJPY` — mindegyik **2010.01.01 .. 2026.06.01** span. A harness **30** hiányzó H1 sorozatot tölt **gate előtt** (cTrader / meglévő ingest).

### 2.4 Gate naptári ablak (frozen)

- **Naptári:** **`2010-01` .. `2026-06`** (hónap-granularitás, mindkét végpont inkluzív).
- **Rebalance hónapok:** ugyanaz, ahol `|U(m)| ≥ min_rankable_pairs` (§5).
- **Warmup:** **nincs** 12h lookback (carry jel = `m−1` kamat); első gate hó **2010-01**, ha adat OK.

---

## 3. Konstrukció (frozen)

### 3.1 Per-pár havi nettó hozam (irány a rangsor szerint)

Minden `pair ∈ U(m)` (§5.1), hónap `m`:

- **Rangsor kulcs:** `carry(pair, m)` (§2.2).
- **Spot:** hó első kereskedési nap **open** → hó utolsó **close**, mid (H1→D1, carry #3 konvenció).
- **Carry accrual:** `pos · (carry/100)/12` (`pos` = +1 long, −1 short).
- **Költség / financing:** §6 (párszintű).
- **`r_pair(m)`** = spot + carry accrual − spread − **nettó swap/financing** (tagelve).

### 3.2 Keresztmetszeti portfólió (dollar-neutral tertilis)

Az adott hónapban rangsorolható párok száma `M = |U(m)|`:

```text
k = floor(M / 3)
```

- **Long basket:** a `carry` szerinti **top `k`** pár, mindegyik **`pos = +1`**, súly **`+1/k`**.
- **Short basket:** **bottom `k`** pár, **`pos = −1`**, súly **`-1/k`**.
- **Middle:** `M − 2k` pár **flat** (0 súly).
- **`r_p(m) = Σ w_i · r_i(m)`** — long és short oldal abszolút notional egyenlő (**dollar-neutral**).

**Frozen:** **tercilis** (nem kvintilis) — stabilabb `k` 41 párnál; kvintilis **TILOS** post-hoc váltás.

### 3.3 Vak döntések (LOCKED)

| Paraméter | Érték |
|-----------|--------|
| Univerzum | **41** pár (§2.3) |
| Rangsor | **Pár szintű** kamatkülönbség |
| Bucket | **Tercil** long / short / flat |
| Súlyozás | **Equal-weight** long és short kosáron belül |
| Rebalance | **Havi** (carry #3 / #4 konzisztencia) |
| Skála | Sharpe / Calmar **scale-invariáns** (nincs leverage tuning) |

---

## 4. Mérési protokoll

- Havi **`r_p(m)`** sorozat a gate ablakon.
- **Sharpe** = `mean(r_p)/std(r_p) × √12`.
- **Calmar** = `(mean(r_p)×12) / |max DD|` (kumulált compounded equity DD).
- **Sub-periódusok (frozen):** **H1** `2010-01`..`2017-12`, **H2** `2018-01`..`2026-06` — külön Sharpe mindegyikre.
- **Pozitív-év arány:** pozitív naptári éves összegű évek / gate évek ≥ **0.60** (carry #4 precedens).

---

## 5. Gate (pre-reg blind checks — frozen)

**Verdict:** `CROSS_SECTIONAL_FX_CARRY_RP_PASS` iff **ALL**; különben `CROSS_SECTIONAL_FX_CARRY_RP_FAIL_PARK`.

| check_id | rule |
|----------|------|
| `sharpe_ge_0_40` | Teljes ablak ann. nettó Sharpe **≥ 0.40** |
| `bootstrap_ci_lower_gt_0` | Block bootstrap **95%** CI lower on Sharpe **> 0**; block=**6** hó, **n=5000**, seed=**20260602** (TSMOM / sleeve_2 precedens) |
| `both_subperiods_sharpe_gt_0` | Sharpe **> 0** H1 **és** H2 (§4) |
| `calmar_ge_0_30` | Calmar **≥ 0.30** |
| `min_120_monthly_obs` | **≥ 120** havi `r_p` obs a gate ablakon (carry #4 precedens) |
| `positive_year_fraction_ge_0_60` | Pozitív-év arány **≥ 0.60** |
| `fraction_months_with_min_universe_size` | **= 1.00** (minden gate hónap): rangsorolható párok `|U(m)| ≥ min_rankable_pairs` |
| `detectability_artifact_present` | Harness JSON tartalmazza a §1.1 `detectability_gate` blokkot (informative, **nem** PASS feltétel) |

### 5.1 Breadth definíciók (frozen)

```text
N_PLANNED           = 41
min_rankable_pairs  = floor(0.80 × N_PLANNED) = floor(32.8) = 32
U(m)                = { pair ∈ frozen list : MEASURED rate both legs at m−1
                        AND valid D1 OHLC for m AND not excluded by cost model hard-fail }
fraction_months_with_min_universe_size
                    = (# months m in gate window with |U(m)| ≥ min_rankable_pairs)
                      / (# months in gate window)
```

**PASS követelmény:** `fraction_months_with_min_universe_size >= 1.00` — **egyetlen** hónap sem lehet „csendben” szűk univerzummal.

**Harness riport:** havi `|U(m)|` histogram, worst month, első/utolsó hónap ahol `< 32`.

---

## 6. Költség és financing (párszintű — **nem** class-aggregát)

**Elv:** FX carry-nél van **páronkénti** swap/capture infrastruktúra (cTrader scan, `gate_net_of_swap_markup`, `build_ctrader_demo_capture_v1.py`); **nem** a TSMOM `instrument_class` aggregát modell.

| Költségleg | Szabály | Provenance |
|------------|---------|------------|
| Spread + slippage | `(spread_entry + 0.7·pip) / entry_mid` round-trip ekvivalens (carry #3) | **MEASURED** spread entry-napról, ha elérhető; különben **ASSUMED** `0.7 pip` slippage tag |
| Overnight swap / financing | Párszintű **nettó** swap a tartási időre (havi hold) | **`MEASURED`** per pair/channel ha `reports/channel/` vagy scan JSON tartalmazza; **`ASSUMED`** explicit param + **`AssumedCaptureError`** ha ADR-039 gate math **MEASURED**-et vár — harness: primary backtest **MEASURED** swap ahol van, **ASSUMED** sensitivity sor **külön** (nem PASS) |
| CIP theoretical carry | Csak **diagnosztika** / expected vs realized | `cip.py` — **nem** helyettesíti MEASURED swap-ot PASS-nál |

**Kötelező artifact mezők:** `cost_ledger[]` per pair per month: `spread`, `financing`, `provenance_spread`, `provenance_financing`.

**Channel gate:** deploy / live order továbbra is `channel_capture_gate` **MEASURED** capture (ADR-039).

---

## 7. Implementáció (következő lépés — **NOT in scope for LOCK**)

- Script (javasolt): `fxaiea_data_root/db/scripts/cross_sectional_fx_carry_gate.py` (vagy TP_sleeve sibling).
- Betöltő: `carry_rate_differential` H1→D1 + kiterjesztett `fred_3m_rates.csv` (11 deviza).
- Kimenet: `models/cross_sectional_fx_carry_gate_v1.json` + markdown report.
- **Előfeltétel:** H1 backfill **30** párra; FRED **SEK/NOK/DKK** audit.

---

## 8. Tiltott utólagos lépések (ADR-034 §8)

- Tercil → kvintilis, `N_PLANNED` szűkítés, rangsor-kulcs, `min_rankable_pairs` / **80%** frakció módosítása eredmény után
- Sharpe / Calmar / bootstrap param hangolás
- Gyenge subperiod kihagyása
- **`carry_factor_risk_premium_gate` újranyitása** „ugyanaz a carry” indokkal

---

## 9. Definition of Done (spec-fázis, 2026-07-10)

- [x] Spec **LOCKED** ezen fájlban
- [x] **Detectability pre-check** **MEASURED** H1 meta-val (11/41 közös **198** hó, §1.1) — **nem** a régi 7-pár feltételezés
- [x] **`fraction_months_with_min_universe_size`** bekötve PASS-ként (§5)
- [ ] Harness + H1/FRED Tier B prep (következő prompt)
- [ ] Gate futás + `FINAL_VERDICT` (még nincs)

---

## 10. Explicit különbség — **NEM** a `carry_factor_risk_premium_gate` újranyitása

| | **D1 #4 `carry_factor_risk_premium_gate`** | **Ez a spec (`CROSS_SECTIONAL_FX_CARRY`)** |
|---|---------------------------------------------|---------------------------------------------|
| **Statisztikai objektum** | Egy **aggregált** havi idősor: `factor_ret(m)` | **Keresztmetszeti** rangsor **párok** között minden `m`-ben |
| **Univerzum** | **7** nem-USD G10 deviza → USD páron keresztül | **41** FX **pár** (cTrader 63-ból, Tier A+B rate) |
| **Rangsor kulcs** | Deviza **kamatszint** `rate(c)` | Pár **kamatkülönbség** `rate(base)−rate(quote)` |
| **Pozíció** | Top-2 / bottom-2 **deviza** kosár | Top/bottom **tercilis párok** |
| **Breadth / erő** | Idő sor hossza dominál (7 elem × sok hó) | **Cross-sectional breadth** (41 páras szórás) — **új** konstrukció |
| **Gate státusz #4** | **FAIL/PARK** standalone (Sharpe 0.282) — **lezárt család** | **Új** blind spec; eredmény **független** család |

**Integritás:** A pozitív D1 #3 EV **nem** indokolja #4 gate lazítást; ez a spec **szándékosan** más hipotézis-test (breadth vs aggregált faktor), **frozen** küszöbökkel **előre**.

---

## 11. Kapcsolódó fájlok

- `FXCarry/db/scripts/carry_factor_risk_premium_gate.py` — **referencia**, nem módosítandó e spec miatt
- `FXCarry/src/carry_sleeve/config.py` — `CCY_PAIR`, `TOP_K=2` (**deviza** faktor, **nem** ez a gate)
- `FXCarry/src/channel_gate/cip.py` — deposit-rate / carry diff **proxy** definíció
- `FXAIEA/db/scripts/fetch_fred_rates.py` — Tier A; Tier B extension kötelező prep
