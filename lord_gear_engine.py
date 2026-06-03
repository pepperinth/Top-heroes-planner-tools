"""
lord_gear_engine.py
===================
Data and calculation engine for the Lord Gear calculator.
No Streamlit dependency — safe to import anywhere.

Sources: TopHeroes Tables spreadsheet, Gear sheet (columns P-T for gear, W-Y for Sacred Codex).
"""

# ══════════════════════════════════════════════════════════════════════════════
# RESOURCE IMAGES
# Extracted from Gear sheet header row (row 3, cols Q-T) and col V row 2.
# ══════════════════════════════════════════════════════════════════════════════

GEAR_IMG_DIR = "lord_gear_imgs"
_RESOURCE_H  = 22   # fixed display height for resource icons

RESOURCE_IMAGES: dict[str, str] = {
    "rm":  "image237.png",   # Refined Metal   (col Q)
    "mt":  "image230.png",   # Magic Thread    (col R)
    "ori": "image292.png",   # Orichalcum      (col S)
    "db":  "image281.png",   # Dragon Blood    (col T)
}
CODEX_IMG = "image220.png"   # Sacred Codex icon (col V row 2)


def show_resource_image(key: str, base_dir: str, st_module) -> None:
    """Display a resource icon at fixed height. key in {'rm','mt','ori','db'}."""
    import os
    from PIL import Image
    img_name = RESOURCE_IMAGES.get(key)
    if not img_name:
        return
    path = os.path.join(base_dir, GEAR_IMG_DIR, img_name)
    img  = Image.open(path)
    ratio = _RESOURCE_H / img.height
    w    = max(1, int(img.width * ratio))
    img  = img.resize((w, _RESOURCE_H), Image.LANCZOS)
    st_module.image(img, width=w)


def show_codex_image(base_dir: str, st_module, height: int = 48) -> None:
    """Display the Sacred Codex icon."""
    import os
    from PIL import Image
    path = os.path.join(base_dir, GEAR_IMG_DIR, CODEX_IMG)
    img  = Image.open(path)
    ratio = height / img.height
    w    = max(1, int(img.width * ratio))
    img  = img.resize((w, height), Image.LANCZOS)
    st_module.image(img, width=w)


# ══════════════════════════════════════════════════════════════════════════════
# RAW PER-ROW COSTS
# Each spreadsheet row is one upgrade step.
# Format: row_number → (refined_metal, magic_thread, orichalcum, dragon_blood)
# ══════════════════════════════════════════════════════════════════════════════

_ROW_COSTS: dict[int, tuple] = {
    4:   (1500,  20,  0,  0),
    5:   (3800,  40,  0,  0),
    6:   (4000,  50,  0,  0),
    7:   (6400,  60,  0,  0),
    8:   (1300,   5, 10,  0),
    9:   (1500,   5, 10,  0),
    10:  (1300,   5, 10,  0),
    11:  (1500,   5, 10,  0),
    12:  (1800,   5, 12,  0),
    13:  (1300,   5, 12,  0),
    14:  (1300,   5, 12,  0),
    15:  (1300,   5, 12,  0),
    16:  (2500,  20, 12,  0),
    17:  (2500,  20, 12,  0),
    18:  (2500,  20, 12,  0),
    19:  (3500,  30, 12,  0),
    20:  (3500,  30, 12,  0),
    21:  (3500,  30, 12,  0),
    22:  (3300,  30, 15,  0),
    23:  (3900,  30, 15,  0),
    24:  (3900,  30, 15,  0),
    25:  (4400,  30, 15,  0),
    26:  (4400,  30, 15,  0),
    27:  (4900,  35, 15,  0),
    28:  (4900,  35, 15,  0),
    29:  (4900,  35, 15,  0),
    30:  (4900,  35, 15,  0),
    31:  (5400,  45, 20,  0),
    32:  (5400,  45, 20,  0),
    33:  (5400,  45, 20,  0),
    34:  (5400,  45, 20,  0),
    35:  (5400,  45, 20,  0),
    36:  (7300,  75, 20,  0),
    37:  (7300,  75, 20,  0),
    38:  (7300,  75, 20,  0),
    39:  (7300,  75, 20,  0),
    40:  (7800,  75, 20,  0),
    41:  (7800,  75, 20,  0),
    42:  (7800,  75, 20,  0),
    43:  (7800,  75, 20,  0),
    44:  (8100,  85, 20,  0),
    45:  (8100,  85, 20,  0),
    46:  (8100,  85, 20,  0),
    47:  (8100,  85, 20,  0),
    48:  (8500,  85, 20,  0),
    49:  (9000,  95, 20,  0),
    50:  (9000,  95, 20,  0),
    51:  (9000,  95, 20,  0),
    52:  (9000,  95, 20,  0),
    53:  (9500,  95, 20,  0),
    54:  (9500,  95, 20,  0),
    55:  (9500,  95, 20,  0),
    56:  (9500,  95, 20,  0),
    57:  (10000, 95, 20,  0),
    58:  (10000, 95, 20,  0),
    59:  (10000, 95, 20,  0),
    60:  (10000, 95, 20,  0),
    61:  (10000, 90, 20,  0),
    62:  (13000, 130, 22, 0),
    63:  (13000, 130, 22, 0),
    64:  (13000, 130, 22, 0),
    65:  (13000, 130, 22, 0),
    66:  (13000, 140, 23, 0),
    67:  (13000, 140, 23, 0),
    68:  (13000, 140, 23, 0),
    69:  (13000, 140, 23, 0),
    70:  (14000, 150, 25, 0),
    71:  (14000, 150, 25, 0),
    72:  (14000, 150, 25, 0),
    73:  (14000, 150, 25, 0),
    74:  (15000, 140, 20, 2),
    75:  (15000, 140, 20, 2),
    76:  (13000, 140, 20, 2),
    77:  (13000, 140, 20, 2),
    78:  (13000, 140, 20, 2),
    79:  (13000, 140, 20, 2),
    80:  (13500, 160, 25, 2),
    81:  (13500, 160, 25, 2),
    82:  (13500, 160, 25, 2),
    83:  (13500, 160, 25, 2),
    84:  (13500, 160, 25, 2),
    85:  (14000, 160, 25, 4),
    86:  (14000, 160, 25, 4),
    87:  (14000, 160, 25, 4),
    88:  (14000, 160, 25, 4),
    89:  (14000, 160, 25, 4),
    90:  (15000, 180, 25, 4),
    91:  (14000, 160, 28, 3),
    92:  (14000, 160, 28, 3),
    93:  (14000, 160, 28, 3),
    94:  (14000, 160, 28, 3),
    95:  (14000, 160, 28, 3),
    96:  (15000, 170, 30, 4),
    97:  (15000, 170, 30, 4),
    98:  (15000, 170, 30, 4),
    99:  (15000, 170, 30, 4),
    100: (15000, 170, 30, 4),
    101: (16500, 175, 30, 4),
    102: (16500, 175, 30, 4),
    103: (16500, 175, 30, 4),
    104: (16500, 175, 30, 4),
    105: (16500, 175, 30, 4),
}

# ══════════════════════════════════════════════════════════════════════════════
# GEAR MILESTONES
# Ordered list of quality milestone levels.
# Each entry: (index, name_pt, name_en, row_number, tier_key)
# 'row_number' = spreadsheet row where this milestone is achieved.
# Cost from milestone A → B = sum of _ROW_COSTS[A.row+1 … B.row].
# ══════════════════════════════════════════════════════════════════════════════

GEAR_MILESTONES: list[tuple] = [
    # idx  name_pt              name_en               row  tier
    (0,  "Início",            "Start",               3,   "start"),
    # ── Comum ──────────────────────────────────────────────────────────────────
    (1,  "Comum BASE",        "Common BASE",          4,   "comum"),
    (2,  "Comum ⭐",           "Common ⭐",             5,   "comum"),
    # ── Raro ───────────────────────────────────────────────────────────────────
    (3,  "Raro BASE",         "Rare BASE",             6,   "raro"),
    (4,  "Raro ⭐",            "Rare ⭐",               7,   "raro"),
    (5,  "Raro ⭐⭐",           "Rare ⭐⭐",              9,   "raro"),
    (6,  "Raro ⭐⭐⭐",          "Rare ⭐⭐⭐",             11,  "raro"),
    # ── Épico ──────────────────────────────────────────────────────────────────
    (7,  "Épico BASE",        "Epic BASE",            13,  "epico"),
    (8,  "Épico ⭐",           "Epic ⭐",              14,  "epico"),
    (9,  "Épico ⭐⭐",          "Epic ⭐⭐",             17,  "epico"),
    (10, "Épico ⭐⭐⭐",         "Epic ⭐⭐⭐",            20,  "epico"),
    # ── Lendário ───────────────────────────────────────────────────────────────
    (11, "Lend. T1",          "Leg. T1",              23,  "lendario"),
    (12, "Lend. T1 ⭐",        "Leg. T1 ⭐",           24,  "lendario"),
    (13, "Lend. T1 ⭐⭐",       "Leg. T1 ⭐⭐",          28,  "lendario"),
    (14, "Lend. T1 ⭐⭐⭐",      "Leg. T1 ⭐⭐⭐",         32,  "lendario"),
    (15, "Lend. T2",          "Leg. T2",              36,  "lendario"),
    (16, "Lend. T2 ⭐",        "Leg. T2 ⭐",           37,  "lendario"),
    (17, "Lend. T2 ⭐⭐",       "Leg. T2 ⭐⭐",          41,  "lendario"),
    (18, "Lend. T2 ⭐⭐⭐",      "Leg. T2 ⭐⭐⭐",         45,  "lendario"),
    (19, "Lend. T3",          "Leg. T3",              49,  "lendario"),
    (20, "Lend. T3 ⭐",        "Leg. T3 ⭐",           50,  "lendario"),
    (21, "Lend. T3 ⭐⭐",       "Leg. T3 ⭐⭐",          54,  "lendario"),
    (22, "Lend. T3 ⭐⭐⭐",      "Leg. T3 ⭐⭐⭐",         58,  "lendario"),
    (23, "Lend. T4",          "Leg. T4",              62,  "lendario"),
    (24, "Lend. T4 ⭐",        "Leg. T4 ⭐",           63,  "lendario"),
    (25, "Lend. T4 ⭐⭐",       "Leg. T4 ⭐⭐",          67,  "lendario"),
    (26, "Lend. T4 ⭐⭐⭐",      "Leg. T4 ⭐⭐⭐",         71,  "lendario"),
    # ── Mítico ─────────────────────────────────────────────────────────────────
    (27, "Mítico",            "Mythic",               75,  "mitico"),
    (28, "Mítico ⭐",          "Mythic ⭐",             76,  "mitico"),
    (29, "Mítico ⭐⭐",         "Mythic ⭐⭐",            81,  "mitico"),
    (30, "Mítico ⭐⭐⭐",        "Mythic ⭐⭐⭐",           86,  "mitico"),
    (31, "Mítico T1",         "Mythic T1",            91,  "mitico"),
    (32, "Mítico T1 ⭐",       "Mythic T1 ⭐",         92,  "mitico"),
    (33, "Mítico T1 ⭐⭐",      "Mythic T1 ⭐⭐",        97,  "mitico"),
    (34, "Mítico T1 ⭐⭐⭐",     "Mythic T1 ⭐⭐⭐",       102, "mitico"),
]

MAX_GEAR_LEVEL = len(GEAR_MILESTONES) - 1  # 34 (index 0 = "Início")

# Colored-circle prefixes for dropdowns (Streamlit doesn't support styled options)
TIER_BADGE: dict[str, str] = {
    "start":    "⬜",
    "comum":    "🟢",
    "raro":     "🔵",
    "epico":    "🟣",
    "lendario": "🟡",
    "mitico":   "🔴",
}

# Tier display colors for metrics/captions (hex)
TIER_COLOR: dict[str, str] = {
    "start":    "#888888",
    "comum":    "#2E7D32",
    "raro":     "#1565C0",
    "epico":    "#6A1B9A",
    "lendario": "#E65100",
    "mitico":   "#B71C1C",
}

def _milestone_names(lang: str = "pt") -> list[str]:
    return [
        f"{TIER_BADGE[tier]} {name_pt if lang == 'pt' else name_en}"
        for _, name_pt, name_en, _, tier in GEAR_MILESTONES
    ]

GEAR_LEVEL_OPTS_PT = _milestone_names("pt")
GEAR_LEVEL_OPTS_EN = _milestone_names("en")


# ══════════════════════════════════════════════════════════════════════════════
# LORD GEAR PIECES
# 6 pieces total: 2 per faction (Attack + HP). All share the same cost table.
# Resources are universal — NOT faction-specific.
# ══════════════════════════════════════════════════════════════════════════════

GEAR_PIECES: list[dict] = [
    {"id": "horda_atk",    "name_pt": "Horda — Ataque",    "name_en": "Horde — Attack",   "faction": "Horda",    "faction_en": "Horde",  "type_pt": "Ataque", "type_en": "Attack"},
    {"id": "horda_hp",     "name_pt": "Horda — HP",         "name_en": "Horde — HP",       "faction": "Horda",    "faction_en": "Horde",  "type_pt": "HP",     "type_en": "HP"},
    {"id": "liga_atk",     "name_pt": "Liga — Ataque",     "name_en": "League — Attack",  "faction": "Liga",     "faction_en": "League", "type_pt": "Ataque", "type_en": "Attack"},
    {"id": "liga_hp",      "name_pt": "Liga — HP",          "name_en": "League — HP",      "faction": "Liga",     "faction_en": "League", "type_pt": "HP",     "type_en": "HP"},
    {"id": "natureza_atk", "name_pt": "Natureza — Ataque", "name_en": "Nature — Attack",  "faction": "Natureza", "faction_en": "Nature", "type_pt": "Ataque", "type_en": "Attack"},
    {"id": "natureza_hp",  "name_pt": "Natureza — HP",      "name_en": "Nature — HP",      "faction": "Natureza", "faction_en": "Nature", "type_pt": "HP",     "type_en": "HP"},
]

GEAR_PIECE_NAMES_PT = [g["name_pt"] for g in GEAR_PIECES]
GEAR_PIECE_NAMES_EN = [g["name_en"] for g in GEAR_PIECES]

def get_gear_piece(name_pt: str) -> dict:
    return next(g for g in GEAR_PIECES if g["name_pt"] == name_pt)


# ══════════════════════════════════════════════════════════════════════════════
# SACRED CODEX DATA
# 17 star upgrade steps. Resources: Magic Thread + Orichalcum + Dragon Blood.
# No Refined Metal (Sacred Codex is universal, one piece only).
# Each entry: (star_number, magic_thread, orichalcum, dragon_blood)
# ══════════════════════════════════════════════════════════════════════════════

CODEX_STAR_COSTS: list[tuple] = [
    (1,  200,  50,  0),
    (2,  200,  50,  0),
    (3,  200,  50,  0),
    (4,  300, 100,  0),
    (5,  300, 100,  0),
    (6,  450, 150,  0),
    (7,  450, 150,  0),
    (8,  450, 150,  0),
    (9,  450, 150,  0),
    (10, 450, 150,  0),
    (11, 600, 200,  0),
    (12, 600, 200,  0),
    (13, 600, 200,  0),
    (14, 600, 200,  0),
    (15, 600, 200,  0),
    (16,   0, 300, 10),
    (17,   0, 400, 30),
]

MAX_CODEX_STARS = len(CODEX_STAR_COSTS)  # 17


# ══════════════════════════════════════════════════════════════════════════════
# CALCULATION FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def calc_gear_resources(from_level: int, to_level: int) -> dict:
    """
    Resources to upgrade lord gear from milestone index `from_level` to `to_level`.
    Returns {"rm", "mt", "ori", "db"}.
    """
    if to_level <= from_level:
        return {"rm": 0, "mt": 0, "ori": 0, "db": 0}

    row_start = GEAR_MILESTONES[from_level][3] + 1  # row after "from" milestone
    row_end   = GEAR_MILESTONES[to_level][3]         # row of "to" milestone

    rm = mt = ori = db = 0
    for row in range(row_start, row_end + 1):
        c = _ROW_COSTS.get(row, (0, 0, 0, 0))
        rm  += c[0]; mt  += c[1]; ori += c[2]; db  += c[3]

    return {"rm": rm, "mt": mt, "ori": ori, "db": db}


def calc_codex_resources(from_star: int, to_star: int) -> dict:
    """
    Resources to upgrade Sacred Codex from `from_star` to `to_star` stars.
    Returns {"mt", "ori", "db"}. (No Refined Metal for Codex.)
    """
    if to_star <= from_star:
        return {"mt": 0, "ori": 0, "db": 0}

    mt = ori = db = 0
    for i in range(from_star, to_star):
        e = CODEX_STAR_COSTS[i]   # index i = cost to reach star i+1
        mt += e[1]; ori += e[2]; db += e[3]

    return {"mt": mt, "ori": ori, "db": db}


def calc_combined(from_gear: int, to_gear: int, from_codex: int, to_codex: int) -> dict:
    """Combined resources for gear + codex upgrades in one pass."""
    g = calc_gear_resources(from_gear, to_gear)
    c = calc_codex_resources(from_codex, to_codex)
    return {
        "rm":  g["rm"],
        "mt":  g["mt"]  + c["mt"],
        "ori": g["ori"] + c["ori"],
        "db":  g["db"]  + c["db"],
    }


# ══════════════════════════════════════════════════════════════════════════════
# EVENT MULTIPLIERS  (Lord Gear Trial — events_data.py tasks 0-3)
# Task 0: Use 100 Refined Metal   → ×0.1 pts/unit
# Task 1: Use 1 Magic Thread      → ×10  pts/unit
# Task 2: Use 1 Orichalcum        → ×15  pts/unit
# Task 3: Consume 1 Dragon Blood  → ×60  pts/unit
# ══════════════════════════════════════════════════════════════════════════════

def calc_event_pts(rm: int, mt: int, ori: int, db: int) -> dict:
    """Returns Lord Gear Trial point breakdown."""
    pts_rm  = rm  * 0.1
    pts_mt  = mt  * 10
    pts_ori = ori * 15
    pts_db  = db  * 60
    return {
        "rm":    pts_rm,
        "mt":    pts_mt,
        "ori":   pts_ori,
        "db":    pts_db,
        "total": pts_rm + pts_mt + pts_ori + pts_db,
    }
