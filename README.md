# PoE2 Tablet Market Intelligence

Hosted Path of Exile 2 tool that snapshots tablet trade listings, infers likely sales from disappearances, and surfaces sell-side affix lift, magic craft edges, buy signals, and stash regex strings.

## Requirements

- Python 3.11+
- PoE account session cookie (`POESESSID`)

## Setup

```bash
cp .env.example .env
# Edit .env and set POE_SESSION_ID

pip install -e ".[dev]"
```

## Run

**Collector + embedded API (recommended):**

```bash
poe-tablet-tool
```

Open http://localhost:8001 for the dashboard.

**API only** (if scheduler runs elsewhere):

```bash
poe-tablet-api
```

## Docker

```bash
docker compose up -d
```

Mounts `./data` for the SQLite database and `./logs` for scheduler logs.

## What it does

1. Detects the current league and archives on rollover
2. Every hour, staggers snapshots across 8 tablet types × 2 modes (rare 4–5 mod / magic 2 mod)
3. Dual-sort fetches (cheapest + most expensive) for better market coverage
4. Normalizes prices to divine via configurable exchange rates
5. Diffs snapshots → `likely_sold`, `relisted`, or `uncertain`
6. Runs analyzers → affix lift, seed pairs, craft edge, regex outputs
7. Serves reports at `/api/reports/*` and `/api/health`

## Configuration

See `.env.example`. Key settings:

| Variable | Purpose |
|---|---|
| `PRICE_MIN_DIVINE_RARE` | Rare query price floor (default 1 div) |
| `PRICE_MIN_DIVINE_MAGIC` | Magic floor (default 0 — collect cheap bases) |
| `CHAOS_PER_DIVINE` | Currency normalization |
| `BUY_SIGNAL_*` | Craft opportunity thresholds |

## Tests

```bash
pytest
```

## Project layout

```
poe_tablet_tool/
  scheduler.py      # Main worker
  api.py            # FastAPI dashboard + reports
  scraper.py        # Trade API client
  differ.py         # Disappearance classification
  rare_analyzer.py  # Sell-side affix lift
  magic_analyzer.py # 2-mod seed pairs
  buy_signal_engine.py
  regex_builder.py
static/dashboard.html
```

Full design doc: `poe2_tablet_market_intelligence_project_doc.md`
