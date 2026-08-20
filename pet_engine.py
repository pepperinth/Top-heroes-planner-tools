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
    # (min_lvl, label, tier, same_copies_cost, any_copies_cost, promo_essence)
    # Promotions from RARE through LEGENDARY ☆ require no essence.
    # LEGENDARY ★ and above require promotion essence (separate from level-up essence).
    # MYTHIC requires level 101 and 10 000 promotion essence.
    (0,   "RARE ☆",          "RARE",      0, 0,  0),
    (10,  "RARE ★",          "RARE",      1, 0,  0),
    (20,  "RARE ★★",         "RARE",      0, 3,  0),
    (30,  "RARE ★★★",        "RARE",      1, 0,  0),
    (35,  "RARE ★★★★",       "RARE",      0, 3,  0),
    (40,  "RARE ★★★★★",      "RARE",      1, 5,  0),
    (45,  "EPIC ☆",          "EPIC",      1, 5,  0),
    (50,  "EPIC ★",          "EPIC",      2, 5,  0),
    (55,  "EPIC ★★",         "EPIC",      2, 10, 0),
    (60,  "EPIC ★★★",        "EPIC",      3, 10, 0),
    (65,  "EPIC ★★★★",       "EPIC",      3, 15, 0),
    (70,  "EPIC ★★★★★",      "EPIC",      4, 15, 0),
    (75,  "LEGENDARY ☆",     "LEGENDARY", 5, 15, 0),
    (80,  "LEGENDARY ★",     "LEGENDARY", 3, 10, 1000),
    (85,  "LEGENDARY ★★",    "LEGENDARY", 4, 15, 2000),
    (90,  "LEGENDARY ★★★",   "LEGENDARY", 5, 20, 4000),
    (95,  "LEGENDARY ★★★★",  "LEGENDARY", 6, 20, 6000),
    (100, "LEGENDARY ★★★★★", "LEGENDARY", 8, 30, 8000),
    (100, "MYTHIC",          "MYTHIC",    8, 30, 10000),
]

RARE_SAME = {10:1, 30:1, 40:1, 45:1, 50:2, 55:2, 60:3, 65:3, 70:4, 75:5,
             80:3, 85:4, 90:5, 95:6, 100:8}
RARE_ANY  = {20:3, 35:3, 40:5, 45:5, 50:5, 55:10, 60:10, 65:15, 70:15, 75:15,
             80:10, 85:15, 90:20, 95:20, 100:30}

# (level, cumulative_food, per_level_essence)
# Per-level essence starts at level 91 (50/level, +50 each level).
# Levels 1-90 cost no essence to level up.
# Promotion essence is tracked separately in PROMO_LIST (6th column).
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
    (80,437100,0),(81,451700,0),(82,466600,0),(83,481800,0),(84,497300,0),
    (85,513100,0),(86,529200,0),(87,545600,0),(88,562300,0),(89,579300,0),
    (90,596600,0),
    (91,602500,50),(92,608500,100),(93,614600,150),(94,620800,200),
    (95,627200,250),
    (96,633700,300),(97,640300,350),(98,647100,400),(99,654000,450),
    (100,661000,500),
    (101,668200,600),(102,675500,700),(103,682900,800),(104,690500,900),
    (105,698200,1000),(106,706000,1100),(107,714000,1200),
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
    65: (0.76, "18.70%", "56.10%", "27,50%", "82.50%", 90),
    70: (0.80, "20.40%", "61.20%", "30.00%", "90.00%", 90),
    75: (0.84, "22.10%", "66.30%", "32.50%", "97.50%", 90),
    80: (0.88, "23.80%", "71.40%", "35.00%", "105.00%", 95),
    85: (0.92, "25.50%", "76.50%", "37.50%", "112.50%", 100),
    90: (0.96, "27.20%", "81.60%", "40.00%", "120.00%", 105),
    95: (1.00, "28.90%", "86.70%", "42.50%", "127.50%", 110),
    100:(1.04, "30.60%", "91.80%", "45.00%", "135.00%", 115),
}

TIER_RANK  = {"RARE": 0, "EPIC": 1, "LEGENDARY": 2, "MYTHIC": 3}
PROMO_INDEX = {p[1]: i for i, p in enumerate(PROMO_LIST)}

# Label of the first promotion that counts as "reaching" each broad tier milestone
TIER_TARGET_PROMO_LABEL = {
    "EPIC":      "EPIC ☆",
    "LEGENDARY": "LEGENDARY ☆",
    "MYTHIC":    "MYTHIC",
}

FACTION_EMOJI = {"League": "🔵", "Horde": "🔴", "Nature": "🟢"}

# ── Pre-built lookup tables ────────────────────────────────────────────────────
FOOD_AT_LEVEL = {lvl: food for lvl, food, _ in RARE_ALL}

_ess_cum = 0
ESS_AT_LEVEL: dict[int, int] = {}
for _lvl, _food, _ess in RARE_ALL:
    _ess_cum += _ess
    ESS_AT_LEVEL[_lvl] = _ess_cum

MAX_LEVEL = max(lvl for lvl, _, _ in RARE_ALL)

TIER_MIN_LEVEL = {
    tier: min(p[0] for p in PROMO_LIST if p[2] == tier)
    for tier in set(p[2] for p in PROMO_LIST)
}

# Cumulative (same_copies, any_copies, promo_essence) up to and including each promotion.
# Keyed by promotion label. Accumulated in PROMO_LIST order so promotions at the same
# min_lvl (e.g. LEGENDARY★★★★★ then MYTHIC) stack correctly.
_PROMO_CUM: dict[str, tuple[int, int, int]] = {}
_cs_run = _ca_run = _ce_run = 0
for _min_lvl, _lbl, _tier, _s, _a, _e in PROMO_LIST:
    _cs_run += _s
    _ca_run += _a
    _ce_run += _e
    _PROMO_CUM[_lbl] = (_cs_run, _ca_run, _ce_run)


def promo_cum(promo_label: str) -> tuple[int, int, int]:
    """Cumulative (same_copies, any_copies, promo_essence) up to this promotion."""
    return _PROMO_CUM.get(promo_label, (0, 0, 0))


def calc_to_promo(target_label: str, current_level: int, current_promo_label: str,
                  inv_food: int, inv_essence: int, inv_same: int, inv_any: int) -> dict:
    """Resources needed to reach a specific target promotion from current state."""
    tgt = next(p for p in PROMO_LIST if p[1] == target_label)
    tgt_min_lvl = tgt[0]

    tgt_food_cum = FOOD_AT_LEVEL.get(tgt_min_lvl, 0)
    cur_food_cum = FOOD_AT_LEVEL.get(current_level, 0)

    # Level-up essence: cumulative cost of levels between current and target min level
    tgt_lvl_ess = ESS_AT_LEVEL.get(tgt_min_lvl, 0)
    cur_lvl_ess = ESS_AT_LEVEL.get(current_level, 0)

    # Promotion essence: accumulated cost of each individual promotion step
    tgt_same_cum, tgt_any_cum, tgt_promo_ess_cum = promo_cum(target_label)
    cur_same_cum, cur_any_cum, cur_promo_ess_cum = promo_cum(current_promo_label)

    same_gross   = tgt_same_cum - cur_same_cum
    surplus_same = max(0, inv_same - same_gross)   # surplus same copies can count as any
    return {
        "food":    max(0, tgt_food_cum - cur_food_cum - inv_food),
        "essence": max(0, (tgt_lvl_ess - cur_lvl_ess) + (tgt_promo_ess_cum - cur_promo_ess_cum) - inv_essence),
        "same":    max(0, same_gross - inv_same),
        "any":     max(0, tgt_any_cum  - cur_any_cum  - inv_any - surplus_same),
        "min_lvl": tgt_min_lvl,
    }


def calc_milestone(tier: str, current_level: int, current_promo_label: str,
                   inv_food: int, inv_essence: int,
                   inv_same_selected: int, total_any: int) -> dict:
    """Resources remaining to reach the entry promotion of a broad tier (EPIC ☆ / LEGENDARY ☆ / MYTHIC)."""
    target_label = TIER_TARGET_PROMO_LABEL[tier]
    return calc_to_promo(target_label, current_level, current_promo_label,
                         inv_food, inv_essence, inv_same_selected, total_any)


def calc_to_target(from_lvl: int, to_lvl: int) -> dict:
    """Resources to level up from from_lvl to to_lvl (ignores promotion essence)."""
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
