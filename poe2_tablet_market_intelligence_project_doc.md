# PoE2 Tablet Market Intelligence — Project Document

## Overview

A hosted league-only Path of Exile 2 tool that identifies:

1. **Which 4–5 affix tablets sell well** in the current league.
2. **Which 2-mod magic tablets are good project-craft candidates** because their seed mods are associated with premium rare tablet outcomes.
3. **Which regex strings to use in stash search** so you can quickly highlight tablets worth selling or crafting.

The tool works by taking repeated snapshots of PoE2 trade listings, diffing snapshots over time to infer likely sales, analyzing affix patterns on expensive and fast-moving tablets, and converting those findings into both sell-side and buy-side signals.

**Core questions answered:**
- What tablet affixes are buyers paying for right now?
- Which rare tablets in my stash are likely high value?
- Which 2-mod magic tablets should I buy or keep to project-craft into profitable rares?
- Which regex strings should I paste into PoE2 stash search to surface those items instantly?

---

## Product Scope

### Primary Use Cases

- **Sell-side discovery:** find the 4–5 mod tablets that consistently command premium value.
- **Craft-side discovery:** find the 2-mod magic tablets that act as strong seeds for profitable regal/project crafting.
- **Stash triage:** generate compact regex strings for PoE2 stash search so valuable tablets are easy to spot.
- **League intelligence:** operate only on the current league economy, with automatic league rollover handling.

### Operating Assumptions

- This tool is **hosted**, not local-only.
- This tool is **league-specific** and should always target the **current active league**.
- This tool should analyze **all tablet types**, not a hand-picked subset.
- The price threshold for “expensive” should be discovered from data after collection begins, not hard-coded up front.
- Rare-tablet sell analysis should focus on **4–5 affix tablets**.
- Magic-tablet craft analysis should focus on **2-mod tablets**.
- Combo-level analysis beyond 2-mod seed pairs can be deferred until after the skeleton is stable.

---

## Goals

- Identify affixes that correlate with high-value rare tablet sales.
- Measure which tablets disappear from listings quickly enough to act as likely sold signals.
- Separate market analysis into two tracks: **rare sell track** and **magic craft track**.
- Surface actionable project-craft opportunities from currently listed 2-mod magic tablets.
- Generate regex strings compatible with PoE2 stash highlighting workflows.
- Archive or reset cleanly on league transitions.

---

## Non-Goals

- This is not a fully generic PoE2 item pricing engine.
- This is not a live trading bot or auto-buyer.
- This is not a permanent historical economy archive across leagues.
- This does not need advanced combo crafting simulations in the first build.
- This does not need mod tier analysis in the first build.

---

## Core Concepts

### 1. Rare Sell Track

This track studies **4–5 affix tablets** and answers:

> Which affixes and tablet archetypes appear on the listings that are most likely to sell well?

This is the “what should I sell / what in my stash is valuable?” side of the tool.

### 2. Magic Craft Track

This track studies **2-mod magic tablets** and answers:

> Which 2-mod tablets are attractive starting points for regal/project crafting because their seed mods map into premium rare outcomes?

This is the “what should I buy / what should I keep for crafting?” side of the tool.

### 3. Regex Output Track

This track transforms sell-side and craft-side findings into compact stash-search regex strings so you can instantly locate:

- rare tablets worth listing,
- magic tablets worth keeping,
- magic tablets worth buying as project bases.

---

## Architecture Overview

```text
┌──────────────────────────────────────────────────────────────┐
│                    Hosted Scheduler                         │
│      cron / worker / job queue on an always-on server       │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                  League Detection Layer                     │
│  discovers current league, detects league rollover/reset    │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                     Snapshot Scraper                        │
│ /trade2/search + /trade2/fetch for all tablet types         │
│ separate query modes for rare-track and magic-track         │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    Persistence Layer                        │
│ SQLite or Postgres: snapshots, listings, affixes, rates     │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                     Snapshot Differ                         │
│ compares old vs new snapshots, flags likely sold records    │
│ separates relists / price edits / uncertain disappearances  │
└──────────────────────────────┬───────────────────────────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
┌───────────────────────────────┐   ┌──────────────────────────┐
│      Rare Sell Analyzer       │   │    Magic Craft Analyzer  │
│  4–5 mod tablets              │   │  2-mod tablets           │
│  affix frequency, lift, EV    │   │  seed pairs, edge, risk  │
└───────────────┬───────────────┘   └─────────────┬────────────┘
                │                                 │
                └──────────────┬──────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                 Regex + Reporting Layer                     │
│ sell regex, craft regex, ranked reports, stash helpers      │
└──────────────────────────────────────────────────────────────┘
```

---

## Data Flow

1. The scheduler wakes on a fixed cadence.
2. The league detector confirms the current league and verifies whether a reset/archive is needed.
3. The scraper runs queries for every tablet type in two modes:
   - **rare mode**: 4–5 affix tablets,
   - **magic mode**: 2-mod tablets.
4. Search results are fetched and normalized into structured listings.
5. Listings and parsed affixes are written to the database.
6. The differ compares the latest snapshot against the prior snapshot window for the same tablet type and mode.
7. Disappeared listings are classified as likely sold, relisted, or uncertain.
8. The rare analyzer computes affix and archetype performance.
9. The magic analyzer computes project-craft opportunities from seed pairs.
10. The regex builder emits stash-search strings for sell-side and craft-side use.
11. Reports are rendered for dashboard/CLI/export consumption.

---

## Deployment Model

### Hosted Runtime

Recommended deployment options:
- Small VPS
- Docker container on a home server
- Cloud VM / Fly.io / Railway / Render background worker

### Service Layout

- **Worker service:** runs snapshots and analysis jobs.
- **Database service:** SQLite for v1, Postgres if concurrency grows.
- **Optional web UI:** static or lightweight app for viewing reports.

### Why Hosted

Because the tool depends on time-separated snapshots, data quality improves dramatically when collection runs continuously, including overnight and during your offline hours.

---

## League Handling

### League Policy

This tool should always target the **current league only**.

### Requirements

- Detect current trade league automatically at startup.
- Store league name with every snapshot and listing.
- On league rollover:
  - archive prior league DB or export summary,
  - initialize a clean working dataset,
  - reset thresholds and fresh-market assumptions.

### Modules

- `league_detector.py`
- `league_reset.py`

---

## Query Modes

### Rare Query Mode

Purpose: identify sellable rare tablets.

Filters:
- tablet item class/type
- current league
- **4–5 total affixes**
- optionally 10 uses remaining if that proves important during analysis
- open-ended price collection at first; thresholds derived later

### Magic Query Mode

Purpose: identify project-craftable bases.

Filters:
- tablet item class/type
- current league
- **exactly 2 total affixes**
- open-ended price collection at first; thresholds derived later

### Tablet Coverage

All supported tablet types should be included via a registry/config layer rather than hard-coded one-offs.

---

## Snapshot Strategy

### Default Cadence

Start with a **1-hour effective comparison window per tablet type and mode**.

### Staggering Strategy

Do not burst all tablet types at once. Instead:
- spread query jobs across the hour,
- rotate tablet types and query modes,
- preserve an approximately consistent diff interval for each category.

### Why

This reduces rate-limit pressure while preserving meaningful disappearance signals.

---

## Database Schema

### `leagues`

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `name` | TEXT UNIQUE | League name |
| `started_at` | DATETIME | First observed time |
| `ended_at` | DATETIME NULL | Set on rollover |
| `is_active` | BOOLEAN | Current working league |

### `snapshots`

Tracks each scrape run.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `league_id` | INTEGER FK | `leagues.id` |
| `tablet_type` | TEXT | e.g. `ritual`, `breach` |
| `query_mode` | TEXT | `rare` or `magic` |
| `taken_at` | DATETIME | UTC timestamp |
| `listing_count` | INTEGER | Listings fetched |
| `query_hash` | TEXT | Normalized query signature |

### `listings`

One row per item per snapshot observation.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `snapshot_id` | INTEGER FK | `snapshots.id` |
| `league_id` | INTEGER FK | `leagues.id` |
| `item_id` | TEXT | Stable item/listing identifier |
| `tablet_type` | TEXT | Denormalized for convenience |
| `query_mode` | TEXT | `rare` or `magic` |
| `affix_count` | INTEGER | Total affixes on tablet |
| `uses_remaining` | INTEGER | 1–10 if available |
| `price_amount` | REAL | Raw listed amount |
| `price_currency` | TEXT | e.g. div, exalt, chaos |
| `price_chaos` | REAL | Normalized chaos value |
| `price_divine` | REAL | Normalized divine value |
| `seller_name` | TEXT NULL | If exposed |
| `first_seen_at` | DATETIME | First observed timestamp |
| `last_seen_at` | DATETIME | Last observed timestamp |
| `disappeared_at` | DATETIME NULL | First missing timestamp |
| `status` | TEXT | `active`, `likely_sold`, `relisted`, `uncertain`, `expired` |
| `raw_json` | TEXT | Full fetched payload |

### `affixes`

One row per affix per listing observation.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `listing_id` | INTEGER FK | `listings.id` |
| `item_id` | TEXT | Convenience key |
| `slot` | TEXT | `prefix`, `suffix`, `unknown` |
| `mod_id` | TEXT | Internal/normalized identifier |
| `mod_text` | TEXT | Human-readable text |
| `value_min` | REAL NULL | Parsed roll low |
| `value_max` | REAL NULL | Parsed roll high |
| `mod_index` | INTEGER | Order within tooltip |

### `exchange_rates`

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `league_id` | INTEGER FK | `leagues.id` |
| `taken_at` | DATETIME | Snapshot time |
| `base_currency` | TEXT | e.g. `divine` |
| `quote_currency` | TEXT | e.g. `chaos` |
| `rate` | REAL | Conversion rate |

### `listing_disappearances`

Explicit disappearance classification record.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `item_id` | TEXT | Listing/item identifier |
| `tablet_type` | TEXT | |
| `query_mode` | TEXT | `rare` or `magic` |
| `old_snapshot_id` | INTEGER FK | Prior snapshot |
| `new_snapshot_id` | INTEGER FK | Later snapshot |
| `classified_as` | TEXT | `likely_sold`, `relisted`, `uncertain`, `expired` |
| `confidence` | REAL | 0.0–1.0 |
| `reason` | TEXT | Heuristic summary |
| `created_at` | DATETIME | |

### `rare_affix_stats`

Materialized sell-side aggregation for 4–5 mod tablets.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `league_id` | INTEGER FK | `leagues.id` |
| `tablet_type` | TEXT | |
| `mod_id` | TEXT | |
| `slot` | TEXT | `prefix` or `suffix` |
| `mod_text` | TEXT | |
| `sold_count` | INTEGER | Likely sold appearances |
| `active_count` | INTEGER | Current active appearances |
| `sold_frequency` | REAL | sold_count / total sold |
| `active_frequency` | REAL | active_count / total active |
| `lift` | REAL | sold_frequency / active_frequency |
| `median_sold_price_div` | REAL | Median sold price |
| `avg_time_to_disappear_hours` | REAL | Sell velocity proxy |
| `updated_at` | DATETIME | |

### `rare_tablet_archetypes`

Aggregated archetype stats for whole 4–5 mod tablets.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `league_id` | INTEGER FK | `leagues.id` |
| `tablet_type` | TEXT | |
| `signature` | TEXT | Canonical mod signature |
| `mod_count` | INTEGER | 4 or 5 |
| `sold_count` | INTEGER | Likely sold count |
| `median_sold_price_div` | REAL | |
| `avg_time_to_disappear_hours` | REAL | |
| `updated_at` | DATETIME | |

### `magic_seed_pairs`

Aggregated stats for 2-mod magic tablets.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `league_id` | INTEGER FK | `leagues.id` |
| `tablet_type` | TEXT | |
| `mod_a_id` | TEXT | Normalized smaller key |
| `mod_b_id` | TEXT | Normalized larger key |
| `mod_a_text` | TEXT | |
| `mod_b_text` | TEXT | |
| `magic_sold_count` | INTEGER | Likely sold magic tablets with this pair |
| `magic_median_price_div` | REAL | Median sold magic price |
| `magic_avg_time_to_disappear_hours` | REAL | Velocity proxy |
| `updated_at` | DATETIME | |

### `crafting_edge`

Core project-crafting opportunity table.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `league_id` | INTEGER FK | `leagues.id` |
| `tablet_type` | TEXT | |
| `mod_a_id` | TEXT | |
| `mod_b_id` | TEXT | |
| `mod_pair_key` | TEXT | Sorted canonical pair |
| `magic_buy_price_div` | REAL | Cheapest live magic buy |
| `magic_median_price_div` | REAL | Historic sold median for the 2-mod base |
| `rare_median_price_div` | REAL | Median rare sale among rares containing both mods |
| `regal_cost_div` | REAL | Current regal-equivalent cost |
| `expected_profit_div` | REAL | rare_median - magic_buy_price - regal_cost |
| `junk_rate` | REAL | Fraction of outcomes/market comps that underperform threshold |
| `confidence` | REAL | Based on sample size and stability |
| `is_buy_signal` | BOOLEAN | Whether edge meets rule |
| `updated_at` | DATETIME | |

### `regex_outputs`

Generated stash-search strings.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `league_id` | INTEGER FK | `leagues.id` |
| `tablet_type` | TEXT NULL | Specific tablet or null for global |
| `regex_mode` | TEXT | `sell_rare`, `keep_magic`, `buy_magic` |
| `label` | TEXT | Human-friendly title |
| `regex_text` | TEXT | Copy/pasteable string |
| `char_count` | INTEGER | Length check |
| `source_summary` | TEXT | What drove generation |
| `updated_at` | DATETIME | |

---

## Differ Logic

The differ is the heart of the market inference model.

### Input

- prior snapshot for a given `league + tablet_type + query_mode`
- latest snapshot for the same group

### Output

For each listing that disappears:
- `likely_sold`
- `relisted`
- `uncertain`
- `expired`

### Heuristics

Use a confidence-weighted rule set:

- Disappeared and a near-identical listing reappears at a different price soon after → **relisted**.
- Disappeared with no near-match replacement and had reasonable market price → **likely_sold**.
- Disappeared during noisy windows or with weak comparables → **uncertain**.
- Disappeared after a known listing timeout boundary → **expired**.

The first build can keep this simple and conservative. It is better to undercount likely sales than to contaminate the sold set with aggressive false positives.

---

## Sell-Side Analytics

### Objective

Find the affixes and archetypes associated with premium rare tablets.

### Main Metrics

- sold count
- active count
- sold frequency
- active frequency
- lift
- median sold price
- average time to disappearance

### Lift Formula

```text
lift = (sold_count / total_sold) / (active_count / total_active)
```

### Why Lift Matters

A mod can be common without being premium. Lift helps identify affixes that are over-represented among likely sold listings, rather than simply common in the market at large.

### Example Questions Answered

- Which suffixes show up most often on likely sold Ritual tablets?
- Which rare tablet archetypes disappear fastest?
- Which affixes are common in active listings but underrepresented in sold ones?

---

## Craft-Side Analytics

### Objective

Identify 2-mod magic tablets that are worth buying or keeping because they seed strong rare outcomes.

### Core Logic

For each 2-mod pair:
1. Measure the historical sold price of that magic pair.
2. Measure the median rare sale price of rare tablets containing both seed mods.
3. Pull the cheapest current live listing for that 2-mod pair.
4. Subtract current buy price and regal cost.
5. Estimate risk via junk rate and confidence.

### Project-Craft Edge Formula

```text
expected_profit_div = rare_median_price_div - magic_buy_price_div - regal_cost_div
```

### Interpretation

- Positive value: potential craft opportunity.
- Negative value: selling or skipping is better.

### Junk Rate

A risk metric that estimates how often the downstream rare outcome market underperforms.

A simple v1 definition:

```text
junk_rate = comps_below_profit_floor / total_comps
```

Where the profit floor can be based on:
- current magic buy price + regal cost,
- or another conservative threshold chosen after initial data review.

### Example Questions Answered

- Which 2-mod magic Ritual tablets are underpriced relative to rare outcomes?
- Which seed pairs have the best expected edge but unacceptable junk rate?
- Which project bases are worth buying right now off the trade site?

---

## Buy Signal Engine

This is the actionable market-opportunity layer.

### Purpose

Convert seed-pair analytics into live shopping opportunities.

### Inputs

- high-confidence seed pairs from `crafting_edge`
- current live trade listings for matching 2-mod tablets
- current regal cost

### Output Fields

- tablet type
- 2-mod pair
- cheapest buy price
- rare median sale price
- expected profit
- junk rate
- confidence

### Rule Example

A listing becomes a buy signal if:
- expected profit is above threshold,
- junk rate is below threshold,
- confidence is above threshold,
- live listing price is still current.

Thresholds should be tuned after initial data collection rather than locked in on day one.

---

## Regex Builder

### Purpose

Generate stash-search strings you can paste into PoE2 stash highlighting workflows.

### Output Modes

1. **Sell Rare Regex**
   - highlights 4–5 mod tablets matching top-value rare traits.
2. **Keep Magic Regex**
   - highlights 2-mod magic tablets that are promising craft bases if already in your stash.
3. **Buy Magic Regex**
   - highlights the mod phrases most relevant to live buy-signal searches and stash triage.

### Builder Rules

- Prefer short, distinctive substrings from mod text.
- Join terms with `|`.
- Respect PoE stash search character constraints.
- Split into multiple regex strings when needed.
- Preserve per-tablet variants if certain affixes are only meaningful in one tablet family.

### Integration Direction

The output should be easy to adapt into tooling and workflows similar to `poe2.re`, so the project can eventually emit prebuilt regex presets derived from real tablet market data.

---

## Tablet Registry

Maintain all supported tablet types in one config source.

```python
TABLET_TYPES = {
    "ritual": {"label": "Ritual Tablet"},
    "breach": {"label": "Breach Tablet"},
    "expedition": {"label": "Expedition Tablet"},
    "delirium": {"label": "Delirium Tablet"},
    # extend as league content requires
}
```

No tablet family should be excluded in the base design.

---

## Modules

### `league_detector.py`
- discovers the current active league
- exposes the league name to all query builders
- verifies that the configured working league matches reality

### `league_reset.py`
- archives previous league artifacts
- creates a fresh working dataset on rollover
- resets cached thresholds and summaries

### `query_builder.py`
- builds rare-mode and magic-mode trade queries
- standardizes tablet-type filters
- keeps query payloads reproducible via hashes

### `scraper.py`
- calls search endpoint
- batches fetch endpoint calls
- normalizes listing payloads
- returns structured listing models

### `parser.py`
- extracts affix count
- parses mod lines
- normalizes mod IDs and text
- classifies prefix/suffix when possible

### `snapshot_store.py`
- writes snapshots and listings
- handles upserts on recurring item IDs
- stores raw JSON for reprocessing

### `differ.py`
- compares snapshots for the same tablet type/mode
- classifies disappeared listings
- records confidence and reasons

### `rate_provider.py`
- refreshes currency conversion data
- normalizes prices into chaos and divine equivalents

### `rare_analyzer.py`
- computes sell-side affix stats
- computes rare archetype signatures
- ranks affixes by lift and price behavior

### `magic_analyzer.py`
- aggregates 2-mod seed pairs
- measures magic price/velocity stats
- connects seed pairs to rare outcomes

### `buy_signal_engine.py`
- evaluates live cheapest listings against expected value
- flags actionable project-craft opportunities

### `regex_builder.py`
- emits PoE2 stash-search strings
- outputs sell-side and craft-side regex sets

### `report_builder.py`
- renders markdown, JSON, CLI, or HTML views
- publishes compact summaries for quick review

---

## Suggested Scheduler Layout

Example 60-minute cycle:

| Minute | Job |
|---|---|
| :00 | Rare snapshot for tablet group A |
| :10 | Magic snapshot for tablet group A |
| :20 | Rare snapshot for tablet group B |
| :30 | Magic snapshot for tablet group B |
| :40 | Rare snapshot for tablet group C |
| :50 | Magic snapshot for tablet group C + analysis jobs |

Alternative: schedule each tablet type individually if the worker framework makes that cleaner.

The important part is consistency, not the exact minute map.

---

## Threshold Strategy

Do **not** hard-code expensive thresholds on day one.

### Phase 1

Collect broad price data for:
- all 4–5 mod rare tablets,
- all 2-mod magic tablets.

### Phase 2

After enough samples accumulate, derive thresholds from observed distributions:
- top percentile cutoffs,
- tablet-type-specific medians,
- velocity-adjusted premium bands.

### Why

Tablet families may have very different value distributions. A fixed threshold can distort the analysis early.

---

## Output Views

### 1. Rare Sell Report

For each tablet type:
- top affixes by lift,
- top rare archetypes by median sold price,
- fastest-disappearing rare patterns,
- suggested sell regex strings.

### 2. Magic Seed Report

For each tablet type:
- top 2-mod seed pairs,
- median magic price,
- relation to premium rare outcomes,
- suggested keep regex strings.

### 3. Buy Signal Report

For each tablet type:
- currently listed underpriced 2-mod magic tablets,
- expected profit,
- junk rate,
- confidence,
- suggested buy regex strings.

### 4. Stash Utility Report

A compact “what should I search for in stash right now?” output.

---

## Example Output Tables

### Rare Sell Table

| Tablet Type | Mod | Slot | Lift | Median Sold Price | Avg Disappear Time |
|---|---|---|---|---|---|
| Ritual | Increased Quantity of Items | Prefix | 2.4 | 4.8 div | 1.9h |
| Ritual | Pack Size | Prefix | 2.1 | 4.2 div | 2.3h |

### Magic Craft Table

| Tablet Type | Seed Pair | Magic Median | Rare Median | Expected Profit | Junk Rate |
|---|---|---|---|---|---|
| Ritual | Quantity + Pack Size | 0.4 div | 4.8 div | 3.6 div | 0.18 |
| Breach | Quantity + Rarity | 0.3 div | 3.2 div | 2.1 div | 0.27 |

Values above are illustrative placeholders for schema design only.

---

## Tech Stack

| Component | Recommended Choice | Reason |
|---|---|---|
| Language | Python 3.11+ | Fast iteration, mature HTTP/data stack |
| HTTP client | `httpx` | Retry and async support |
| DB v1 | SQLite | Low-friction initial build |
| DB v2 | Postgres | Better for scaling hosted workloads |
| Scheduling | cron / APScheduler / Celery beat | Reliable recurring jobs |
| Reporting | Markdown + HTML + CLI | Easy review and Obsidian-friendly export |
| Config | `.env` + pydantic settings | Easy ops |

---

## Config Skeleton

```env
APP_ENV=production
DATABASE_URL=sqlite:///data/poe2_tablets.db
SNAPSHOT_INTERVAL_MINUTES=60
CURRENT_LEAGUE_AUTO=true
ARCHIVE_ON_LEAGUE_RESET=true
ENABLE_WEB_UI=false
LOG_LEVEL=INFO
```

Optional later thresholds:

```env
BUY_SIGNAL_MIN_PROFIT_DIV=1.0
BUY_SIGNAL_MAX_JUNK_RATE=0.30
BUY_SIGNAL_MIN_CONFIDENCE=0.60
```

These should remain tentative until real market data exists.

---

## Roadmap

### Phase 1 — Skeleton
- league detection
- query builder
- scraper
- parser
- DB schema
- snapshot storage
- differ

### Phase 2 — First Analytics
- rare sell analyzer
- magic seed analyzer
- report builder
- manual review of threshold distributions

### Phase 3 — Craft Edge
- buy signal engine
- junk rate tuning
- confidence scoring
- regex builder

### Phase 4 — Quality of Life
- dashboard/web UI
- exports for Obsidian notes
- prebuilt regex presets
- league rollover archive summaries

### Deferred
- 3-mod combo modeling
- advanced craft simulations
- richer archetype clustering

---

## Risks and Limitations

- There is no true public global sold-history feed, so disappearance remains a proxy.
- Price edits and relists can contaminate naive sale inference.
- Early-league markets move fast enough that thresholds will drift.
- Sample sizes may be weak for niche tablet types at first.
- Regex strings are constrained by stash-search usability and length.
- Current-league-only focus means long-term historical trend analysis is intentionally limited.

---

## Final Product Vision

This tool should eventually give you a single practical loop:

1. **See which 4–5 mod tablets sell well.**
2. **See which 2-mod magic tablets can be bought or kept as profitable project bases.**
3. **Paste generated regex into stash search and immediately find those items.**
4. **Use current-league data only, so the results stay economically relevant.**

In plain terms, the tool becomes:

> “Here are the rare tablets the market wants, and here are the 2-mod magic tablets you could buy or keep to craft toward those outcomes.”
