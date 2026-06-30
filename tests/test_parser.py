"""Tests for listing parser."""

from poe_tablet_tool.parser import (
    filter_for_query_mode,
    parse_fetch_result,
)
from poe_tablet_tool.query_builder import MAGIC_MODE, RARE_MODE
from poe_tablet_tool.rate_provider import to_divine


SAMPLE_LISTING = {
    "id": "abc123",
    "item": {
        "rarity": "Rare",
        "explicitMods": [
            {
                "description": "10% increased Quantity of Items Found in your Maps",
                "hash": "stat.quantity",
                "mods": [{"name": "Quantity", "tier": "1", "magnitudes": [{"min": 10, "max": 10}]}],
            },
            {
                "description": "5% increased Pack Size in your Maps",
                "hash": "stat.pack_size",
                "mods": [{"name": "Pack Size", "tier": "1", "magnitudes": [{"min": 5, "max": 5}]}],
            },
            {
                "description": "20% increased Magic Monsters",
                "hash": "stat.magic_monsters",
                "mods": [{"name": "Magic", "tier": "1", "magnitudes": [{"min": 20, "max": 20}]}],
            },
            {
                "description": "15% increased Rare Monsters",
                "hash": "stat.rare_monsters",
                "mods": [{"name": "Rare", "tier": "1", "magnitudes": [{"min": 15, "max": 15}]}],
            },
        ],
        "implicitMods": [
            {"description": "8 uses remaining", "hash": "stat.uses"},
        ],
    },
    "listing": {
        "price": {"amount": 400, "currency": "chaos"},
        "account": {"name": "TestSeller"},
    },
}


def test_parse_fetch_result_affix_count():
    parsed = parse_fetch_result(SAMPLE_LISTING)
    assert parsed is not None
    assert parsed.affix_count == 4
    assert parsed.seller_name == "TestSeller"


def test_to_divine_chaos():
    assert to_divine(200, "chaos") == 1.0


def test_filter_rare_mode():
    rare = parse_fetch_result(SAMPLE_LISTING)
    magic_listing = {
        **SAMPLE_LISTING,
        "item": {
            **SAMPLE_LISTING["item"],
            "rarity": "Magic",
            "explicitMods": SAMPLE_LISTING["item"]["explicitMods"][:2],
        },
    }
    magic = parse_fetch_result(magic_listing)
    filtered = filter_for_query_mode([rare, magic], RARE_MODE)
    assert len(filtered) == 1
    assert filtered[0].affix_count == 4


def test_filter_magic_mode():
    magic_listing = {
        **SAMPLE_LISTING,
        "item": {
            **SAMPLE_LISTING["item"],
            "rarity": "Magic",
            "explicitMods": SAMPLE_LISTING["item"]["explicitMods"][:2],
        },
    }
    parsed = parse_fetch_result(magic_listing)
    filtered = filter_for_query_mode([parsed], MAGIC_MODE)
    assert len(filtered) == 1
    assert filtered[0].affix_count == 2
