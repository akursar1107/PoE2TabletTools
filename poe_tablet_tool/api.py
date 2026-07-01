"""
FastAPI read layer for dashboard and external consumers.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import poe_tablet_tool.report_builder as report_builder
from poe_tablet_tool.config import settings
from poe_tablet_tool.health import get_all_health

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="PoE2 Tablet Market Intelligence", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _league_id() -> int:
    league_id = report_builder.get_active_league_id()
    if league_id is None:
        raise HTTPException(status_code=503, detail="No active league in database")
    return league_id


@app.get("/")
def index() -> FileResponse:
    path = STATIC_DIR / "index.html"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(path)


@app.get("/dashboard")
def dashboard() -> FileResponse:
    path = STATIC_DIR / "dashboard.html"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="dashboard.html not found")
    return FileResponse(path)


@app.get("/api/health")
def health() -> dict:
    league_id = report_builder.get_active_league_id()
    jobs = get_all_health()
    stale = [j for j in jobs if j.get("last_success_at") is None]
    return {
        "status": "ok" if league_id else "no_league",
        "league_id": league_id,
        "jobs_total": len(jobs),
        "jobs_without_success": len(stale),
        "jobs": jobs,
    }


@app.get("/api/reports/summary")
def report_summary() -> dict:
    league_id = _league_id()
    return {
        "affix_frequency": report_builder.affix_frequency(league_id),
        "affix_price": report_builder.affix_price(league_id),
        "affix_velocity": report_builder.affix_velocity(league_id),
        "price_over_time": report_builder.price_over_time(league_id),
        "price_distribution": report_builder.price_distribution(league_id),
        "affix_combos": report_builder.affix_combos(league_id),
        "rare_affix_lift": report_builder.rare_affix_lift(league_id),
        "buy_signals": report_builder.buy_signals(league_id),
        "regex_outputs": report_builder.regex_outputs(league_id),
    }


@app.get("/api/reports/affix-frequency")
def api_affix_frequency() -> list[dict]:
    return report_builder.affix_frequency(_league_id())


@app.get("/api/reports/affix-price")
def api_affix_price() -> list[dict]:
    return report_builder.affix_price(_league_id())


@app.get("/api/reports/affix-velocity")
def api_affix_velocity() -> list[dict]:
    return report_builder.affix_velocity(_league_id())


@app.get("/api/reports/price-over-time")
def api_price_over_time() -> list[dict]:
    return report_builder.price_over_time(_league_id())


@app.get("/api/reports/price-distribution")
def api_price_distribution() -> list[dict]:
    return report_builder.price_distribution(_league_id())


@app.get("/api/reports/affix-combos")
def api_affix_combos() -> list[dict]:
    return report_builder.affix_combos(_league_id())


@app.get("/api/reports/rare-affix-lift")
def api_rare_affix_lift() -> list[dict]:
    return report_builder.rare_affix_lift(_league_id())


@app.get("/api/reports/buy-signals")
def api_buy_signals() -> list[dict]:
    return report_builder.buy_signals(_league_id())


@app.get("/api/reports/regex")
def api_regex() -> list[dict]:
    return report_builder.regex_outputs(_league_id())


@app.get("/api/reports/normal-prices")
def api_normal_prices() -> dict:
    league_id = _league_id()
    return {
        "prices": report_builder.normal_prices(league_id),
        "history": report_builder.normal_price_history(league_id),
    }


@app.get("/normal-prices")
def normal_prices_dashboard() -> FileResponse:
    path = STATIC_DIR / "normal_prices.html"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="normal_prices.html not found")
    return FileResponse(path)


@app.get("/api/health/detailed")
def detailed_health() -> dict:
    """Detailed health check including PoE API status, DB health, and snapshot times."""
    from poe_tablet_tool.health import get_detailed_health

    return get_detailed_health()


@app.get("/api/health/poe")
def poe_api_health() -> dict:
    """Check PoE trade API connectivity."""
    from poe_tablet_tool.health import check_poe_api_health

    return check_poe_api_health()


@app.get("/api/reports/price-spread")
def api_price_spread() -> dict:
    """Price spread analysis across normal/magic/rare modes."""
    league_id = _league_id()
    return {
        "spread_by_mode": report_builder.price_spread_analysis(league_id),
        "spread_summary": report_builder.price_spread_summary(league_id),
    }


@app.get("/api/reports/crafting-profitability")
def api_crafting_profitability() -> list[dict]:
    """Crafting profitability matrix (normal -> magic/rare)."""
    return report_builder.crafting_profitability(_league_id())


@app.get("/api/reports/time-patterns")
def api_time_patterns() -> list[dict]:
    """Time-based price patterns (hour of day, day of week)."""
    return report_builder.time_based_patterns(_league_id())


@app.get("/api/export/prices-csv")
def export_prices_csv() -> str:
    """Export current prices as CSV."""
    import csv
    from io import StringIO

    league_id = _league_id()
    from poe_tablet_tool.db.connection import get_connection

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT
            l.tablet_type,
            l.query_mode,
            l.price_divine,
            l.price_currency,
            l.affix_count,
            l.uses_remaining,
            l.seller_name,
            s.taken_at
        FROM listings l
        JOIN snapshots s ON l.snapshot_id = s.id
        WHERE l.league_id = ?
        ORDER BY l.tablet_type, l.query_mode, l.price_divine DESC
        """,
        (league_id,),
    ).fetchall()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "tablet_type",
            "query_mode",
            "price_divine",
            "price_currency",
            "affix_count",
            "uses_remaining",
            "seller_name",
            "taken_at",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row["tablet_type"],
                row["query_mode"],
                row["price_divine"] or "",
                row["price_currency"] or "",
                row["affix_count"],
                row["uses_remaining"] or "",
                row["seller_name"] or "",
                row["taken_at"] or "",
            ]
        )

    return output.getvalue()


def main() -> None:
    import uvicorn

    uvicorn.run(
        "poe_tablet_tool.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )


if __name__ == "__main__":
    main()


@app.post("/api/snapshots/trigger")
def trigger_snapshot(
    tablet_type: str = "ritual",
    query_mode: str = "rare",
) -> dict:
    """
    Manually trigger a snapshot collection job.
    Useful for backfilling or testing.
    """
    from poe_tablet_tool.query_builder import MAGIC_MODE, NORMAL_MODE, RARE_MODE
    from poe_tablet_tool.scheduler import run_single_snapshot_job
    from poe_tablet_tool.tablets import TABLET_TYPES

    # Validate tablet_type
    if tablet_type not in TABLET_TYPES:
        return {
            "error": f"Invalid tablet_type: {tablet_type}. Valid: {list(TABLET_TYPES.keys())}",
            "status": "invalid",
        }

    # Validate query_mode
    valid_modes = {RARE_MODE, MAGIC_MODE, NORMAL_MODE}
    if query_mode not in valid_modes:
        return {
            "error": f"Invalid query_mode: {query_mode}. Valid: {valid_modes}",
            "status": "invalid",
        }

    result = run_single_snapshot_job(tablet_type, query_mode)
    return result


@app.get("/api/league/info")
def league_info() -> dict:
    """Get current league information."""
    from poe_tablet_tool.league_detector import detect_league
    from poe_tablet_tool.league_reset import get_all_leagues

    current_league = detect_league()
    all_leagues = get_all_leagues()

    return {
        "current_league": current_league,
        "all_leagues": [
            {
                "name": l["name"],
                "started_at": l["started_at"],
                "is_active": bool(l["is_active"]),
            }
            for l in all_leagues
        ],
    }


@app.get("/api/reports/mod-reference")
def api_mod_reference() -> list[dict]:
    """Get all tablet modifier suffixes - summary by tablet type."""
    return report_builder.mod_reference()


@app.get("/api/reports/mod-reference-separated")
def api_mod_reference_separated() -> list[dict]:
    """Get all tablet modifiers with prefixes and suffixes separated."""
    return report_builder.mod_reference_separated()


@app.get("/api/reports/mod-reference/{tablet_type}")
def api_mod_reference_detail(tablet_type: str) -> dict:
    """Get detailed modifiers (prefixes and suffixes) for a specific tablet type."""
    return report_builder.mod_reference_detail(tablet_type)


@app.get("/modifiers")
def modifiers_dashboard() -> FileResponse:
    path = STATIC_DIR / "modifiers.html"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="modifiers.html not found")
    return FileResponse(path)


@app.get("/tablet/{tablet_type}")
def tablet_detail(tablet_type: str) -> FileResponse:
    path = STATIC_DIR / "tablet_detail.html"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="tablet_detail.html not found")
    return FileResponse(path)
