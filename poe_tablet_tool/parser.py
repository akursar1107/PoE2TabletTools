"""
Parses raw fetch result dicts from the PoE2 trade API into structured models.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from poe_tablet_tool.query_builder import MAGIC_MODE, NORMAL_MODE, RARE_MODE
from poe_tablet_tool.rate_provider import to_divine

logger = logging.getLogger(__name__)

# Map trade API currency strings to a canonical form
CURRENCY_ALIASES: dict[str, str] = {
    "divine": "divine",
    "exalted": "exalted",
    "chaos": "chaos",
    "gold": "gold",
}


@dataclass
class ParsedAffix:
    mod_id: str
    mod_text: str
    mod_family: str = ""
    slot: str = "unknown"  # 'prefix', 'suffix', or 'unknown'
    value_min: float | None = None
    value_max: float | None = None
    mod_index: int = 0


_NUM_RE = re.compile(r"\d+")


def _mod_family(text: str) -> str:
    """Strip numeric values from mod text to produce a groupable family string."""
    return _NUM_RE.sub("#", text).strip()


@dataclass
class ParsedListing:
    item_id: str
    seller_name: str
    price_amount: float | None
    price_currency: str | None
    price_divine: float | None  # normalized; None until exchange rate applied
    affix_count: int
    uses_remaining: int | None
    rarity: str  # 'Magic', 'Rare', 'Normal'
    affixes: list[ParsedAffix] = field(default_factory=list)
    raw_json: str = ""


def _parse_price(listing: dict) -> tuple[float | None, str | None]:
    price = listing.get("price")
    if not price:
        return None, None
    amount = price.get("amount")
    currency = CURRENCY_ALIASES.get(price.get("currency", "").lower())
    return amount, currency


def _parse_mod_list(
    mod_list: list, slot_override: str | None = None
) -> list[ParsedAffix]:
    """
    Parse a list of mod objects as returned by the PoE2 trade fetch API.
    Each mod obj: {description, hash, mods: [{name, tier, magnitudes: [{min, max}]}]}
    Falls back to plain string handling for backwards compat.
    """
    affixes: list[ParsedAffix] = []

    for i, mod_obj in enumerate(mod_list):
        if isinstance(mod_obj, str):
            affixes.append(
                ParsedAffix(
                    mod_id="",
                    mod_text=mod_obj,
                    mod_family=_mod_family(mod_obj),
                    slot=slot_override or "unknown",
                    mod_index=i,
                )
            )
            continue

        # Canonical mod ID: strip leading "stat." prefix if present
        raw_hash = mod_obj.get("hash", "")
        mod_id = raw_hash.removeprefix("stat.")

        mod_text = mod_obj.get("description", "")
        mods_list = mod_obj.get("mods", [])

        slot = slot_override or "unknown"
        val_min: float | None = None
        val_max: float | None = None

        if mods_list:
            tier = mods_list[0].get("tier", "")
            if slot_override is None:
                if tier.startswith("P"):
                    slot = "prefix"
                elif tier.startswith("S"):
                    slot = "suffix"

            magnitudes = mods_list[0].get("magnitudes", [])
            if magnitudes:
                try:
                    val_min = float(magnitudes[0].get("min", 0))
                    val_max = float(magnitudes[0].get("max", 0))
                except (TypeError, ValueError):
                    pass

        affixes.append(
            ParsedAffix(
                mod_id=mod_id,
                mod_text=mod_text,
                mod_family=_mod_family(mod_text),
                slot=slot,
                value_min=val_min,
                value_max=val_max,
                mod_index=i,
            )
        )

    return affixes


def _parse_mods(item: dict) -> list[ParsedAffix]:
    affixes: list[ParsedAffix] = []
    idx_offset = 0

    explicit = _parse_mod_list(item.get("explicitMods", []))
    for a in explicit:
        a.mod_index += idx_offset
    affixes.extend(explicit)
    idx_offset += len(explicit)

    implicit = _parse_mod_list(item.get("implicitMods", []), slot_override="implicit")
    for a in implicit:
        a.mod_index += idx_offset
    affixes.extend(implicit)

    return affixes


def _count_affixes(item: dict, affixes: list[ParsedAffix]) -> int:
    return len([a for a in affixes if a.slot not in ("implicit", "crafted")])


def _parse_uses_remaining(item: dict) -> int | None:
    for mod_obj in item.get("implicitMods", []):
        text = mod_obj.get("description", "") if isinstance(mod_obj, dict) else mod_obj
        lower = text.lower()
        if "use" in lower and "remaining" in lower:
            for part in text.split():
                try:
                    return int(part)
                except ValueError:
                    continue
    return None


def parse_fetch_result(raw: dict[str, Any]) -> ParsedListing | None:
    """Parse one item from the trade API fetch response. Returns None on failure."""
    try:
        item = raw.get("item", {})
        listing = raw.get("listing", {})
        account = listing.get("account", {})

        item_id: str = raw.get("id", "")
        if not item_id:
            return None

        seller_name: str = account.get("name", "")
        rarity: str = item.get("rarity", "Normal")
        price_amount, price_currency = _parse_price(listing)
        affixes = _parse_mods(item)
        affix_count = _count_affixes(item, affixes)
        uses_remaining = _parse_uses_remaining(item)

        return ParsedListing(
            item_id=item_id,
            seller_name=seller_name,
            price_amount=price_amount,
            price_currency=price_currency,
            price_divine=to_divine(price_amount, price_currency),
            affix_count=affix_count,
            uses_remaining=uses_remaining,
            rarity=rarity,
            affixes=affixes,
            raw_json=json.dumps(raw),
        )
    except Exception:
        logger.exception("Failed to parse listing: %s", raw.get("id"))
        return None


def parse_all(raw_results: list[dict[str, Any]]) -> list[ParsedListing]:
    parsed = [parse_fetch_result(r) for r in raw_results]
    return [p for p in parsed if p is not None]


def filter_for_query_mode(
    listings: list[ParsedListing], query_mode: str
) -> list[ParsedListing]:
    """Keep only listings matching the intended affix count for each track."""
    if query_mode == RARE_MODE:
        return [listing for listing in listings if listing.affix_count in (4, 5)]
    if query_mode == MAGIC_MODE:
        return [listing for listing in listings if listing.affix_count == 2]
    if query_mode == NORMAL_MODE:
        return [listing for listing in listings if listing.affix_count == 0]
    raise ValueError(f"Unknown query_mode: {query_mode}")
