"""
Tablet type registry.
refName values come from Exiled-Exchange-2 items.ndjson — these are the exact
strings the PoE2 trade API expects in the `type` filter.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TabletType:
    key: str          # internal identifier
    ref_name: str     # trade API `type` value
    label: str        # human-readable label
    tag: str          # tower_augment_* tag from game data


TABLET_TYPES: dict[str, TabletType] = {
    t.key: t
    for t in [
        TabletType("ritual",     "Ritual Tablet",     "Ritual Tablet",     "tower_augment_ritual"),
        TabletType("breach",     "Breach Tablet",     "Breach Tablet",     "tower_augment_breach"),
        TabletType("expedition", "Expedition Tablet", "Expedition Tablet", "tower_augment_expedition"),
        TabletType("delirium",   "Delirium Tablet",   "Delirium Tablet",   "tower_augment_delirium"),
        TabletType("abyss",      "Abyss Tablet",      "Abyss Tablet",      "tower_augment_abyss"),
        TabletType("overseer",   "Overseer Tablet",   "Overseer Tablet",   "tower_augment_map_boss"),
        TabletType("irradiated", "Irradiated Tablet", "Irradiated Tablet", "tower_augment_generic"),
        TabletType("temple",     "Temple Tablet",     "Temple Tablet",     "tower_augment_temple"),
    ]
}
