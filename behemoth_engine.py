from __future__ import annotations
"""
behemoth_engine.py
==================
Data and calculation engine for the Behemoth calculator.
No Streamlit dependency — safe to import anywhere.

Sources: TopHeroes Tables spreadsheet, Behemoth sheet.
"""

# ══════════════════════════════════════════════════════════════════════════════
# LEVEL DATA
# Magicite cost to reach each level (i.e. cost of the upgrade TO that level).
# Level 1 costs nothing (starting point).
# Magic Core is required at milestone levels only.
# ══════════════════════════════════════════════════════════════════════════════

MAGICITE_PER_LEVEL: dict[int, int] = {
    1: 0,
    2: 480,
    3: 720,
    4: 960,
    5: 1200,
    6: 1440,
    7: 1680,
    8: 1920,
    9: 2160,
    10: 2400,
    11: 2640,
    12: 3000,
    13: 3360,
    14: 3720,
    15: 4080,
    16: 4440,
    17: 4800,
    18: 5160,
    19: 5520,
    20: 5880,
    21: 6240,
    22: 6720,
    23: 7200,
    24: 7680,
    25: 8160,
    26: 8640,
    27: 9120,
    28: 9600,
    29: 10080,
    30: 10560,
    31: 11040,
    32: 11640,
    33: 12240,
    34: 12840,
    35: 13440,
    36: 14040,
    37: 14640,
    38: 15240,
    39: 15840,
    40: 16440,
    41: 17040,
    42: 17760,
    43: 18480,
    44: 19200,
    45: 19920,
    46: 20640,
    47: 21360,
    48: 22080,
    49: 22800,
    50: 23500,
    51: 24240,
    52: 25080,
    53: 25920,
    54: 26760,
    55: 27600,
    56: 28440,
    57: 29280,
    58: 30120,
    59: 30960,
    60: 31800,
    61: 32640,
    62: 33600,
    63: 34560,
    64: 35520,
    65: 36480,
    66: 37440,
    67: 38400,
    68: 39360,
    69: 40320,
    70: 41280,
    71: 42240,
    72: 43200,
    73: 44100,
    74: 45120,
    75: 46080,
    76: 47040,
    77: 48000,
    78: 48960,
    79: 49920,
    80: 50880,
    81: 51840,
    82: 52800,
    83: 53760,
    84: 54720,
    85: 55680,
    86: 56640,
    87: 57600,
    88: 58560,
    89: 59520,
    90: 60480,
    91: 61440,
    92: 62400,
    93: 63360,
    94: 64320,
    95: 65280,
    96: 66240,
    97: 67200,
    98: 68160,
    99: 69120,
    100: 70080,
    101: 71040,
    102: 72000,
    103: 72960,
    104: 73920,
    105: 74880,
    106: 75480,
    107: 76800,
    108: 77760,
    109: 78720,
    110: 79680,
    111: 80640,
    112: 81600,
    113: 82560,
    114: 83520,
    115: 84480,
    116: 85440,
    117: 86400,
    118: 87360,
    119: 88320,
    120: 89280,
    121: 90560,
}

# Magic Core required at milestone levels (cost to pass through that level).
MAGIC_CORE_AT_LEVEL: dict[int, int] = {
    20:  1500,
    30:  3100,
    40:  3700,
    50:  4300,
    60:  4900,
    70:  5500,
    80:  6200,
    90:  6800,
    100: 7400,
    110: 8000,
    120: 8600,
}

MAX_LEVEL = 121

# ══════════════════════════════════════════════════════════════════════════════
# STAR DATA
# STAR_SEAL_COSTS[i] = covenant seals needed to unlock star (i+1).
# Index 0 → Star 1 costs 6 seals; index 49 → Star 50 costs 220 seals.
# ══════════════════════════════════════════════════════════════════════════════

STAR_SEAL_COSTS: list[int] = [
    6, 8, 10, 12, 14,          # stars 1–5
    18, 20, 24, 28, 34,        # stars 6–10
    40, 46, 52, 58, 64,        # stars 11–15
    70, 76, 82, 88, 94,        # stars 16–20
    100, 106, 112, 118, 120,   # stars 21–25
    124, 128, 132, 136, 140,   # stars 26–30
    144, 148, 152, 156, 160,   # stars 31–35
    164, 168, 172, 176, 180,   # stars 36–40
    184, 188, 192, 196, 200,   # stars 41–45
    204, 208, 212, 216, 220,   # stars 46–50
]

# ══════════════════════════════════════════════════════════════════════════════
# STAR DISPLAY IMAGES
# Each entry maps a star count (0–50) to the sprite filename that shows the
# cumulative visual state: how many "legs" of each visual star are filled.
# Each visual star has 5 legs → 5 seal purchases per visual star.
# Tiers: gold (stars 1-25), red (stars 26-50).
# Images extracted from TopHeroes Tables spreadsheet, Behemoth sheet col 12.
# ══════════════════════════════════════════════════════════════════════════════

STAR_IMAGES: list[str] = [
    "image305.png",   #  0 — empty (no stars)
    # ── Gold tier ─────────────────────────────────────────────────────────────
    "image575.png",   #  1 — gold ★1 leg 1/5
    "image492.png",   #  2 — gold ★1 leg 2/5
    "image482.png",   #  3 — gold ★1 leg 3/5
    "image532.png",   #  4 — gold ★1 leg 4/5
    "image485.png",   #  5 — gold ★1 complete
    "image487.png",   #  6 — gold ★2 leg 1/5
    "image483.png",   #  7 — gold ★2 leg 2/5
    "image484.png",   #  8 — gold ★2 leg 3/5
    "image503.png",   #  9 — gold ★2 leg 4/5
    "image530.png",   # 10 — gold ★2 complete
    "image526.png",   # 11 — gold ★3 leg 1/5
    "image569.png",   # 12 — gold ★3 leg 2/5
    "image524.png",   # 13 — gold ★3 leg 3/5
    "image574.png",   # 14 — gold ★3 leg 4/5
    "image486.png",   # 15 — gold ★3 complete
    "image542.png",   # 16 — gold ★4 leg 1/5
    "image489.png",   # 17 — gold ★4 leg 2/5
    "image568.png",   # 18 — gold ★4 leg 3/5
    "image508.png",   # 19 — gold ★4 leg 4/5
    "image506.png",   # 20 — gold ★4 complete
    "image496.png",   # 21 — gold ★5 leg 1/5
    "image567.png",   # 22 — gold ★5 leg 2/5
    "image511.png",   # 23 — gold ★5 leg 3/5
    "image500.png",   # 24 — gold ★5 leg 4/5
    "image493.png",   # 25 — gold ★5 complete (all gold done)
    # ── Red tier ──────────────────────────────────────────────────────────────
    "image522.png",   # 26 — red ★1 leg 1/5
    "image586.png",   # 27 — red ★1 leg 2/5
    "image497.png",   # 28 — red ★1 leg 3/5
    "image510.png",   # 29 — red ★1 leg 4/5
    "image495.png",   # 30 — red ★1 complete
    "image517.png",   # 31 — red ★2 leg 1/5
    "image498.png",   # 32 — red ★2 leg 2/5
    "image520.png",   # 33 — red ★2 leg 3/5
    "image494.png",   # 34 — red ★2 leg 4/5
    "image502.png",   # 35 — red ★2 complete
    "image521.png",   # 36 — red ★3 leg 1/5
    "image501.png",   # 37 — red ★3 leg 2/5
    "image499.png",   # 38 — red ★3 leg 3/5
    "image541.png",   # 39 — red ★3 leg 4/5
    "image519.png",   # 40 — red ★3 complete
    "image594.png",   # 41 — red ★4 leg 1/5
    "image560.png",   # 42 — red ★4 leg 2/5
    "image513.png",   # 43 — red ★4 leg 3/5
    "image536.png",   # 44 — red ★4 leg 4/5
    "image539.png",   # 45 — red ★4 complete
    "image600.png",   # 46 — red ★5 leg 1/5
    "image518.png",   # 47 — red ★5 leg 2/5
    "image528.png",   # 48 — red ★5 leg 3/5
    "image566.png",   # 49 — red ★5 leg 4/5
    "image531.png",   # 50 — red ★5 complete (all red done)
    # ── Platinum tier ─────────────────────────────────────────────────────────
    "image557.png",   # 51 — platinum ★1 leg 1/5
    "image525.png",   # 52 — platinum ★1 leg 2/5
    "image529.png",   # 53 — platinum ★1 leg 3/5
    "image527.png",   # 54 — platinum ★1 leg 4/5
    "image535.png",   # 55 — platinum ★1 complete
    "image538.png",   # 56 — platinum ★2 leg 1/5
    "image587.png",   # 57 — platinum ★2 leg 2/5
    "image534.png",   # 58 — platinum ★2 leg 3/5
    "image537.png",   # 59 — platinum ★2 leg 4/5
    "image565.png",   # 60 — platinum ★2 complete
    "image533.png",   # 61 — platinum ★3 leg 1/5
    "image554.png",   # 62 — platinum ★3 leg 2/5
    "image620.png",   # 63 — platinum ★3 leg 3/5
    "image591.png",   # 64 — platinum ★3 leg 4/5
    "image598.png",   # 65 — platinum ★3 complete
    "image545.png",   # 66 — platinum ★4 leg 1/5
    "image558.png",   # 67 — platinum ★4 leg 2/5
    "image613.png",   # 68 — platinum ★4 leg 3/5
    "image627.png",   # 69 — platinum ★4 leg 4/5
    "image553.png",   # 70 — platinum ★4 complete
    "image551.png",   # 71 — platinum ★5 leg 1/5
    "image543.png",   # 72 — platinum ★5 leg 2/5
    "image548.png",   # 73 — platinum ★5 leg 3/5
    "image547.png",   # 74 — platinum ★5 leg 4/5
    "image549.png",   # 75 — platinum ★5 complete (all platinum done)
    # ── Black tier (complete only — no per-leg images) ───────────────────────
    "image340.png",   # 76 — black ★1 complete
    "image336.png",   # 77 — black ★2 complete
    "image334.png",   # 78 — black ★3 complete
    "image339.png",   # 79 — black ★4 complete
    "image438.png",   # 80 — black ★5 complete
]

MAX_STARS      = 75   # Behemoth progression cap (gold 1-25, red 26-50, platinum 51-75)
MAX_STARS_CALC = len(STAR_SEAL_COSTS)  # 50 — cost data ends at red tier
STAR_IMAGE_DIR = "behemoth_imgs"
_STAR_DISPLAY_H = 48  # fixed display height — each star appears the same individual size


def show_star_image(star_idx: int, base_dir: str, st_module) -> None:
    """Scale by fixed height so every individual star appears the same visual size.
    Width scales proportionally: 1-star is narrow, 5-stars is ~5× wider.
    Explicit width= prevents Streamlit from auto-expanding small images."""
    import os
    from PIL import Image
    path  = os.path.join(base_dir, STAR_IMAGE_DIR, STAR_IMAGES[star_idx])
    img   = Image.open(path)
    ratio = _STAR_DISPLAY_H / img.height
    w     = max(1, int(img.width * ratio))
    img   = img.resize((w, _STAR_DISPLAY_H), Image.LANCZOS)
    st_module.image(img, width=w)

# ══════════════════════════════════════════════════════════════════════════════
# FACTION & BEHEMOTH DATA
# ══════════════════════════════════════════════════════════════════════════════

FACTION_ICON_DIR = "faction_imgs"

# Faction icons extracted from TopHeroes Tables, Troop Skins sheet
FACTION_ICONS: dict[str, str] = {
    "Horda":    "image63.png",  # red fire emblem
    "Liga":     "image79.png",  # blue shield
    "Natureza": "image72.png",  # green leaf
}

BEHEMOTHS: list[dict] = [
    {"name": "Silvermoon Commander", "faction": "Horda",    "faction_en": "Horde"},
    {"name": "Golden Scorpion",       "faction": "Horda",    "faction_en": "Horde"},
    {"name": "Bloodmoon Queen",        "faction": "Liga",     "faction_en": "League"},
    {"name": "Frenzied Blaze Almon",   "faction": "Liga",     "faction_en": "League"},
    {"name": "Inferno Tyrant",         "faction": "Natureza", "faction_en": "Nature"},
    {"name": "Icy Phoenix",            "faction": "Natureza", "faction_en": "Nature"},
]

BEHEMOTH_NAMES: list[str] = [b["name"] for b in BEHEMOTHS]

def get_behemoth(name: str) -> dict:
    return next(b for b in BEHEMOTHS if b["name"] == name)


# ══════════════════════════════════════════════════════════════════════════════
# CALCULATION FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def calc_level_resources(from_lvl: int, to_lvl: int) -> dict:
    """
    Returns resources needed to level from `from_lvl` to `to_lvl`.
    `from_lvl` is the current level (already reached, not charged again).

    Returns:
        {
            "magicite":       int,
            "magic_cores":    int,
            "core_milestones": {lvl: cores},  # only milestones in range
        }
    """
    if to_lvl <= from_lvl:
        return {"magicite": 0, "magic_cores": 0, "core_milestones": {}}

    total_mag = sum(MAGICITE_PER_LEVEL.get(l, 0) for l in range(from_lvl + 1, to_lvl + 1))
    milestones = {
        l: MAGIC_CORE_AT_LEVEL[l]
        for l in range(from_lvl + 1, to_lvl + 1)
        if l in MAGIC_CORE_AT_LEVEL
    }
    total_cores = sum(milestones.values())

    return {
        "magicite":        total_mag,
        "magic_cores":     total_cores,
        "core_milestones": milestones,
    }


def calc_star_resources(from_star: int, to_star: int) -> int:
    """
    Returns total covenant seals to go from `from_star` to `to_star`.
    `from_star` = 0 means no stars yet.
    """
    if to_star <= from_star:
        return 0
    return sum(STAR_SEAL_COSTS[i] for i in range(from_star, to_star))


def calc_total(from_lvl: int, to_lvl: int, from_star: int, to_star: int) -> dict:
    """Combined resource summary for a level + star upgrade."""
    lvl = calc_level_resources(from_lvl, to_lvl)
    seals = calc_star_resources(from_star, to_star)
    return {
        "magicite":        lvl["magicite"],
        "magic_cores":     lvl["magic_cores"],
        "core_milestones": lvl["core_milestones"],
        "seals":           seals,
    }
