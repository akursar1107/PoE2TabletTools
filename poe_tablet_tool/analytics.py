"""
Runs all analytics jobs for the active league.
"""

import logging

from poe_tablet_tool.buy_signal_engine import run_buy_signal_engine
from poe_tablet_tool.magic_analyzer import run_magic_analyzer
from poe_tablet_tool.rare_analyzer import run_rare_analyzer
from poe_tablet_tool.regex_builder import run_regex_builder
from poe_tablet_tool.snapshot_store import analysis_floor_snapshot_id

logger = logging.getLogger(__name__)


def run_all_analytics(league_id: int) -> dict[str, int]:
    floor = analysis_floor_snapshot_id(league_id)
    results = {
        "rare_affix_stats": run_rare_analyzer(league_id, floor),
        "magic_seed_pairs": run_magic_analyzer(league_id, floor),
        "crafting_edge": run_buy_signal_engine(league_id, floor),
        "regex_outputs": run_regex_builder(league_id),
    }
    logger.info("Analytics complete: %s", results)
    return results
