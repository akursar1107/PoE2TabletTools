"""
Static data for tablet modifiers (prefixes and suffixes).
Source: https://www.poe2wiki.net/wiki/List_of_modifiers_for_tablets
"""

# Shared prefix groups across all tablet types
# Each prefix has: group, name (the actual modifier name) and description
SHARED_PREFIXES = [
    {
        "group": "MapAdditionalExile",
        "name": "Exiled",
        "description": "Map is inhabited by 1 additional Rogue Exile",
    },
    {
        "group": "MapMonsterEffectiveness",
        "name": "Challenger's",
        "description": "Monsters have (10-15)% increased Effectiveness",
    },
    {
        "group": "MapDroppedGoldIncrease",
        "name": "Bountiful",
        "description": "(25-35)% increased Gold found in Map",
    },
    {
        "group": "MapExperienceGainIncrease",
        "name": "Elevated",
        "description": "(12-18)% increased Experience gain in Map",
    },
    {
        "group": "MapAdditionalAzmeriWisp",
        "name": "Azmeri's",
        "description": "Map contains 1 additional Azmeri Spirit",
    },
    {
        "group": "MapRarePackIncrease",
        "name": "Brimming",
        "description": "Map has (25-35)% increased number of Rare Monsters",
    },
    {
        "group": "MapPackSizeIncrease",
        "name": "Breeding",
        "description": "(5-7)% increased Pack Size in Map",
    },
    {
        "group": "MapAdditionalEssence",
        "name": "Crystallised",
        "description": "Map contains an additional Essence",
    },
    {
        "group": "MapDroppedItemRarityIncrease",
        "name": "Collector's",
        "description": "(8-12)% increased Rarity of Items found in Map",
    },
    {
        "group": "MapMonsterRarityIncrease",
        "name": "Abounding",
        "description": "Map has (15-20)% increased Monster Rarity",
    },
    {
        "group": "MapMagicPackIncrease",
        "name": "Teeming",
        "description": "Map has (30-40)% increased Magic Monsters",
    },
    {
        "group": "MapAdditionalStoneCircle",
        "name": "Summoner's",
        "description": "Map contains an additional Summoning Circle",
    },
    {
        "group": "MapAdditionalChests",
        "name": "Treasurer's",
        "description": "Map contains (2-3) additional Rare Chests",
    },
]

# Shared suffix groups across all tablet types
# Each suffix group contains multiple modifiers with name and description
SHARED_SUFFIXES = {
    "MapAdditionalShrine": [
        {
            "name": "of Shrines",
            "description": "Map has (70-100)% increased chance to contain Shrines",
        },
        {"name": "of the Devoted", "description": "Map contains an additional Shrine"},
    ],
    "MapAdditionalStrongbox": [
        {
            "name": "of the Antiquarian",
            "description": "Map contains an additional Strongbox",
        },
        {
            "name": "of Strongboxes",
            "description": "Map has (70-100)% increased chance to contain Strongboxes",
        },
    ],
    "MapDroppedMapsIncrease": [
        {
            "name": "of the Cartographer",
            "description": "(30-40)% increased Quantity of Waystones found in Map",
        },
    ],
    "MapAdditionalExile": [
        {
            "name": "of the Exile",
            "description": "Map has (70-100)% increased chance to contain Rogue Exiles",
        },
    ],
    "MapAdditionalEssence": [
        {
            "name": "of the Essence",
            "description": "Map has (70-100)% increased chance to contain Essences",
        },
    ],
    "MapAdditionalUniqueMonsterModifier": [
        {
            "name": "of Contest",
            "description": "Unique Monsters have 1 additional Rare Modifier",
        },
    ],
    "MapAdditionalStoneCircle": [
        {
            "name": "of the Summoning",
            "description": "Map has (70-100)% increased chance to contain a Summoning Circle",
        },
    ],
    "MapAdditionalSpirit": [
        {
            "name": "of Spirits",
            "description": "Map has (70-100)% increased chance to contain Azmeri Spirits",
        },
    ],
    "MapAdditionalModifier": [
        {
            "name": "of Undertaking",
            "description": "Map has (1-2) additional random Modifiers",
        },
    ],
}

# Tablet-specific suffixes
TABLET_SUFFIXES = {
    "irradiated": {
        "unique": []  # Irradiated only has shared suffixes
    },
    "abyss": {
        "unique": [
            {
                "group": "AbyssRareMonsterIncrease",
                "mods": [
                    {
                        "name": "of Champions",
                        "description": "(1-2) additional Rare Monsters are spawned from Abysses in Map",
                    }
                ],
            },
            {
                "group": "AbyssIncreasedRewards",
                "mods": [
                    {
                        "name": "of Treasures",
                        "description": "Abyss Pits in Map are twice as likely to have Rewards",
                    }
                ],
            },
            {
                "group": "AbyssDepthsChance",
                "mods": [
                    {
                        "name": "of the Depths",
                        "description": "Abysses in Map have (10-20)% increased chance to lead to an Abyssal Depths",
                    }
                ],
            },
            {
                "group": "AbyssExtraModifiers",
                "mods": [
                    {
                        "name": "of Dark Power",
                        "description": "(20-30)% increased chance for Abyssal monsters in Map to have Abyssal Modifiers",
                    }
                ],
            },
            {
                "group": "AbyssExtraTickets",
                "mods": [
                    {
                        "name": "of Ossification",
                        "description": "(20-30)% increased chance for Desecrated Currency from Abysses in Map",
                    }
                ],
            },
            {
                "group": "AbyssAdditionalChance",
                "mods": [
                    {
                        "name": "of Hollows",
                        "description": "Map contains an additional Abyss",
                    }
                ],
            },
            {
                "group": "Abyss4AdditionalChance",
                "mods": [
                    {
                        "name": "of Schisms",
                        "description": "Map has (20-40)% chance to contain four additional Abysses",
                    }
                ],
            },
            {
                "group": "AbyssMonsterIncrease",
                "mods": [
                    {
                        "name": "of the Abyssal Horde",
                        "description": "Abysses in Map spawn (20-30)% increased Monsters",
                    }
                ],
            },
            {
                "group": "AbyssEnhancedMonstersPerChasm",
                "mods": [
                    {
                        "name": "of Escalation",
                        "description": "Abyssal Monsters have (8-12)% increased Effectiveness for each closed Pit, up to 100%",
                    }
                ],
            },
        ]
    },
    "breach": {
        "unique": [
            {
                "group": "BreachAdditionalRares",
                "mods": [
                    {
                        "name": "of the Invasion",
                        "description": "Unstable Breaches in Map spawn (1-3) additional Rare Monsters when Stabilised",
                    }
                ],
            },
            {
                "group": "BreachRareMonsterPotency",
                "mods": [
                    {
                        "name": "of the Hand",
                        "description": "(5-20)% increased Effectiveness of Rare Breach Monsters in Map",
                    }
                ],
            },
            {
                "group": "BreachWombgiftLevelChance",
                "mods": [
                    {
                        "name": "of the Flesh",
                        "description": "Wombgifts have (10-30)% chance to drop one Level higher in Map",
                    }
                ],
            },
            {
                "group": "BreachMonsterQuantity",
                "mods": [
                    {
                        "name": "of the Horde",
                        "description": "Breaches in Map have (5-15)% increased Pack Size",
                    }
                ],
            },
            {
                "group": "BreachBossChance",
                "mods": [
                    {
                        "name": "of the Commander",
                        "description": "Unstable Breaches in Map have (20-50)% increased chance to contain Vruun, Marshal of Xesht",
                    }
                ],
            },
            {
                "group": "BreachHivebloodQuantity",
                "mods": [
                    {
                        "name": "of the Flow",
                        "description": "(30-60)% increased Quantity of Hiveblood found in Map",
                    }
                ],
            },
            {
                "group": "BreachWombgiftQuantity",
                "mods": [
                    {
                        "name": "of the Form",
                        "description": "(30-60)% increased Quantity of Wombgifts found in Map",
                    }
                ],
            },
        ]
    },
    "delirium": {
        "unique": [
            {
                "group": "DeliriumFogDissipationDelay",
                "mods": [
                    {
                        "name": "of Eternity",
                        "description": "Delirium Fog in Map lasts (6-12) additional seconds before dissipating",
                    }
                ],
            },
            {
                "group": "DeliriumDoodadsIncrease",
                "mods": [
                    {
                        "name": "of Mirrors",
                        "description": "Delirium Fog in Map spawns (15-30)% increased Fracturing Mirrors",
                    }
                ],
            },
            {
                "group": "DeliriumPackSizeIncrease",
                "mods": [
                    {
                        "name": "of Persecution",
                        "description": "Delirium Monsters in Map have (15-30)% increased Pack Size",
                    }
                ],
            },
            {
                "group": "DeliriumAdditionalShardsChance",
                "mods": [
                    {
                        "name": "of Shattering",
                        "description": "Delirium Fog in Map spawns (12-26)% increased MirrorShards",
                    }
                ],
            },
            {
                "group": "DeliriumBossChance",
                "mods": [
                    {
                        "name": "of Phobia",
                        "description": "Delirium Encounters in Map are (15-30)% more likely to spawn Unique Bosses",
                    }
                ],
            },
            {
                "group": "DeliriumFogPersistence",
                "mods": [
                    {
                        "name": "of the Unending",
                        "description": "Delirium Fog in Map dissipates (30-20)% slower",
                    }
                ],
            },
            {
                "group": "DeliriumDifficultyIncrease",
                "mods": [
                    {
                        "name": "of Madness",
                        "description": "Delirium in Map increases (15-30)% faster with distance from the mirror",
                    }
                ],
            },
            {
                "group": "DeliriumRareMonsterPause",
                "mods": [
                    {
                        "name": "of Freeze Time",
                        "description": "Slaying Rare Monsters in Map pauses the Delirium Mirror Timer for (3-5) seconds",
                    }
                ],
            },
            {
                "group": "DeliriumMonsterSplinterIncrease",
                "mods": [
                    {
                        "name": "of the Simulacrum",
                        "description": "(15-30)% increased Stack size of Simulacrum Splinters found in Map",
                    }
                ],
            },
        ]
    },
    "expedition": {
        "unique": [
            {
                "group": "ExpeditionArtifactIncrease",
                "mods": [
                    {
                        "name": "of Verisium",
                        "description": "(15-30)% increased quantity of Expedition Artifacts dropped by Monsters in Map",
                    }
                ],
            },
            {
                "group": "ExpeditionRunicMonsters",
                "mods": [
                    {
                        "name": "of Runes",
                        "description": "Map contains (15-30)% increased number of Runic Monster Markers",
                    }
                ],
            },
            {
                "group": "ExpeditionExplosionPlacement",
                "mods": [
                    {
                        "name": "of the Detonator",
                        "description": "(15-30)% increased Expedition Explosive Placement Range in Map",
                    }
                ],
            },
            {
                "group": "ExpeditionLogbookIncrease",
                "mods": [
                    {
                        "name": "of Knowledge",
                        "description": "(15-30)% increased Quantity of Expedition Logbooks dropped by Runic Monsters in Map",
                    }
                ],
            },
            {
                "group": "ExpeditionRelicModEffect",
                "mods": [
                    {
                        "name": "of Relics",
                        "description": "(12-18)% increased Effect of Expedition Remnants in Map",
                    }
                ],
            },
            {
                "group": "ExpeditionExplosionRadius",
                "mods": [
                    {
                        "name": "of the Demolition",
                        "description": "(15-30)% increased Expedition Explosive Radius in Map",
                    }
                ],
            },
            {
                "group": "ExpeditionRelicIncrease",
                "mods": [
                    {
                        "name": "of the Writings",
                        "description": "Expeditions in Map have +(1-2) Remnants",
                    }
                ],
            },
            {
                "group": "ExpeditionRareMonsters",
                "mods": [
                    {
                        "name": "of Ancient Fiends",
                        "description": "(25-40)% increased number of Rare Expedition Monsters in Map",
                    }
                ],
            },
        ]
    },
    "overseer": {
        "unique": [
            {
                "group": "MapBossAdditionalSpirit",
                "mods": [
                    {
                        "name": "of Wisps",
                        "description": "Map contains (1-2) additional Azmeri Spirits",
                    }
                ],
            },
            {
                "group": "MapBossRarity",
                "mods": [
                    {
                        "name": "of Treasure",
                        "description": "(35-60)% increased Rarity of Items dropped by Map Bosses",
                    }
                ],
            },
            {
                "group": "MapBossWaystoneChance",
                "mods": [
                    {
                        "name": "of Pathways",
                        "description": "(18-30)% increased Quantity of Waystones dropped by Map Bosses",
                    }
                ],
            },
            {
                "group": "MapBossQuantity",
                "mods": [
                    {
                        "name": "of Hoards",
                        "description": "(13-20)% increased Quantity of Items dropped by Map Bosses",
                    }
                ],
            },
            {
                "group": "MapBossAdditionalShrine",
                "mods": [
                    {
                        "name": "of Worship",
                        "description": "Map contains (1-2) additional Shrines",
                    }
                ],
            },
            {
                "group": "MapBossAdditionalEssence",
                "mods": [
                    {
                        "name": "of Crystals",
                        "description": "Map contains (1-2) additional Essences",
                    }
                ],
            },
            {
                "group": "MapBossExperience",
                "mods": [
                    {
                        "name": "of Conquering",
                        "description": "Map Bosses grant (40-80)% increased Experience",
                    }
                ],
            },
            {
                "group": "MapBossAdditionalStrongbox",
                "mods": [
                    {
                        "name": "of Compartments",
                        "description": "Map contains (1-2) additional Strongboxes",
                    }
                ],
            },
        ]
    },
    "ritual": {
        "unique": [
            {
                "group": "RitualChanceForNoCost",
                "mods": [
                    {
                        "name": "of the Occult",
                        "description": "Favours Rerolled at Ritual Altars in Map have (3-6)% chance to cost no Tribute",
                    }
                ],
            },
            {
                "group": "RitualDeferSpeed",
                "mods": [
                    {
                        "name": "of the Appeal",
                        "description": "Favours Deferred at Ritual Altars in Map reappear (25-40)% sooner",
                    }
                ],
            },
            {
                "group": "RitualDeferCostIncrease",
                "mods": [
                    {
                        "name": "of Devotion",
                        "description": "Deferring Favours at Ritual Altars in Map costs (30-20)% reduced Tribute",
                    }
                ],
            },
            {
                "group": "RitualOmenChance",
                "mods": [
                    {
                        "name": "of Omens",
                        "description": "Ritual Favours in Map have (35-70)% increased chance to be Omens",
                    }
                ],
            },
            {
                "group": "RitualTributeIncrease",
                "mods": [
                    {
                        "name": "of Sacrifice",
                        "description": "Monsters Sacrificed at Ritual Altars in Map grant (18-30)% increased Tribute",
                    }
                ],
            },
            {
                "group": "RitualRerollCostIncrease",
                "mods": [
                    {
                        "name": "of the Dogma",
                        "description": "Rerolling Favours at Ritual Altars in Map costs (30-20)% reduced Tribute",
                    }
                ],
            },
            {
                "group": "RitualMagicMonsters",
                "mods": [
                    {
                        "name": "of the Cult",
                        "description": "Revived Monsters from Ritual Altars in Map have (25-40)% increased chance to be Rare",
                    }
                ],
            },
            {
                "group": "RitualRareMonsters",
                "mods": [
                    {
                        "name": "of the Foundling",
                        "description": "Revived Monsters from Ritual Altars in Map have (35-70)% increased chance to be Magic",
                    }
                ],
            },
            {
                "group": "RitualAdditionalReroll",
                "mods": [
                    {
                        "name": "of Prayers",
                        "description": "Ritual Altars in Map allow rerolling Favours (1-3) additional times",
                    }
                ],
            },
        ]
    },
    "temple": {
        "unique": [
            {
                "group": "IncursionSecondaryEncounters",
                "mods": [
                    {
                        "name": "of Encounters",
                        "description": "(25-50)% increased chance Vaal Beacons summon additional Monsters in Map",
                    }
                ],
            },
            {
                "group": "IncursionPackSize",
                "mods": [
                    {
                        "name": "of Packs",
                        "description": "(10-30)% increased Pack Size for Monsters around Vaal Beacons in Map",
                    }
                ],
            },
            {
                "group": "IncursionRareChestChance",
                "mods": [
                    {
                        "name": "of Riches",
                        "description": "(30-60)% increased chance Vaal Beacon Chests are Rare in Map",
                    }
                ],
            },
            {
                "group": "IncursionExtraPacks",
                "mods": [
                    {
                        "name": "of Multitude",
                        "description": "1 extra pack of Monsters around Vaal Beacons in Map",
                    }
                ],
            },
            {
                "group": "IncursionExtraPacksChance",
                "mods": [
                    {
                        "name": "of Additional Packs",
                        "description": "(30-60)% chance for an extra packs of Monsters around Vaal Beacons in Map",
                    }
                ],
            },
            {
                "group": "IncursionTokenChance",
                "mods": [
                    {
                        "name": "of Vaal Crystals",
                        "description": "(5-10)% chance to gain an additional Crystal from Vaal Beacons in Map",
                    }
                ],
            },
            {
                "group": "IncursionBossChance",
                "mods": [
                    {
                        "name": "of the Vaal",
                        "description": "(10-25)% chance to add a Vaal Beacon Unique Monster to the Map",
                    }
                ],
            },
        ]
    },
}


# Modifier group categories for better organization
MOD_CATEGORIES = {
    # Shared/generic categories
    "Map": "General",
    "Additional": "General",
    # Abyss
    "Abyss": "Abyss",
    # Breach
    "Breach": "Breach",
    # Delirium
    "Delirium": "Delirium",
    # Expedition
    "Expedition": "Expedition",
    # Overseer/Map Boss
    "MapBoss": "Boss",
    # Ritual
    "Ritual": "Ritual",
    # Temple/Incursion
    "Incursion": "Temple",
    # Essences
    "Essence": "Essence",
    # Spirits
    "Spirit": "Spirit",
    "Azmeri": "Spirit",
    # Strongboxes
    "Strongbox": "Containers",
    # Shrines
    "Shrine": "Shrines",
    # Chests
    "Chest": "Containers",
    # Maps/Waystones
    "Maps": "Maps",
    "Waystone": "Maps",
    # Exiles
    "Exile": "Monsters",
    # Monsters
    "Monster": "Monsters",
    "Pack": "Monsters",
    # Items
    "Item": "Items",
    "Dropped": "Items",
    # Experience
    "Experience": "Progression",
    "Gain": "Progression",
    # Gold/Currency
    "Gold": "Currency",
    "Currency": "Currency",
}


def get_category_for_group(group_name: str) -> str:
    """Determine the category for a modifier group based on its name."""
    for prefix, category in MOD_CATEGORIES.items():
        if prefix in group_name:
            return category
    return "General"


def get_all_modifiers():
    """Get all modifiers organized by tablet type with full descriptions."""
    tablets = [
        "irradiated",
        "abyss",
        "breach",
        "delirium",
        "expedition",
        "overseer",
        "ritual",
        "temple",
    ]

    result = {}
    for tablet in tablets:
        result[tablet] = {"prefixes": SHARED_PREFIXES, "suffixes": {}}

        # Add shared suffixes
        for group, mods in SHARED_SUFFIXES.items():
            result[tablet]["suffixes"][group] = mods

        # Add tablet-specific suffixes
        if tablet in TABLET_SUFFIXES:
            for entry in TABLET_SUFFIXES[tablet]["unique"]:
                result[tablet]["suffixes"][entry["group"]] = entry["mods"]

    return result


def get_modifiers_by_tablet(tablet_type):
    """Get modifiers for a specific tablet type with full descriptions."""
    all_mods = get_all_modifiers()
    return all_mods.get(tablet_type, {})


def get_suffixes_summary():
    """Get a summary of prefix and suffix groups per tablet type (for display)."""
    tablets = [
        "irradiated",
        "abyss",
        "breach",
        "delirium",
        "expedition",
        "overseer",
        "ritual",
        "temple",
    ]

    result = []
    for tablet in tablets:
        mods = {}

        # Add shared prefixes
        for prefix in SHARED_PREFIXES:
            group = prefix["group"]
            if group not in mods:
                mods[group] = []
            mods[group].append(
                {"name": prefix["name"], "description": prefix["description"]}
            )

        # Add shared suffixes
        for group, suffix_mods in SHARED_SUFFIXES.items():
            if group not in mods:
                mods[group] = []
            mods[group].extend(
                {"name": m["name"], "description": m["description"]}
                for m in suffix_mods
            )

        # Add tablet-specific suffixes
        if tablet in TABLET_SUFFIXES:
            for entry in TABLET_SUFFIXES[tablet]["unique"]:
                group = entry["group"]
                if group not in mods:
                    mods[group] = []
                mods[group].extend(
                    {"name": m["name"], "description": m["description"]}
                    for m in entry["mods"]
                )

        # Count total individual modifiers
        total_mod_count = sum(len(m) for m in mods.values())
        result.append(
            {
                "tablet_type": tablet,
                "mod_count": total_mod_count,
                "suffix_groups": mods,
            }
        )

    return result


def get_modifiers_separated():
    """Get modifiers with prefixes and suffixes separated for display."""
    tablets = [
        "irradiated",
        "abyss",
        "breach",
        "delirium",
        "expedition",
        "overseer",
        "ritual",
        "temple",
    ]

    # Build a set of all prefix group names for identification
    prefix_groups = {p["group"] for p in SHARED_PREFIXES}

    result = []
    for tablet in tablets:
        prefixes = {}
        suffixes = {}

        # Add shared prefixes
        for prefix in SHARED_PREFIXES:
            group = prefix["group"]
            if group not in prefixes:
                prefixes[group] = []
            prefixes[group].append(
                {"name": prefix["name"], "description": prefix["description"]}
            )

        # Add shared suffixes (skip any that are prefix groups)
        for group, suffix_mods in SHARED_SUFFIXES.items():
            if group not in suffixes:
                suffixes[group] = []
            suffixes[group].extend(
                {"name": m["name"], "description": m["description"]}
                for m in suffix_mods
            )

        # Add tablet-specific suffixes
        if tablet in TABLET_SUFFIXES:
            for entry in TABLET_SUFFIXES[tablet]["unique"]:
                group = entry["group"]
                if group not in suffixes:
                    suffixes[group] = []
                suffixes[group].extend(
                    {"name": m["name"], "description": m["description"]}
                    for m in entry["mods"]
                )

        # Add categories to modifier groups
        for group in prefixes:
            prefixes[group] = {
                "mods": prefixes[group],
                "category": get_category_for_group(group),
            }
        for group in suffixes:
            suffixes[group] = {
                "mods": suffixes[group],
                "category": get_category_for_group(group),
            }

        # Count total individual modifiers
        prefix_count = sum(len(m["mods"]) for m in prefixes.values())
        suffix_count = sum(len(m["mods"]) for m in suffixes.values())
        total_mod_count = prefix_count + suffix_count
        result.append(
            {
                "tablet_type": tablet,
                "mod_count": total_mod_count,
                "prefix_count": prefix_count,
                "suffix_count": suffix_count,
                "prefixes": prefixes,
                "suffixes": suffixes,
            }
        )

    return result
