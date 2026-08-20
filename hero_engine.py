"""
hero_engine.py — Hero Calculator data and calculation engine.
Data sourced from TopHeroes Tables (1).xlsx — Heroes & Gear sheets.
"""
from __future__ import annotations

# ── Hero roster ───────────────────────────────────────────────────────────────
# tier     : "Mythic" | "Legendary"
# faction  : "Liga" | "Horda" | "Natureza"
# has_uw   : Exclusive Weapon (UW) available
# has_hs   : Heroic Spirit available
# skills   : number of skills (4 or 5)
# trait3   : hero-specific 3rd trait label (from spreadsheet col E)

HEROES: dict[str, dict] = {
    # ── Mythic ────────────────────────────────────────────────────────────────
    "Artificer":    {"tier": "Mythic", "faction": "Liga",     "has_uw": True,  "has_hs": True,  "skills": 5, "trait3": "Critical Resistance +30%"},
    "Bishop":       {"tier": "Mythic", "faction": "Liga",     "has_uw": True,  "has_hs": False, "skills": 5, "trait3": "HP Drain +20%"},
    "Lilia Maid":   {"tier": "Mythic", "faction": "Liga",     "has_uw": True,  "has_hs": False, "skills": 5, "trait3": "Critical Resistance +30%"},
    "Paragon":      {"tier": "Mythic", "faction": "Liga",     "has_uw": True,  "has_hs": True,  "skills": 5, "trait3": "HP Drain +20%"},
    "Rose Princess":{"tier": "Mythic", "faction": "Liga",     "has_uw": True,  "has_hs": True,  "skills": 5, "trait3": "Critical Resistance +30%"},
    "Beastmaster":  {"tier": "Mythic", "faction": "Horda",    "has_uw": True,  "has_hs": True,  "skills": 5, "trait3": "Skill Damage Reduction +50%"},
    "Desert Prince":{"tier": "Mythic", "faction": "Horda",    "has_uw": True,  "has_hs": True,  "skills": 5, "trait3": "Skill Damage Reduction +50%"},
    "Shadow Priest":{"tier": "Mythic", "faction": "Horda",    "has_uw": True,  "has_hs": False, "skills": 5, "trait3": "Critical Resistance +30%"},
    "Storm Maiden": {"tier": "Mythic", "faction": "Horda",    "has_uw": True,  "has_hs": True,  "skills": 5, "trait3": "HP Drain +20%"},
    "Wanderer":     {"tier": "Mythic", "faction": "Horda",    "has_uw": True,  "has_hs": False, "skills": 5, "trait3": "HP Drain +20%"},
    "Witch":        {"tier": "Mythic", "faction": "Horda",    "has_uw": True,  "has_hs": True,  "skills": 5, "trait3": "Critical Resistance +30%"},
    "Altar Marshal":{"tier": "Mythic", "faction": "Natureza", "has_uw": True,  "has_hs": True,  "skills": 5, "trait3": "HP Drain +20%"},
    "Monk":         {"tier": "Mythic", "faction": "Natureza", "has_uw": True,  "has_hs": True,  "skills": 5, "trait3": "Critical Resistance +30%"},
    "Petalis":      {"tier": "Mythic", "faction": "Natureza", "has_uw": True,  "has_hs": True,  "skills": 5, "trait3": "Critical Resistance +30%"},
    "Tidecaller":   {"tier": "Mythic", "faction": "Natureza", "has_uw": True,  "has_hs": True,  "skills": 5, "trait3": "Skill Damage Reduction +50%"},
    # ── Legendary ─────────────────────────────────────────────────────────────
    "Adjudicator":       {"tier": "Legendary", "faction": "Liga",     "has_uw": True,  "has_hs": True,  "skills": 5, "trait3": "Block +30%"},
    "Astrologer":        {"tier": "Legendary", "faction": "Liga",     "has_uw": True,  "has_hs": False, "skills": 5, "trait3": "Amplify Damage of the Skill +50%"},
    "Bard":              {"tier": "Legendary", "faction": "Liga",     "has_uw": True,  "has_hs": False, "skills": 5, "trait3": "Construction Rate +40%"},
    "Hostess":           {"tier": "Legendary", "faction": "Liga",     "has_uw": True,  "has_hs": False, "skills": 5, "trait3": "Soldier training speed +40%"},
    "Nun":               {"tier": "Legendary", "faction": "Liga",     "has_uw": True,  "has_hs": False, "skills": 5, "trait3": "Healing Rate +30%"},
    "Pyromancer":        {"tier": "Legendary", "faction": "Liga",     "has_uw": True,  "has_hs": False, "skills": 5, "trait3": "HP Drain +20%"},
    "Secret Keeper":     {"tier": "Legendary", "faction": "Liga",     "has_uw": True,  "has_hs": False, "skills": 5, "trait3": "PvP marching speed +50%"},
    "Barbarian":         {"tier": "Legendary", "faction": "Horda",    "has_uw": True,  "has_hs": False, "skills": 5, "trait3": "Block +30%"},
    "Headhunter":        {"tier": "Legendary", "faction": "Horda",    "has_uw": False, "has_hs": False, "skills": 5, "trait3": "Ruby Gathering Speed +40%"},
    "Shaman":            {"tier": "Legendary", "faction": "Horda",    "has_uw": True,  "has_hs": False, "skills": 4, "trait3": "Tech Research Rate +40%"},
    "Soulmancer":        {"tier": "Legendary", "faction": "Horda",    "has_uw": True,  "has_hs": False, "skills": 5, "trait3": "Critical Resistance +30%"},
    "Swordmaster":       {"tier": "Legendary", "faction": "Horda",    "has_uw": True,  "has_hs": False, "skills": 5, "trait3": "HP Drain +20%"},
    "Warlock":           {"tier": "Legendary", "faction": "Horda",    "has_uw": True,  "has_hs": False, "skills": 5, "trait3": "Daily Resource Plunder Limit +360 000"},
    "Wilderness Hunter": {"tier": "Legendary", "faction": "Horda",    "has_uw": True,  "has_hs": False, "skills": 5, "trait3": "Critical Damage +60%"},
    "Druid":             {"tier": "Legendary", "faction": "Natureza", "has_uw": True,  "has_hs": False, "skills": 5, "trait3": "Healing Rate +30%"},
    "Forest Maiden":     {"tier": "Legendary", "faction": "Natureza", "has_uw": True,  "has_hs": False, "skills": 5, "trait3": "Amplify Damage of the Skill +50%"},
    "Pixie":             {"tier": "Legendary", "faction": "Natureza", "has_uw": True,  "has_hs": False, "skills": 5, "trait3": "Amplify Damage of the Skill +50%"},
    "Sage":              {"tier": "Legendary", "faction": "Natureza", "has_uw": True,  "has_hs": False, "skills": 5, "trait3": "Skill Damage Reduction +50%"},
    "Stonemason":        {"tier": "Legendary", "faction": "Natureza", "has_uw": False, "has_hs": False, "skills": 5, "trait3": "Stone Gathering Speed +40%"},
    "Treeguard":         {"tier": "Legendary", "faction": "Natureza", "has_uw": True,  "has_hs": False, "skills": 5, "trait3": "Timber Gathering Speed +40%"},
    "Watcher":           {"tier": "Legendary", "faction": "Natureza", "has_uw": False, "has_hs": False, "skills": 5, "trait3": "Soldier Capacity +2000"},
    "Windwalker":        {"tier": "Legendary", "faction": "Natureza", "has_uw": True,  "has_hs": False, "skills": 5, "trait3": "Amplify Damage of the Skill +50%"},
}

MYTHIC_HEROES    = [n for n, d in HEROES.items() if d["tier"] == "Mythic"]
LEGENDARY_HEROES = [n for n, d in HEROES.items() if d["tier"] == "Legendary"]
ALL_HERO_NAMES   = MYTHIC_HEROES + LEGENDARY_HEROES

FACTION_HEROES: dict[str, list[str]] = {"Liga": [], "Horda": [], "Natureza": []}
for _name, _data in HEROES.items():
    FACTION_HEROES[_data["faction"]].append(_name)

HEROIC_SPIRIT_HEROES = [n for n, d in HEROES.items() if d["has_hs"]]

# ── Star / Leg system ─────────────────────────────────────────────────────────
# Each "star" has 5 legs. Total: 15 stars × 5 legs = 75 legs (idx 1-75).
# Colors: Color 1 (stars 1-5, legs 1-25), Color 2 (stars 6-10, legs 26-50),
#         Color 3 (stars 11-15, legs 51-75).
# Shards per leg: per the "Shards per Star" column (one leg = one unit).

def _build_leg_costs(per_star_costs: list[int]) -> list[int]:
    """per_star_costs: list of 15 values (one per star). Returns 75 per-leg costs."""
    out = []
    for c in per_star_costs:
        out.extend([c] * 5)
    return out

# Shard cost per leg — Legendary (15 stars)
_LEG_LEG = [1, 1, 2, 2, 4,    # Color 1 (Y)
             6, 4, 4, 8, 8,    # Color 2 (R)
             16, 4, 8, 16, 16] # Color 3 (P)
LEGENDARY_LEG_COSTS: list[int] = _build_leg_costs(_LEG_LEG)

# Shard cost per leg — Mythic (15 stars)
_MYT_LEG = [2, 2, 4, 4, 8,     # Color 1
             12, 8, 8, 16, 16,  # Color 2
             32, 8, 16, 32, 32] # Color 3
MYTHIC_LEG_COSTS: list[int] = _build_leg_costs(_MYT_LEG)

# Cumulative shards (index 0 = 0 legs done)
def _build_cumul(costs: list[int]) -> list[int]:
    c = [0]
    for v in costs:
        c.append(c[-1] + v)
    return c

LEGENDARY_CUMUL: list[int] = _build_cumul(LEGENDARY_LEG_COSTS)  # len 76
MYTHIC_CUMUL:    list[int] = _build_cumul(MYTHIC_LEG_COSTS)      # len 76

MAX_LEGS = 75  # legs 0-75

# Color boundaries (star groups)
COLOR_NAMES = {
    "Legendary": ["Amarela", "Vermelha", "Platinada"],
    "Mythic":    ["Amarela", "Vermelha", "Platinada"],
}
COLOR_BOUNDS = [0, 25, 50, 75]  # leg idx boundaries

# Star/leg display helpers
_STAR_COLORS_PT = ["Amarela", "Vermelha", "Platinada"]
_STAR_COLORS_EN = ["Yellow",  "Red",      "Platinum"]

def leg_to_display(leg_idx: int, lang: str = "pt") -> str:
    if leg_idx == 0:
        return "0★" if lang == "pt" else "0★"
    star_num = (leg_idx - 1) // 5 + 1
    leg_num  = (leg_idx - 1) % 5 + 1
    color_i  = (leg_idx - 1) // 25
    colors   = _STAR_COLORS_PT if lang == "pt" else _STAR_COLORS_EN
    color    = colors[color_i] if color_i < 3 else f"C{color_i+1}"
    star_in_color = (star_num - 1) % 5 + 1
    return f"⭐{star_in_color} {color} · {leg_num}/5"

def shards_for_legs(tier: str, from_leg: int, to_leg: int) -> int:
    cumul = LEGENDARY_CUMUL if tier == "Legendary" else MYTHIC_CUMUL
    return max(0, cumul[to_leg] - cumul[from_leg])


# ── Skill Books ───────────────────────────────────────────────────────────────
# Level 1 is baseline (no books). Levels 2-15 have progressive costs.
SKILL_BOOK_COSTS: list[int] = [0, 100, 200, 400, 600, 800, 1100, 1300, 1600, 1900, 2200, 2700, 3200, 3900, 4700]
SKILL_BOOK_CUMUL: list[int] = [sum(SKILL_BOOK_COSTS[:i+1]) for i in range(len(SKILL_BOOK_COSTS))]
MAX_SKILL_LEVEL = len(SKILL_BOOK_COSTS) - 1  # 14 upgrades → level 15


def books_for_one_skill(from_level: int, to_level: int) -> int:
    """Books for a single skill from_level → to_level (levels 1-15)."""
    f = max(0, min(from_level - 1, MAX_SKILL_LEVEL))
    t = max(0, min(to_level - 1, MAX_SKILL_LEVEL))
    return max(0, SKILL_BOOK_CUMUL[t] - SKILL_BOOK_CUMUL[f])


def books_for_skills(hero_name: str, from_level: int, to_level: int) -> int:
    """Total books for one skill (uniform levels) from_level → to_level."""
    return books_for_one_skill(from_level, to_level)


def total_books(hero_name: str, from_level: int, to_level: int) -> int:
    """Total books for ALL skills at the same level."""
    n_skills = HEROES[hero_name]["skills"]
    return n_skills * books_for_one_skill(from_level, to_level)


def total_books_per_skill(hero_name: str,
                          from_levels: list[int],
                          to_levels: list[int]) -> int:
    """Total books where each skill has its own from/to level."""
    n = HEROES[hero_name]["skills"]
    fl = (list(from_levels) + [1] * n)[:n]
    tl = (list(to_levels)   + [1] * n)[:n]
    return sum(books_for_one_skill(f, t) for f, t in zip(fl, tl))


# ── Awakening (Legendary only) ────────────────────────────────────────────────
# Uses faction-specific Soul Stones.
# Structure: (tier, level_within_tier, shards, soul_stones_at_this_step)
AWAKENING_STEPS: list[tuple[int, int, int, int]] = [
    # tier, sub-level, shards, SS
    (0, 0,  5, 1),  # Initial unlock
    (1, 1, 10, 0),
    (1, 2, 10, 0),
    (1, 3, 15, 0),
    (1, 4, 15, 0),
    (1, 5, 15, 2),  # Tier 1 complete → 2 SS
    (2, 0, 15, 0),
    (2, 1, 15, 0),
    (2, 2, 15, 0),
    (2, 3, 20, 0),
    (2, 4, 20, 0),
    (2, 5, 20, 2),  # Tier 2 complete → 2 SS
    (3, 0, 20, 0),
    (3, 1, 20, 0),
    (3, 2, 30, 0),
    (3, 3, 30, 0),
    (3, 4, 30, 0),
    (3, 5, 40, 4),  # Tier 3 complete → 4 SS
]
# Total: 345 shards, 9 Soul Stones for full awakening

AWK_STEP_LABELS: list[str] = ["Inativo"] + [
    f"T{t} L{l}" for t, l, _, _ in AWAKENING_STEPS
]
MAX_AWK_STEP = len(AWAKENING_STEPS)  # 18 steps (0 = not awakened)

def awk_cost(from_step: int, to_step: int) -> tuple[int, int]:
    """Returns (shards, soul_stones) for awakening from_step → to_step."""
    shards = sum(s for _, _, s, _ in AWAKENING_STEPS[from_step:to_step])
    ss     = sum(s for _, _, _, s in AWAKENING_STEPS[from_step:to_step])
    return shards, ss


# ── Heroic Spirit (simple table) ──────────────────────────────────────────────
# 9 heroes (3 per faction). Levels 1-100. Uses Heroic Spirit Shards.
_HS_RANGES = [
    (1,   1,  10),   # level 1: 10 shards
    (2,   5,   2),   # levels 2-5: 2 each
    (6,  10,   4),
    (11, 15,   6),
    (16, 20,   8),
    (21, 25,  10),
    (26, 30,  12),
    (31, 35,  14),
    (36, 40,  20),
    (41, 45,  24),
    (46, 50,  28),
    (51, 55,  32),
    (56, 60,  36),
    (61, 65,  40),
    (66, 70,  44),
    (71, 75,  48),
    (76, 80,  52),
    (81, 85,  56),
    (86, 90,  60),
    (91, 95,  65),
    (96, 100, 70),
]
MAX_HS_LEVEL = 100

# Build per-level cost lookup
HS_COST_PER_LEVEL: list[int] = [0] * (MAX_HS_LEVEL + 1)  # index = level
for _start, _end, _cost in _HS_RANGES:
    for _lv in range(_start, _end + 1):
        HS_COST_PER_LEVEL[_lv] = _cost

# Cumulative
HS_CUMUL: list[int] = [0] * (MAX_HS_LEVEL + 1)
for _lv in range(1, MAX_HS_LEVEL + 1):
    HS_CUMUL[_lv] = HS_CUMUL[_lv - 1] + HS_COST_PER_LEVEL[_lv]


def hs_shards(from_level: int, to_level: int) -> int:
    return max(0, HS_CUMUL[to_level] - HS_CUMUL[from_level])


# ── Unique Weapon / Exclusive Gear (UW) ───────────────────────────────────────
# 20 levels. Uses hero-specific UW Shards (or Universal UW Shards).
UW_SHARDS_PER_LEVEL: list[int] = [
    5, 10, 15, 20, 25, 30, 35, 40, 45, 50,
    55, 60, 65, 70, 80, 90, 100, 110, 130, 150,
]
MAX_UW_LEVEL = len(UW_SHARDS_PER_LEVEL)  # 20

UW_CUMUL: list[int] = [0]
for _c in UW_SHARDS_PER_LEVEL:
    UW_CUMUL.append(UW_CUMUL[-1] + _c)


def uw_shards(from_level: int, to_level: int) -> int:
    f = max(0, min(from_level, MAX_UW_LEVEL))
    t = max(0, min(to_level,   MAX_UW_LEVEL))
    return max(0, UW_CUMUL[t] - UW_CUMUL[f])


# ── Traits ────────────────────────────────────────────────────────────────────
# 4 types per hero, each up to level 30.
# Unlock next type requires previous type at level ≥ 5.
# First level of each type: diamonds cost. Levels 2-30: 10 trait shards each.
TRAIT_TYPE_NAMES_PT = ["Ataque", "HP", "Exclusivo", "HP (T4)"]
TRAIT_TYPE_NAMES_EN = ["Attack", "HP", "Exclusive",  "HP (T4)"]
TRAIT_DIAMOND_COSTS = [200, 500, 1000, 2000]   # to unlock level 1 of each type
TRAIT_FRAGS_PER_LEVEL = 10                      # levels 2-30
TRAIT_UNLOCK_PREREQ   = 5                        # min level of prev type to unlock next
MAX_TRAIT_LEVEL       = 30


def trait_cost(type_idx: int, from_level: int, to_level: int) -> tuple[int, int]:
    """Returns (diamonds, trait_shards) to go from_level → to_level for one trait type."""
    diamonds = TRAIT_DIAMOND_COSTS[type_idx] if from_level == 0 and to_level >= 1 else 0
    frag_start = max(from_level, 1)  # level 1 costs diamonds only
    frag_end   = to_level
    frags = max(0, frag_end - frag_start) * TRAIT_FRAGS_PER_LEVEL
    return diamonds, frags


def total_trait_cost(from_levels: list[int], to_levels: list[int]) -> tuple[int, int]:
    """Sum across all 4 trait types. from_levels/to_levels: list of 4 ints."""
    total_dia = total_frags = 0
    for i in range(4):
        d, f = trait_cost(i, from_levels[i], to_levels[i])
        total_dia   += d
        total_frags += f
    return total_dia, total_frags


# ── Combined calculator ───────────────────────────────────────────────────────

def calc_hero(
    hero_name: str,
    # Stars
    from_leg: int = 0,
    to_leg: int = 0,
    # Skills — uniform or per-skill
    from_skill_lv: int = 1,
    to_skill_lv: int = 1,
    from_skills: list[int] | None = None,  # per-skill (overrides from_skill_lv)
    to_skills:   list[int] | None = None,  # per-skill (overrides to_skill_lv)
    # Awakening (step index 0-18)
    from_awk: int = 0,
    to_awk: int = 0,
    # Heroic Spirit
    from_hs: int = 0,
    to_hs: int = 0,
    # UW
    from_uw: int = 0,
    to_uw: int = 0,
    # Traits (per type)
    from_traits: list[int] | None = None,
    to_traits:   list[int] | None = None,
) -> dict:
    hero = HEROES[hero_name]
    tier = hero["tier"]

    result: dict = {
        "hero":           hero_name,
        "tier":           tier,
        "faction":        hero["faction"],
        # Stars
        "star_shards":    shards_for_legs(tier, from_leg, to_leg),
        # Skills (per-skill if provided, otherwise uniform)
        "skill_books":    (total_books_per_skill(hero_name, from_skills, to_skills)
                           if from_skills is not None and to_skills is not None
                           else total_books(hero_name, from_skill_lv, to_skill_lv)),
        # Awakening
        "awk_shards":     0,
        "awk_ss":         0,
        # Heroic Spirit
        "hs_shards":      hs_shards(from_hs, to_hs) if hero["has_hs"] else 0,
        # UW
        "uw_shards":      uw_shards(from_uw, to_uw) if hero["has_uw"] else 0,
        # Traits
        "trait_diamonds": 0,
        "trait_shards":   0,
    }

    if tier == "Legendary" and to_awk > from_awk:
        result["awk_shards"], result["awk_ss"] = awk_cost(from_awk, to_awk)

    if from_traits is None:
        from_traits = [0, 0, 0, 0]
    if to_traits is None:
        to_traits = [0, 0, 0, 0]
    result["trait_diamonds"], result["trait_shards"] = total_trait_cost(from_traits, to_traits)

    return result
