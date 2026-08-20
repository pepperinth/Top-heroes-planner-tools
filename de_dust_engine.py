from __future__ import annotations
"""
de_dust_engine.py
Pure-logic layer for the DE & Dust Planner.
No Streamlit dependency.
"""

BARS_PER_B = 5

# ── Building catalogue ─────────────────────────────────────────────────────────
# costs: DE per bar for each B transition (index 0 = B0→B1 … 5 = B5→B6)
# None = that transition does not exist for this building
BUILDINGS = {
    "castle": {"en": "Castle",              "pt": "Castelo",             "faction": "all",    "costs": [126, 151, 227, 303, 388, 485]},
    "brk_l":  {"en": "Barracks (League)",   "pt": "Quartel (League)",    "faction": "league", "costs": [57,  68,  120, 181, 266, 333]},
    "brk_h":  {"en": "Barracks (Horde)",    "pt": "Quartel (Horde)",     "faction": "horde",  "costs": [57,  68,  120, 181, 266, 333]},
    "brk_n":  {"en": "Barracks (Nature)",   "pt": "Quartel (Nature)",    "faction": "nature", "costs": [57,  68,  120, 181, 266, 333]},
    "stat_l": {"en": "Statue (League)",     "pt": "Estátua (League)",    "faction": "league", "costs": [57,  68,  120, 181, 266, None]},
    "stat_h": {"en": "Statue (Horde)",      "pt": "Estátua (Horde)",     "faction": "horde",  "costs": [57,  68,  120, 181, 266, None]},
    "stat_n": {"en": "Statue (Nature)",     "pt": "Estátua (Nature)",    "faction": "nature", "costs": [57,  68,  120, 181, 266, None]},
    "tg":     {"en": "Training Ground",     "pt": "Campo de Treino",     "faction": "all",    "costs": [18,  23,  35,  48,  None, None]},
    "milh":   {"en": "Military Hall",       "pt": "Salão Militar",       "faction": "all",    "costs": [95,  114, 205, None, None, None]},
    "hosp":   {"en": "Hospital",            "pt": "Hospital",            "faction": "all",    "costs": [25,  30,  45,  64,  86,  None]},
    "sword":  {"en": "Sword",               "pt": "Espada",              "faction": "all",    "costs": [32,  57,  67,  None, None, None]},
    "shield": {"en": "Shield",              "pt": "Escudo",              "faction": "all",    "costs": [32,  57,  67,  None, None, None]},
    "rc":     {"en": "Research Cottage",    "pt": "Cabana de Pesquisa",  "faction": "all",    "costs": [32,  57,  67,  None, None, None]},
    "guild":  {"en": "Guild Building",      "pt": "Guildas",             "faction": "all",    "costs": [32,  57,  67,  None, None, None]},
    "watch":  {"en": "Watchtower",          "pt": "Torre de Vigia",      "faction": "all",    "costs": [38,  68,  None, None, None, None]},
    "medal":  {"en": "Medal Hall",          "pt": "Salão de Medalhas",   "faction": "all",    "costs": [95,  114, 205, None, None, None]},
    "troop":  {"en": "Troop Skin Center",   "pt": "Centro de Skins",     "faction": "all",    "costs": [95,  114, 205, None, None, None]},
    # Brilliance Institute: separate building, unlocks at Castle B2.
    # 15 levels (not standard B structure). Costs: lv1-6=32, lv7-11=57, lv12-15=67. Total=745 DE.
    "bi":     {"en": "Brilliance Institute","pt": "Instituto de Brilhantismo", "faction": "all",    "costs": [32,  57,  67,  None, None, None], "bi_special": True},
}

BI_LEVEL_COSTS = [32] * 6 + [57] * 5 + [67] * 4   # 15 levels, 745 DE total


# ── Castle prerequisite chain ──────────────────────────────────────────────────
# What must be ready BEFORE the castle can start each B level.
# "rc_lv40" / "hosp_lv40" are regular (pre-Brilliance) building levels;
# their DE cost is not in our data, so they are shown as warnings only.
CASTLE_PREREQS = {
    1: [("rc_lv40",  40), ("hosp_lv40", 40)],
    2: [("brk_l",    1),  ("guild",      1)],
    3: [("brk_h",    1),  ("hosp",       1)],
    4: [("brk_n",    3),  ("guild",      3)],
    5: [("hosp",     4),  ("brk_any",    4)],
    6: [("hosp",     5),  ("brk_any",    5)],
}

PREREQ_LABELS = {
    "rc_lv40":   {"en": "Research Cottage (regular lv.40)", "pt": "Cabana de Pesquisa (nível normal 40)"},
    "hosp_lv40": {"en": "Hospital (regular lv.40)",          "pt": "Hospital (nível normal 40)"},
    "brk_any":   {"en": "Any Barracks",                      "pt": "Qualquer Quartel"},
}

FACTION_LABEL = {
    "all":    {"en": "All factions", "pt": "Todas as facções"},
    "league": {"en": "League",       "pt": "Liga"},
    "horde":  {"en": "Horde",        "pt": "Horda"},
    "nature": {"en": "Nature",       "pt": "Natureza"},
}


# ── Core computations ──────────────────────────────────────────────────────────

def max_b(building_id: str) -> int:
    """Maximum available Brilliance level for a building."""
    costs = BUILDINGS.get(building_id, {}).get("costs", [])
    return sum(1 for c in costs if c is not None)


def de_cost(building_id: str, from_b: int, to_b: int) -> int:
    """DE to go from Brilliance level from_b to to_b (each B = 5 bars)."""
    if building_id not in BUILDINGS or from_b >= to_b:
        return 0
    costs = BUILDINGS[building_id]["costs"]
    total = 0
    for b in range(from_b, to_b):
        if b < len(costs) and costs[b] is not None:
            total += costs[b] * BARS_PER_B
    return total


def bi_de_cost(from_lv: int, to_lv: int) -> int:
    """DE cost for Brilliance Institute from_lv → to_lv (1-indexed levels)."""
    return sum(BI_LEVEL_COSTS[i] for i in range(from_lv, min(to_lv, 15)))


def bar_labels(building_id: str) -> list:
    """Display labels for each bar level from B0 to max B.

    Bar 0 = level 40 (shown as "40"); bars 1-4 = 41-44;
    bar 5 = B1 (level 45); bars 6-9 = 46-49; bar 10 = B2; etc.
    Only B0 is shown as its numeric level; higher B-boundaries use "B1", "B2", …
    """
    mxb = max_b(building_id)
    labels = []
    for i in range(mxb * 5 + 1):
        if i == 0:
            labels.append("40")
        elif i % 5 == 0:
            labels.append(f"B{i // 5}")
        else:
            labels.append(str(40 + i))
    return labels


def de_cost_bar(building_id: str, from_bar: int, to_bar: int) -> int:
    """DE cost at single-bar granularity (from_bar and to_bar are bar indices).

    Bar index = b_level * 5 + bar_within_b.  Each bar costs costs[b_idx] DE.
    """
    if building_id not in BUILDINGS or from_bar >= to_bar:
        return 0
    costs = BUILDINGS[building_id]["costs"]
    total = 0
    for bar in range(from_bar, to_bar):
        b_idx = bar // 5
        if b_idx < len(costs) and costs[b_idx] is not None:
            total += costs[b_idx]
    return total


# ── Research data (Dragon Dust) ────────────────────────────────────────────────
# levels: dust cost per level (index 0 = lv0→lv1).  None = data unavailable.
# biReq (BI_R only): minimum Brilliance Institute level required to unlock.

BI_R = [
    {"name": "Training Speed 1",   "biReq": 1,  "levels": [1,1,2,2,2,2,3,3,4,4]},
    {"name": "Relic HP",           "biReq": 3,  "levels": [8,10,11,13,16,19,23,27,32,38]},
    {"name": "Relic Attack",       "biReq": 3,  "levels": [8,10,11,13,16,19,23,27,32,38]},
    {"name": "Soldier Assault 1",  "biReq": 5,  "levels": [12,14,16,20,23,28,34,40,48,57]},
    {"name": "Soldier Defense 1",  "biReq": 5,  "levels": [12,14,16,20,23,28,34,40,48,57]},
    {"name": "March Size",         "biReq": 5,  "levels": [16,19,22,26,31,37,45,54,64,76]},
    {"name": "Hero Level",         "biReq": 7,  "levels": [62,131]},
    {"name": "Soldier Capacity 1", "biReq": 9,  "levels": [26,34,47,71,112]},
    {"name": "Training Mastery",   "biReq": 9,  "levels": [26,34,47,71,112]},
    {"name": "Healing Speed",      "biReq": 9,  "levels": [44,57,78,117,186]},
    {"name": "Hero Assault 1",     "biReq": 11, "levels": [46,55,64,78,92,110,133,160,192,228]},
    {"name": "Hero Defense 1",     "biReq": 11, "levels": [46,55,64,78,92,110,133,160,192,228]},
    {"name": "Healing Boost",      "biReq": 13, "levels": [70,90,125,187,298]},
    {"name": "Hero Assault 2",     "biReq": 13, "levels": [57,69,80,97,114,137,166,200,239,285]},
    {"name": "Hero Defense 2",     "biReq": 13, "levels": [57,69,80,97,114,137,166,200,239,285]},
    {"name": "Soldier Level",      "biReq": 15, "levels": [288]},
    {"name": "Hero Level 2",       "biReq": 15, "levels": [189,321,642]},
]

FAC_R = [
    # Tier 1 (items 0-5)
    {"name": "Soldier Attack 1",        "levels": [4,5,7,10,15]},
    {"name": "Soldier HP 1",            "levels": [4,5,7,10,15]},
    {"name": "Damage on Counter 1",     "levels": [5,6,8,11,18]},
    {"name": "Hero Attack 1",           "levels": [5,7,9,13,21]},
    {"name": "Hero HP 1",               "levels": [5,7,9,13,21]},
    {"name": "Dmg Reduction Counter 1", "levels": [6,7,10,15,24]},
    # Tier 2 (items 6-11)
    {"name": "Soldier Attack 2",        "levels": [5,6,7,8,9,11,13,16,19,23]},
    {"name": "Soldier HP 2",            "levels": [5,6,7,8,9,11,13,16,19,23]},
    {"name": "Damage on Counter 2",     "levels": [14,18,25,37,58]},
    {"name": "Hero Attack 2",           "levels": [9,11,13,15,18,22,26,31,37,45]},
    {"name": "Hero HP 2",               "levels": [9,11,13,15,18,22,26,31,37,45]},
    {"name": "Dmg Reduction Counter 2", "levels": [24,31,34,64,101]},
    # Tier 3 (items 12-17)
    {"name": "Soldier Attack 3",        "levels": [12,15,17,20,24,29,35,42,50,59]},
    {"name": "Soldier HP 3",            "levels": [12,15,17,20,24,29,35,42,50,59]},
    {"name": "Damage on Counter 3",     "levels": [34,44,61,91,144]},
    {"name": "Hero Attack 3",           "levels": [17,20,23,28,33,39,47,57,68,81]},
    {"name": "Hero HP 3",               "levels": [17,20,23,28,33,39,47,57,68,81]},
    {"name": "Dmg Reduction Counter 3", "levels": [41,53,61,102,173]},
    # Tier 4 (items 18-23)
    {"name": "Soldier Attack 4",        "levels": [21,25,29,35,42,50,60,72,87,103]},
    {"name": "Soldier HP 4",            "levels": [21,25,29,35,42,50,60,72,87,103]},
    {"name": "Damage on Counter 4",     "levels": [54,70,97,145,231]},
    {"name": "Hero Attack 4",           "levels": [30,36,42,50,59,71,86,103,124,147]},
    {"name": "Hero HP 4",               "levels": [30,36,42,50,59,71,86,103,124,147]},
    {"name": "Dmg Reduction Counter 4", "levels": [81,110,154,217,346]},
]

AWK_R = [
    # Tier 1 (items 0-5)
    {"name": "Soldier Assault 1",  "levels": [5,6,8,12,18]},
    {"name": "Soldier Defense 1",  "levels": [5,6,8,12,18]},
    {"name": "TG Capacity 1",      "levels": [5,6,7,8,9,11,13,16,19]},
    {"name": "Attack Link 1",      "levels": [6,7,8,10,11,13,16,19,23]},
    {"name": "HP Link 1",          "levels": [6,7,8,10,11,13,16,19,23]},
    {"name": "Defense Spec 1",     "levels": [7,8,10,11]},
    # Tier 2 (items 6-11)
    {"name": "Soldier Assault 2",  "levels": [9,11,15,23,35]},
    {"name": "Soldier Defense 2",  "levels": [9,11,15,23,35]},
    {"name": "TG Capacity 2",      "levels": [9,11,13,16,18,22,26,32,38,45]},
    {"name": "Attack Link 2",      "levels": [11,13,16,19,22,26,32,38,46]},
    {"name": "HP Link 2",          "levels": [11,13,16,19,22,26,32,38,46]},
    {"name": "Attack Spec 1",      "levels": [13,16,18,22,26,31,37,44,53]},
    # Tier 3 (items 12-17)
    {"name": "Soldier Assault 3",  "levels": [15,18,21,25,29,35,42,51,61]},
    {"name": "Soldier Defense 3",  "levels": [15,18,21,25,29,35,42,51,61]},
    {"name": "March Size 1",       "levels": [18,22,26,31,36,43,52,63,76]},
    {"name": "Attack Link 3",      "levels": [20,24,28,34,40,48,58,69,83,99]},
    {"name": "HP Link 3",          "levels": [20,24,28,34,40,48,58,69,83,99]},
    {"name": "Defense Spec 2",     "levels": [22,26,31,37,43,52,63,76,91,108]},
    # Tier 4 (items 18-23)
    {"name": "Soldier Assault 4",  "levels": [26,31,36,43,51,61,73,88,106,126]},
    {"name": "Soldier Defense 4",  "levels": [26,31,36,43,51,61,73,88,106,126]},
    {"name": "March Size 2",       "levels": [29,35,41,49,58,69,83,101,121,144]},
    {"name": "Attack Link 4",      "levels": [36,43,51,61,72,86,104,126,151,179]},
    {"name": "HP Link 4",          "levels": [36,43,51,61,72,86,104,126,151,179]},
    {"name": "Attack Spec 2",      "levels": [43,52,61,73,86,103,125,151,181,215]},
]

S2_R = [
    {"name": "League Hero Level",     "name_pt": "Nível de Herói de Liga",      "levels": [13]},
    {"name": "Horde Hero Level",      "name_pt": "Nível de Herói de Horda",     "levels": [13]},
    {"name": "Nature Hero Level",     "name_pt": "Nível de Herói de Natureza",  "levels": [13]},
    {"name": "Full League March (A)", "name_pt": "Marcha Completa de Liga (A)", "levels": [10,None,None,None,None,23,28]},
    {"name": "Full Horde March (A)",  "name_pt": "Marcha Completa de Horda (A)","levels": [10,None,None,None,None,23,28]},
    {"name": "Full Nature March (A)", "name_pt": "Marcha Completa de Natureza (A)","levels": [10,None,None,None,None,23,28]},
    {"name": "Full League March (B)", "name_pt": "Marcha Completa de Liga (B)", "levels": [14,None,None,None,None,None,None,None,58]},
    {"name": "Full Horde March (B)",  "name_pt": "Marcha Completa de Horda (B)","levels": [14,None,None,None,None,None,None,None,58]},
    {"name": "Full Nature March (B)", "name_pt": "Marcha Completa de Natureza (B)","levels": [14,None,None,None,None,None,None,None,58]},
    {"name": "Full Horde March (C)",  "name_pt": "Marcha Completa de Horda (C)","levels": [18,21,25,30,35,42,50,61,73,86]},
    {"name": "Full Nature March (C)", "name_pt": "Marcha Completa de Natureza (C)","levels": [18,21,25,30,35,42,50,61,73,86]},
    {"name": "Faction March Size",    "name_pt": "Tamanho de Marcha de Facção", "levels": [18,21,25,30,35,42,50,61,73,86]},
]

S3_R = [
    {"name": "Full League March (A)", "name_pt": "Marcha Completa de Liga (A)", "levels": [15,19,27,40,63]},
    {"name": "Full Horde March (A)",  "name_pt": "Marcha Completa de Horda (A)","levels": [15,19,27,40,63]},
    {"name": "Full Nature March (A)", "name_pt": "Marcha Completa de Natureza (A)","levels": [15,19,27,40,63]},
    {"name": "Fort Contest Queue",    "name_pt": "Fila de Contestação de Forte","levels": [38]},
    {"name": "Full League March (B)", "name_pt": "Marcha Completa de Liga (B)", "levels": [11,14,16,19,22,27,32,38,46,55]},
    {"name": "Full Horde March (B)",  "name_pt": "Marcha Completa de Horda (B)","levels": [11,14,16,19,22,27,32,38,46,55]},
    {"name": "Full Nature March (B)", "name_pt": "Marcha Completa de Natureza (B)","levels": [11,14,16,19,22,27,32,38,46,55]},
    {"name": "League Hero Level",     "name_pt": "Nível de Herói de Liga",      "levels": [36,47,65,97,155]},
    {"name": "Horde Hero Level",      "name_pt": "Nível de Herói de Horda",     "levels": [36,47,65,97,155]},
    {"name": "Nature Hero Level",     "name_pt": "Nível de Herói de Natureza",  "levels": [36,47,65,97,155]},
    {"name": "Full Horde March (C)",  "name_pt": "Marcha Completa de Horda (C)","levels": [20,24,28,34,40,48,58,69,83,98]},
    {"name": "Full Nature March (C)", "name_pt": "Marcha Completa de Natureza (C)","levels": [20,24,28,34,40,48,58,69,83,98]},
    {"name": "Faction March Size",    "name_pt": "Tamanho de Marcha de Facção", "levels": [20,24,28,34,40,48,58,69,83,98]},
]

BI2_R = [
    # Unlocks when BI1 reaches 70% completion (≈ 21 000 Dust)
    # Required for T12 troops. Total: 23 711 Dust (all factions × 1).
    {"name": "March Size 1",     "levels": [50, 55, 61, 66, 75]},
    {"name": "Soldier Attack 1", "levels": [40, 44, 49, 54, 60, 66, 73, 81, 90, 99]},
    {"name": "Soldier HP 1",     "levels": [40, 44, 49, 54, 60, 66, 73, 81, 90, 99]},
    {"name": "Hero Level Cap 1", "levels": [150]},
    {"name": "Hero Attack 1",    "levels": [60, 66, 73, 81, 90, 99, 109, 120, 132, 145]},
    {"name": "Hero HP 1",        "levels": [60, 66, 73, 81, 90, 99, 109, 120, 132, 145]},
    {"name": "March Size 2",     "levels": [125, 138, 152, 168, 185]},
    {"name": "Soldier Attack 2", "levels": [75, 83, 92, 102, 113, 125, 138, 152, 168, 186]},
    {"name": "Soldier HP 2",     "levels": [75, 83, 92, 102, 113, 125, 138, 152, 168, 186]},
    {"name": "Hero Level Cap 2", "levels": [250]},
    {"name": "Hero Attack 2",    "levels": [100, 110, 121, 134, 148, 163, 180, 198, 218, 240]},
    {"name": "Hero HP 2",        "levels": [100, 110, 121, 134, 148, 163, 180, 198, 218, 240]},
    {"name": "March Size 3",     "levels": [225, 248, 273, 301, 332]},
    {"name": "Gear Attack 1",    "levels": [150, 165, 182, 201, 222, 245, 270, 297, 327]},
    {"name": "Gear HP 1",        "levels": [150, 165, 182, 201, 222, 245, 270, 297, 327]},
    {"name": "March Size 4",     "levels": [375, None, 455, 501, 552]},
    {"name": "Gear Attack 2",    "levels": [175, 193, 213, 235, 259, 285, 314, 346, 381]},
    {"name": "Gear HP 2",        "levels": [175, 193, 213, 235, 259, 285, 314, 346, 381]},
    {"name": "Troop Level",      "levels": [800]},
    {"name": "Anti-Counter 1",   "levels": [300]},
]

S4_R = [
    {"name": "Full League March (A)", "name_pt": "Marcha Completa de Liga (A)", "levels": [20,22,25,28,31,35,39,43,48,53]},
    {"name": "Full Horde March (A)",  "name_pt": "Marcha Completa de Horda (A)","levels": [20,22,25,28,31,35,39,43,48,53]},
    {"name": "Full Nature March (A)", "name_pt": "Marcha Completa de Natureza (A)","levels": [20,22,25,28,31,35,39,43,48,53]},
    {"name": "League Hero Level",     "name_pt": "Nível de Herói de Liga",      "levels": [40,44,49,54,60]},
    {"name": "Horde Hero Level",      "name_pt": "Nível de Herói de Horda",     "levels": [40,44,49,54,60]},
    {"name": "Nature Hero Level",     "name_pt": "Nível de Herói de Natureza",  "levels": [40,44,49,54,60]},
    {"name": "Full Horde March (B)",  "name_pt": "Marcha Completa de Horda (B)","levels": [50]},
    {"name": "Full Nature March (B)", "name_pt": "Marcha Completa de Natureza (B)","levels": [50]},
    {"name": "Faction March Size",    "name_pt": "Tamanho de Marcha de Facção", "levels": [50]},
]

# Convenience groupings
FACTION_RESEARCH = {"BI": BI_R, "BI2": BI2_R, "Faccao": FAC_R, "Awakening": AWK_R}
SHARED_RESEARCH  = {"S2": S2_R, "S3": S3_R, "S4": S4_R}

# Tier slices for Faction and Awakening (6 items each)
RESEARCH_TIER_SLICES = [
    (slice(0,  6),  "Tier 1"),
    (slice(6,  12), "Tier 2"),
    (slice(12, 18), "Tier 3"),
    (slice(18, 24), "Tier 4"),
]


def research_max_levels(levels: list) -> int:
    """Number of levels with known dust cost (non-None entries)."""
    return len([x for x in levels if x is not None])


def research_cost(levels: list, from_lv: int, to_lv: int) -> int:
    """Dust cost to go from level from_lv to to_lv."""
    valid = [x for x in levels if x is not None]
    return sum(valid[i] for i in range(from_lv, min(to_lv, len(valid))))


def castle_prereq_chain(
    target_b: int,
    current_castle_b: int,
    current_levels: dict,
    brk_any_choice: str = "brk_l",
) -> list:
    """
    Returns a list of prerequisite items needed to reach Castle target_b.

    Each item is a dict:
      building_id, label_en, label_pt, required_b, current_b,
      needs_upgrade, de_cost, is_regular_level (bool)
    """
    # Accumulate the highest required B per building across all unlocked B levels
    needed: dict[str, int] = {}
    for b_level in range(current_castle_b + 1, target_b + 1):
        for (bid, req_b) in CASTLE_PREREQS.get(b_level, []):
            actual = brk_any_choice if bid == "brk_any" else bid
            needed[actual] = max(needed.get(actual, 0), req_b)

    result = []
    for bid, req_b in needed.items():
        if bid in ("rc_lv40", "hosp_lv40"):
            result.append({
                "building_id":    bid,
                "label_en":       PREREQ_LABELS[bid]["en"],
                "label_pt":       PREREQ_LABELS[bid]["pt"],
                "required_b":     req_b,
                "current_b":      None,
                "needs_upgrade":  True,
                "de_cost":        0,
                "is_regular_level": True,
            })
        else:
            curr = current_levels.get(bid, 0)
            cost = de_cost(bid, curr, req_b) if req_b > curr else 0
            bdata = BUILDINGS.get(bid, {})
            result.append({
                "building_id":    bid,
                "label_en":       bdata.get("en", bid),
                "label_pt":       bdata.get("pt", bid),
                "required_b":     req_b,
                "current_b":      curr,
                "needs_upgrade":  req_b > curr,
                "de_cost":        cost,
                "is_regular_level": False,
            })
    return result


def compute_castle_total(
    target_b: int,
    current_castle_b: int,
    current_levels: dict,
    brk_any_choice: str = "brk_l",
) -> dict:
    """Full DE breakdown: Castle itself + all prerequisites."""
    castle_de = de_cost("castle", current_castle_b, target_b)
    prereqs    = castle_prereq_chain(target_b, current_castle_b, current_levels, brk_any_choice)
    prereq_de  = sum(p["de_cost"] for p in prereqs)
    return {
        "castle_de":  castle_de,
        "prereqs":    prereqs,
        "prereq_de":  prereq_de,
        "total_de":   castle_de + prereq_de,
    }
