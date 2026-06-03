from __future__ import annotations
"""
pet_engine.py — Pet Calculator data and calculation engine.
"""

PETS = [
    # (name, faction, faction_specific, active_skill, passive_buff)
    ("Eggy",        "League", True,  "2 heroes gain Crit Rate & Crit DMG boost temporarily",                "Increased damage each time an enemy dies"),
    ("Zappy",       "League", False, "2 heroes gain Normal Attack DMG boost for 4 attacks",                 "Reduce enemy healing & boost skill damage"),
    ("Candiboo",    "League", True,  "2 heroes gain Normal Atk Reduction & DMG boost temporarily",          "Increased Soldier Attack & HP"),
    ("Snowball",    "League", True,  "Pet attacks 2 enemies & reduces their Attack temporarily",            "Increased Soldier Attack & HP"),
    ("Howli",       "Horde",  False, "Pet attacks 2 enemies & increases their DMG taken temporarily",       "All heroes DMG increase & ignore enemy DMG reduction"),
    ("Flickerkit",  "Horde",  True,  "Pet attacks 4 enemies & reduce their DMG Reduction temporarily",      "Increased DMG & DMG Reduction to Horde heroes"),
    ("Tiggy",       "Horde",  True,  "Pet attacks 2 enemies & reduce their DMG increase temporarily",       "Increased Soldier Attack & HP"),
    ("Time Dragon", "Horde",  True,  "Pet attacks 2 enemies & reduce their Critical DMG temporarily",       "Increased Soldier Attack & HP"),
    ("Spark",       "Horde",  True,  "—",                                                                   "—"),
    ("Cactini",     "Nature", True,  "Pet attacks 2 enemies & lowers their Crit Rate temporarily",          "All heroes Attack increases"),
    ("Sproutfang",  "Nature", False, "Pet attacks 2 enemies & lowers their Defense temporarily",            "—"),
    ("Cubbly",      "Nature", False, "Reduces heroes Crit DMG taken & deals a counter-attack",              "Boost to active shields & HP increase"),
    ("Pegasus",     "Nature", True,  "Pet attacks 2 enemies & reduces their Amplify DMG skill temporarily",  "Increased Soldier Attack & HP"),
    ("Snowpal",     "Nature", False, "Slow Attack & Movement of 3 enemies temporarily",                     "All heroes Attack increases + Increased Soldier Attack & HP"),
    ("Tidal Crab",  "Nature", True,  "—",                                                                   "—"),
]

PROMO_LIST = [
    # (min_lvl, label, tier, same_copies_cost, any_copies_cost)
    (0,   "RARE ☆",          "RARE",      0, 0),
    (10,  "RARE ★",          "RARE",      1, 0),
    (20,  "RARE ★★",         "RARE",      0, 3),
    (30,  "RARE ★★★",        "RARE",      1, 0),
    (35,  "RARE ★★★★",       "RARE",      0, 3),
    (40,  "RARE ★★★★★",      "RARE",      1, 5),
    (45,  "EPIC ☆",          "EPIC",      1, 5),
    (50,  "EPIC ★",          "EPIC",      2, 5),
    (55,  "EPIC ★★",         "EPIC",      2, 10),
    (60,  "EPIC ★★★",        "EPIC",      3, 10),
    (65,  "EPIC ★★★★",       "EPIC",      3, 15),
    (70,  "EPIC ★★★★★",      "EPIC",      4, 15),
    (75,  "LEGENDARY ☆",     "LEGENDARY", 5, 15),
    (80,  "LEGENDARY ★",     "LEGENDARY", 3, 10),
    (85,  "LEGENDARY ★★",    "LEGENDARY", 4, 15),
    (90,  "LEGENDARY ★★★",   "LEGENDARY", 5, 20),
    (95,  "LEGENDARY ★★★★",  "LEGENDARY", 6, 20),
    (100, "LEGENDARY ★★★★★", "LEGENDARY", 8, 30),
    (100, "MYTHIC",          "MYTHIC",    3, 10),
]

RARE_SAME = {10:1, 30:1, 40:1, 45:1, 50:2, 55:2, 60:3, 65:3, 70:4, 75:5,
             80:3, 85:4, 90:5, 95:6, 100:8}
RARE_ANY  = {20:3, 35:3, 40:5, 45:5, 50:5, 55:10, 60:10, 65:15, 70:15, 75:15,
             80:10, 85:15, 90:20, 95:20, 100:30}

# (level, cumulative_food, per_level_essence)
RARE_ALL = [
    (1,0,0),(2,100,0),(3,250,0),(4,450,0),(5,700,0),(6,1000,0),(7,1400,0),
    (8,1900,0),(9,2500,0),(10,3200,0),(11,4000,0),(12,4900,0),(13,5900,0),
    (14,7000,0),(15,8200,0),(16,9500,0),(17,10900,0),(18,12400,0),(19,14000,0),
    (20,15700,0),(21,17500,0),(22,19400,0),(23,21400,0),(24,23500,0),(25,25700,0),
    (26,28000,0),(27,30400,0),(28,32900,0),(29,35500,0),(30,38250,0),
    (31,41150,0),(32,44200,0),(33,47400,0),(34,50750,0),(35,54250,0),
    (36,57900,0),(37,61700,0),(38,65650,0),(39,69750,0),(40,74050,0),
    (41,78550,0),(42,83250,0),(43,88150,0),(44,93250,0),(45,98550,0),
    (46,104050,0),(47,109750,0),(48,115650,0),(49,121750,0),(50,128100,0),
    (51,134700,0),(52,141550,0),(53,148650,0),(54,156000,0),(55,163600,0),
    (56,171450,0),(57,179550,0),(58,187900,0),(59,196500,0),(60,205350,0),
    (61,214450,0),(62,223800,0),(63,233400,0),(64,243250,0),(65,253350,0),
    (66,263700,0),(67,274300,0),(68,285150,0),(69,296250,0),(70,307600,0),
    (71,319200,0),(72,331100,0),(73,343300,0),(74,355800,0),(75,368600,0),
    (76,381700,0),(77,395100,0),(78,408800,0),(79,422800,0),
    (80,437100,1000),(81,451700,1000),(82,466600,1000),(83,481800,1000),(84,497300,1000),
    (85,513100,3000),(86,529200,3000),(87,545600,3000),(88,562300,3000),(89,579300,3000),
    (90,596600,7000),
    (91,602500,7050),(92,608500,7200),(93,614600,7500),(94,620800,8000),
    (95,627200,14250),
    (96,633700,14550),(97,640300,14900),(98,647100,15300),(99,654000,15750),
    (100,661000,24250),
    (101,668200,24250),(102,675500,24250),(103,682900,24250),(104,690500,24250),
    (105,698200,24250),(106,706000,24250),(107,714000,24250),
]

STATS = {
    1:  (0.36, "1.70%",  "5.10%",  "2.50%",  "7.50%",  35),
    10: (0.40, "3.40%",  "10.20%", "5.00%",  "15.00%", 40),
    20: (0.44, "5.10%",  "15.30%", "7.50%",  "22.50%", 45),
    30: (0.48, "6.80%",  "20.40%", "10.00%", "30.00%", 50),
    35: (0.52, "8.50%",  "25.50%", "12.50%", "37.50%", 55),
    40: (0.56, "10.20%", "30.60%", "15.00%", "45.00%", 60),
    45: (0.60, "11.90%", "35.70%", "17.50%", "52.50%", 70),
    50: (0.64, "13.60%", "40.80%", "20.00%", "60.00%", 80),
    55: (0.68, "15.30%", "45.90%", "22.50%", "67.50%", 90),
    60: (0.72, "17.00%", "51.00%", "25.00%", "75.00%", 90),
    65: (0.76, "18.70%", "56.10%", "27.50%", "82.50%", 90),
    70: (0.80, "20.40%", "61.20%", "30.00%", "90.00%", 90),
    75: (0.84, "22.10%", "66.30%", "32.50%", "97.50%", 90),
    80: (0.88, "23.80%", "71.40%", "35.00%", "105.00%", 95),
    85: (0.92, "25.50%", "76.50%", "37.50%", "112.50%", 100),
    90: (0.96, "27.20%", "81.60%", "40.00%", "120.00%", 105),
    95: (1.00, "28.90%", "86.70%", "42.50%", "127.50%", 110),
    100:(1.04, "30.60%", "91.80%", "45.00%", "135.00%", 115),
}

# Total resources required to reach each tier from scratch
TIER_TARGETS = {
    "EPIC":      (98550,   4,  16,     0),
    "LEGENDARY": (368600, 23,  86,     0),
    "MYTHIC":    (661000, 52, 191, 33750),
}

TIER_RANK = {"RARE": 0, "EPIC": 1, "LEGENDARY": 2, "MYTHIC": 3}

FACTION_EMOJI = {"League": "🔵", "Horde": "🔴", "Nature": "🟢"}

# ── Pre-built lookup tables ────────────────────────────────────────────────────
FOOD_AT_LEVEL = {lvl: food for lvl, food, _ in RARE_ALL}

_ess_cum = 0
ESS_AT_LEVEL: dict[int, int] = {}
for _lvl, _food, _ess in RARE_ALL:
    _ess_cum += _ess
    ESS_AT_LEVEL[_lvl] = _ess_cum

MAX_LEVEL = max(lvl for lvl, _, _ in RARE_ALL)

# Cumulative copies used across all promotions up to and including each promo entry
_PROMO_CUM: dict[tuple, tuple[int, int]] = {}
for _min_lvl, _lbl, _tier, _s, _a in PROMO_LIST:
    cs = sum(RARE_SAME.get(l, 0) for l in range(0, _min_lvl + 1))
    ca = sum(RARE_ANY.get(l, 0)  for l in range(0, _min_lvl + 1))
    _PROMO_CUM[(_min_lvl, _lbl)] = (cs, ca)


def promo_cum(promo_min_lvl: int, promo_label: str) -> tuple[int, int]:
    return _PROMO_CUM.get((promo_min_lvl, promo_label), (0, 0))


def calc_milestone(tier: str, current_level: int, promo_min_lvl: int, promo_label: str,
                   inv_food: int, inv_essence: int,
                   inv_same_selected: int, total_any: int) -> dict:
    tgt_food, tgt_same, tgt_any, tgt_ess = TIER_TARGETS[tier]
    food_spent = FOOD_AT_LEVEL.get(current_level, 0)
    ess_spent  = ESS_AT_LEVEL.get(current_level, 0)
    cum_same, cum_any = promo_cum(promo_min_lvl, promo_label)
    return {
        "food":    max(0, tgt_food - food_spent - inv_food),
        "same":    max(0, tgt_same - cum_same   - inv_same_selected),
        "any":     max(0, tgt_any  - cum_any    - total_any),
        "essence": max(0, tgt_ess  - ess_spent  - inv_essence),
    }


def calc_to_target(from_lvl: int, to_lvl: int) -> dict:
    return {
        "food":    max(0, FOOD_AT_LEVEL.get(to_lvl, 0) - FOOD_AT_LEVEL.get(from_lvl, 0)),
        "essence": max(0, ESS_AT_LEVEL.get(to_lvl, 0)  - ESS_AT_LEVEL.get(from_lvl, 0)),
        "same":    sum(RARE_SAME.get(l, 0) for l in range(from_lvl + 1, to_lvl + 1)),
        "any":     sum(RARE_ANY.get(l, 0)  for l in range(from_lvl + 1, to_lvl + 1)),
    }


def max_level_with_food(current_lvl: int, inv_food: int) -> int:
    available = FOOD_AT_LEVEL.get(current_lvl, 0) + inv_food
    result = current_lvl
    for lvl, food, _ in RARE_ALL:
        if food <= available:
            result = lvl
        else:
            break
    return result


def get_stats(level: int) -> tuple:
    stat_lvl = max((s for s in STATS if s <= level), default=1)
    return STATS[stat_lvl]
