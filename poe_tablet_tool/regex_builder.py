"""
Generates PoE2 stash-search regex strings from analyzer output.
"""

import logging
import re
from datetime import datetime, timezone

from poe_tablet_tool.db.connection import get_connection

logger = logging.getLogger(__name__)

MAX_REGEX_CHARS = 120
MAX_TERMS = 8


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _distinct_substring(mod_text: str) -> str:
    cleaned = re.sub(r"\[[^\]]+\]", "", mod_text)
    cleaned = re.sub(r"\d+", "", cleaned).strip()
    words = [w for w in cleaned.split() if len(w) >= 4]
    return words[0] if words else cleaned[:20]


def _join_terms(terms: list[str]) -> str:
    unique: list[str] = []
    seen: set[str] = set()
    for term in terms:
        t = term.strip()
        if not t or t.lower() in seen:
            continue
        seen.add(t.lower())
        unique.append(t)
    regex = "|".join(unique)
    if len(regex) <= MAX_REGEX_CHARS:
        return regex
    return "|".join(unique[:MAX_TERMS])


def run_regex_builder(league_id: int) -> int:
    conn = get_connection()
    now = _now()
    conn.execute("DELETE FROM regex_outputs WHERE league_id = ?", (league_id,))
    written = 0

    rare_by_type = conn.execute(
        """
        SELECT tablet_type, mod_text, lift
        FROM rare_affix_stats
        WHERE league_id = ? AND lift > 1.0
        ORDER BY tablet_type, lift DESC
        """,
        (league_id,),
    ).fetchall()

    by_tablet: dict[str | None, list[str]] = {}
    for row in rare_by_type:
        by_tablet.setdefault(row["tablet_type"], []).append(_distinct_substring(row["mod_text"]))

    global_rare_terms: list[str] = []
    for row in sorted(rare_by_type, key=lambda r: r["lift"], reverse=True)[:MAX_TERMS]:
        global_rare_terms.append(_distinct_substring(row["mod_text"]))

    outputs: list[tuple[str | None, str, str, str]] = [
        (None, "sell_rare", "Top rare sell affixes (all tablets)", _join_terms(global_rare_terms)),
    ]
    for tablet_type, terms in by_tablet.items():
        outputs.append(
            (tablet_type, "sell_rare", f"Sell rare — {tablet_type}", _join_terms(terms[:MAX_TERMS]))
        )

    magic_rows = conn.execute(
        """
        SELECT ce.tablet_type, msp.mod_a_text, msp.mod_b_text, ce.expected_profit_div
        FROM crafting_edge ce
        JOIN magic_seed_pairs msp
          ON msp.league_id = ce.league_id
         AND msp.tablet_type = ce.tablet_type
         AND msp.mod_pair_key = ce.mod_pair_key
        WHERE ce.league_id = ? AND ce.is_buy_signal = 1
        ORDER BY ce.expected_profit_div DESC
        LIMIT 20
        """,
        (league_id,),
    ).fetchall()

    buy_terms = []
    keep_terms = []
    for row in magic_rows:
        buy_terms.append(_distinct_substring(row["mod_a_text"]))
        buy_terms.append(_distinct_substring(row["mod_b_text"]))
        keep_terms.append(_distinct_substring(row["mod_a_text"]))

    if buy_terms:
        outputs.append((None, "buy_magic", "Buy magic project bases", _join_terms(buy_terms)))
    if keep_terms:
        outputs.append((None, "keep_magic", "Keep magic craft bases", _join_terms(keep_terms)))

    for tablet_type, regex_mode, label, regex_text in outputs:
        if not regex_text:
            continue
        conn.execute(
            """
            INSERT INTO regex_outputs (
                league_id, tablet_type, regex_mode, label, regex_text,
                char_count, source_summary, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                league_id,
                tablet_type,
                regex_mode,
                label,
                regex_text,
                len(regex_text),
                f"Generated from league_id={league_id}",
                now,
            ),
        )
        written += 1

    conn.commit()
    logger.info("regex_builder wrote %d regex outputs", written)
    return written
