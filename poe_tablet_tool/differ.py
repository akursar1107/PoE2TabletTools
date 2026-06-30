"""
Compares consecutive snapshots for the same tablet_type + query_mode
and classifies disappeared listings with improved accuracy.

Improvements over v1:
- Requires items to be visible in multiple snapshots before classifying as sold
- Better relist detection with price stability and seller checks
- New classification: "price_updated" for items that reappear with different prices
- Confidence scoring based on multiple factors
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from poe_tablet_tool.db.connection import get_connection
from poe_tablet_tool.snapshot_store import (
    get_item_ids_in_snapshot,
    get_previous_snapshot_id,
    mark_disappeared,
)

logger = logging.getLogger(__name__)

# Configuration constants
MIN_SNAPSHOTS_FOR_SOLD = 2  # Item must appear in at least 2 consecutive snapshots
RELIST_PRICE_TOLERANCE = 0.15  # 15% price difference still counts as relist
PRICE_UPDATE_THRESHOLD = 0.30  # 30%+ price change suggests price update, not relist
MAX_VISIBILITY_DURATION_HOURS = 24  # Items visible >24h are less likely to be sold


@dataclass
class ListingHistory:
    """Complete history of a listing across snapshots."""
    item_id: str
    first_seen: str
    last_seen: str
    seller_name: str
    prices: list[float]  # List of price_divine values in order
    snapshot_count: int
    was_price_stable: bool = False


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_listing_history(
    item_id: str, league_id: int, new_snapshot_id: int
) -> ListingHistory | None:
    """Fetch complete history of a listing across all snapshots."""
    conn = get_connection()
    
    rows = conn.execute(
        """
        SELECT 
            item_id, 
            seller_name, 
            price_divine, 
            first_seen_at, 
            last_seen_at,
            snapshot_id
        FROM listings 
        WHERE item_id = ? AND league_id = ?
        ORDER BY snapshot_id
        """,
        (item_id, league_id),
    ).fetchall()
    
    if not rows:
        return None
    
    prices = [r["price_divine"] for r in rows if r["price_divine"] is not None]
    
    # Check if price was stable (within tolerance) across all snapshots
    was_stable = True
    if len(prices) >= 2:
        for i in range(1, len(prices)):
            if prices[i-1] > 0 and prices[i] > 0:
                delta = abs(prices[i] - prices[i-1]) / max(prices[i-1], 0.001)
                if delta > RELIST_PRICE_TOLERANCE:
                    was_stable = False
                    break
    
    return ListingHistory(
        item_id=rows[0]["item_id"],
        first_seen=rows[0]["first_seen_at"],
        last_seen=rows[-1]["last_seen_at"],
        seller_name=rows[0]["seller_name"] if rows else "",
        prices=prices,
        snapshot_count=len(rows),
        was_price_stable=was_stable,
    )


def _get_new_listings_by_seller(new_snapshot_id: int) -> dict[str, list[dict]]:
    """Get all listings in new snapshot indexed by seller."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT item_id, seller_name, price_divine, price_currency
        FROM listings WHERE snapshot_id = ?
        """,
        (new_snapshot_id,),
    ).fetchall()
    
    index: dict[str, list[dict]] = {}
    for row in rows:
        seller = row["seller_name"]
        if seller:
            index.setdefault(seller, []).append({
                "item_id": row["item_id"],
                "price_divine": row["price_divine"],
                "price_currency": row["price_currency"],
            })
    return index


def _calculate_visibility_duration(first: str, last: str) -> timedelta | None:
    """Calculate how long a listing was visible."""
    try:
        first_dt = datetime.fromisoformat(first.replace("Z", "+00:00"))
        last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
        return last_dt - first_dt
    except (ValueError, TypeError):
        return None


def _classify_disappearance(
    item_id: str,
    league_id: int,
    tablet_type: str,
    query_mode: str,
    old_snapshot_id: int,
    new_snapshot_id: int,
    new_by_seller: dict[str, list[dict]],
) -> tuple[str, float, str]:
    """
    Classify a disappeared listing with improved accuracy.
    
    Returns: (classification, confidence, reason)
    """
    # Get complete history of this item
    history = _get_listing_history(item_id, league_id, new_snapshot_id)
    
    if history is None:
        return "uncertain", 0.1, "no history available"
    
    seller = history.seller_name
    
    # Check 1: Is this a relist? (seller has new listing)
    if seller and seller in new_by_seller:
        for new_listing in new_by_seller[seller]:
            if new_listing["item_id"] == item_id:
                # Same item relisted - this shouldn't happen, but handle it
                continue
            
            new_price = new_listing.get("price_divine")
            old_prices = history.prices
            
            if old_prices and new_price is not None:
                # Check all old prices against new price
                for old_price in old_prices:
                    if old_price and old_price > 0 and new_price > 0:
                        delta = abs(new_price - old_price) / old_price
                        if delta <= RELIST_PRICE_TOLERANCE:
                            return "relisted", 0.85, f"seller {seller} relisted at similar price (delta: {delta:.0%})"
                        elif delta <= PRICE_UPDATE_THRESHOLD:
                            # Could be price update or relist with different price
                            if history.snapshot_count >= MIN_SNAPSHOTS_FOR_SOLD:
                                return "price_updated", 0.70, f"seller {seller} has new listing at different price (delta: {delta:.0%})"
    
    # Check 2: Was the item visible long enough?
    visibility = _calculate_visibility_duration(history.first_seen, history.last_seen)
    if visibility and visibility.total_seconds() > MAX_VISIBILITY_DURATION_HOURS * 3600:
        # Items visible >24h are less likely to be sold
        confidence = max(0.3, 0.7 - (visibility.total_seconds() / (24 * 3600) * 0.4))
        return "uncertain", confidence, f"item was visible for {visibility} (too long for confident sale)"
    
    # Check 3: Did it appear in enough snapshots?
    if history.snapshot_count < MIN_SNAPSHOTS_FOR_SOLD:
        return "uncertain", 0.4, f"only appeared in {history.snapshot_count} snapshot(s)"
    
    # Check 4: Was the price stable? (more confidence if stable)
    stability_bonus = 0.15 if history.was_price_stable and history.prices else 0
    
    # Check 5: Does seller still have other listings? (reduces sale confidence)
    if seller and seller in new_by_seller and len(new_by_seller[seller]) > 0:
        # Seller still active, slightly less confident
        confidence = 0.65 + stability_bonus
        return "likely_sold", confidence, f"seller active, stable price: {history.was_price_stable}"
    
    # Default: likely sold with high confidence
    confidence = 0.75 + stability_bonus
    return "likely_sold", min(confidence, 0.95), "disappeared with stable history"


def _classify_with_fallback(
    item_id: str,
    league_id: int,
    tablet_type: str,
    query_mode: str,
    old_snapshot_id: int,
    new_snapshot_id: int,
    new_by_seller: dict[str, list[dict]],
    old_details: dict[str, dict],
) -> tuple[str, float, str]:
    """Try enhanced classification, fall back to simple classification."""
    try:
        return _classify_disappearance(
            item_id, league_id, tablet_type, query_mode,
            old_snapshot_id, new_snapshot_id, new_by_seller
        )
    except Exception as e:
        logger.debug(f"Enhanced classification failed for {item_id}: {e}")
        # Fall back to simple classification
        old_listing = old_details.get(item_id, {})
        
        # Simple relist check
        if old_listing.get("seller_name") in new_by_seller:
            return "relisted", 0.7, "seller has new listing"
        
        if old_listing.get("price_divine") is not None:
            return "likely_sold", 0.55, "disappeared with price data"
        
        return "uncertain", 0.3, "disappeared without clear signal"


def record_disappearance(
    item_id: str,
    classified_as: str,
    confidence: float,
    reason: str,
    old_snapshot_id: int,
    new_snapshot_id: int,
    tablet_type: str,
    query_mode: str,
) -> None:
    conn = get_connection()
    now = _now()
    conn.execute(
        """
        INSERT INTO listing_disappearances
            (item_id, tablet_type, query_mode, old_snapshot_id, new_snapshot_id,
             classified_as, confidence, reason, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            item_id,
            tablet_type,
            query_mode,
            old_snapshot_id,
            new_snapshot_id,
            classified_as,
            round(confidence, 2),
            reason,
            now,
        ),
    )
    conn.commit()


def diff_snapshots(
    league_id: int,
    tablet_type: str,
    query_mode: str,
    new_snapshot_id: int,
) -> int:
    """
    Compare new snapshot with previous snapshots and classify disappearances.
    Returns total count of disappeared items.
    """
    old_snapshot_id = get_previous_snapshot_id(
        league_id, tablet_type, query_mode, new_snapshot_id
    )
    if old_snapshot_id is None:
        logger.debug(
            "No previous snapshot for %s/%s — skipping diff", tablet_type, query_mode
        )
        return 0

    old_ids = get_item_ids_in_snapshot(old_snapshot_id)
    new_ids = get_item_ids_in_snapshot(new_snapshot_id)
    disappeared_ids = old_ids - new_ids

    if not disappeared_ids:
        logger.debug("No disappearances for %s/%s", tablet_type, query_mode)
        return 0

    # Get old listing details for fallback classification
    old_details = {}
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT item_id, seller_name, price_divine
        FROM listings WHERE snapshot_id = ?
        """,
        (old_snapshot_id,),
    ).fetchall()
    for row in rows:
        old_details[row["item_id"]] = {
            "seller_name": row["seller_name"],
            "price_divine": row["price_divine"],
        }
    
    # Get new listings by seller for relist detection
    new_by_seller = _get_new_listings_by_seller(new_snapshot_id)
    
    now = _now()
    sold_count = 0
    relist_count = 0
    uncertain_count = 0
    price_updated_count = 0

    for item_id in disappeared_ids:
        classified_as, confidence, reason = _classify_with_fallback(
            item_id, league_id, tablet_type, query_mode,
            old_snapshot_id, new_snapshot_id, new_by_seller, old_details
        )
        
        mark_disappeared(item_id, old_snapshot_id, now, classified_as)
        record_disappearance(
            item_id=item_id,
            classified_as=classified_as,
            confidence=confidence,
            reason=reason,
            old_snapshot_id=old_snapshot_id,
            new_snapshot_id=new_snapshot_id,
            tablet_type=tablet_type,
            query_mode=query_mode,
        )
        
        if classified_as == "likely_sold":
            sold_count += 1
        elif classified_as == "relisted":
            relist_count += 1
        elif classified_as == "uncertain":
            uncertain_count += 1
        elif classified_as == "price_updated":
            price_updated_count += 1

    logger.info(
        "Diffed %s/%s: %d disappeared (%d likely_sold, %d relisted, %d price_updated, %d uncertain) (old=%d, new=%d)",
        tablet_type,
        query_mode,
        len(disappeared_ids),
        sold_count,
        relist_count,
        price_updated_count,
        uncertain_count,
        old_snapshot_id,
        new_snapshot_id,
    )
    return len(disappeared_ids)
