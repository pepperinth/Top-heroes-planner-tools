"""
hero_gear_engine.py — Hero Gear & Hero Gear Promotion data and calculation engine.
Data sourced from TopHeroes Tables (1).xlsx — Gear sheet (Hero Gear + Hero Gear Promotion columns).

Gear level : 0 (fresh) → 40 (max)
Promotion  : 0 (none)  → 25 (max, 5 tiers × 5 steps each)
Promotion requires gear at LVL 40.

Resources:
  Leveling  : Enhancement Rune (blue crystal) + Ruby (red crystal)
  Promotion : Enhancement Rune + Gold Bar + Ruby  OR  Legendary/Mythic Stones (5th step of each tier)
"""
from __future__ import annotations

# ── Resource images ───────────────────────────────────────────────────────────
HERO_GEAR_IMG_DIR = "hero_gear_imgs"
_RESOURCE_H = 22

RESOURCE_IMAGES: dict[str, str] = {
    "enh_rune":   "image_r2_c2_1.png",    # Enhancement Rune (blue crystal)
    "ruby":       "image_r2_c3_2.png",    # Ruby (red crystal)
    "gold_bar":   "image_r2_c7_5.png",    # Gold Bar
    "leg_stone":  "image_r2_c9_7.png",    # Legendary Stone (orange)
    "myth_stone": "image_r35_c9_56.png",  # Legendary + Mythic stones (combined icon)
}


def show_resource_image(key: str, base_dir: str, st_module, height: int = 22) -> None:
    import os
    from PIL import Image
    img_name = RESOURCE_IMAGES.get(key)
    if not img_name:
        return
    path = os.path.join(base_dir, HERO_GEAR_IMG_DIR, img_name)
    try:
        img = Image.open(path)
        ratio = height / img.height
        w = max(1, int(img.width * ratio))
        img = img.resize((w, height), Image.LANCZOS)
        st_module.image(img, width=w)
    except Exception:
        pass


# ── Gear sets and pieces ──────────────────────────────────────────────────────
GEAR_SETS = ["Knight", "Blood", "Titan"]

GEAR_SET_NAMES_PT: dict[str, str] = {
    "Knight": "Glória do Cavaleiro",
    "Blood":  "Fúria de Sangue",
    "Titan":  "Poder do Titã",
}
GEAR_SET_NAMES_EN: dict[str, str] = {
    "Knight": "Glory of the Knight",
    "Blood":  "Fury of Blood",
    "Titan":  "Titan's Might",
}
GEAR_SET_COLORS: dict[str, str] = {
    "Knight": "#4a7cc7",
    "Blood":  "#c74a4a",
    "Titan":  "#7a4ac7",
}

GEAR_PIECES_PT = ["Arma", "Bota", "Capacete", "Armadura"]
GEAR_PIECES_EN = ["Weapon", "Boot", "Helmet", "Armor"]
GEAR_PIECE_ICONS = ["⚔️", "👟", "⛑️", "🛡️"]


# ── Hero Gear leveling (LVL 0 → 40) ──────────────────────────────────────────
# Cost to upgrade from LVL (n-1) to LVL n: (enh_rune, ruby)
# Levels grouped in blocks of 4 with identical per-level costs.

MAX_GEAR_LEVEL = 40

_LV_GROUPS = [
    (1,  4,  1500,  7200),
    (5,  8,  2250, 10800),
    (9,  12, 3000, 14400),
    (13, 16, 3750, 18000),
    (17, 20, 4500, 21600),
    (21, 24, 5250, 25200),
    (25, 28, 6000, 28800),
    (29, 32, 6750, 32400),
    (33, 36, 7500, 36000),
    (37, 40, 8250, 39600),
]

GEAR_LV_RUNE: list[int] = [0] * (MAX_GEAR_LEVEL + 1)
GEAR_LV_RUBY: list[int] = [0] * (MAX_GEAR_LEVEL + 1)
for _a, _b, _r, _rb in _LV_GROUPS:
    for _lv in range(_a, _b + 1):
        GEAR_LV_RUNE[_lv] = _r
        GEAR_LV_RUBY[_lv] = _rb

# Cumulative costs from LVL 0
GEAR_LV_CUMUL_RUNE: list[int] = [0] * (MAX_GEAR_LEVEL + 1)
GEAR_LV_CUMUL_RUBY: list[int] = [0] * (MAX_GEAR_LEVEL + 1)
for _lv in range(1, MAX_GEAR_LEVEL + 1):
    GEAR_LV_CUMUL_RUNE[_lv] = GEAR_LV_CUMUL_RUNE[_lv - 1] + GEAR_LV_RUNE[_lv]
    GEAR_LV_CUMUL_RUBY[_lv] = GEAR_LV_CUMUL_RUBY[_lv - 1] + GEAR_LV_RUBY[_lv]


def gear_level_cost(from_lv: int, to_lv: int) -> tuple[int, int]:
    """Returns (enh_rune, ruby) to go from_lv → to_lv."""
    f = max(0, min(from_lv, MAX_GEAR_LEVEL))
    t = max(0, min(to_lv,   MAX_GEAR_LEVEL))
    return (
        max(0, GEAR_LV_CUMUL_RUNE[t] - GEAR_LV_CUMUL_RUNE[f]),
        max(0, GEAR_LV_CUMUL_RUBY[t] - GEAR_LV_CUMUL_RUBY[f]),
    )


# ── Hero Gear Promotion (steps 0 → 25) ───────────────────────────────────────
# 5 tiers × 5 steps each = 25 total.
# Steps 1-4 of each tier: enh_rune + gold_bars + ruby.
# Step  5 of each tier: enh_rune + gold_bars + stones (no ruby).
# Promotion star display: step P → platinum star index = 50 + P (uses behemoth_imgs).

MAX_PROMOTION = 25

_PROMO_TIERS = [
    # (enh_rune, gold_bars, ruby_per_step, leg_stones_at_5th, myth_stones_at_5th)
    (12500, 150,  750_000,  5,  0),
    (16250, 195,  975_000, 10,  0),
    (20000, 240, 1_200_000, 15,  0),
    (23750, 285, 1_420_000, 20,  0),
    (27500, 330, 1_650_000,  0, 10),
]

# Per-step costs: index 0 = step 1, index 24 = step 25
# tuple: (enh_rune, gold_bars, ruby, leg_stones, myth_stones)
PROMO_STEP_COSTS: list[tuple[int, int, int, int, int]] = []
for _rune, _gold, _ruby, _leg, _myth in _PROMO_TIERS:
    for _ in range(4):
        PROMO_STEP_COSTS.append((_rune, _gold, _ruby, 0, 0))
    PROMO_STEP_COSTS.append((_rune, _gold, 0, _leg, _myth))

# Cumulative costs: index = steps completed
PROMO_CUMUL_RUNE: list[int] = [0] * (MAX_PROMOTION + 1)
PROMO_CUMUL_GOLD: list[int] = [0] * (MAX_PROMOTION + 1)
PROMO_CUMUL_RUBY: list[int] = [0] * (MAX_PROMOTION + 1)
PROMO_CUMUL_LEG:  list[int] = [0] * (MAX_PROMOTION + 1)
PROMO_CUMUL_MYTH: list[int] = [0] * (MAX_PROMOTION + 1)
for _i, (_r, _g, _rb, _l, _m) in enumerate(PROMO_STEP_COSTS):
    PROMO_CUMUL_RUNE[_i + 1] = PROMO_CUMUL_RUNE[_i] + _r
    PROMO_CUMUL_GOLD[_i + 1] = PROMO_CUMUL_GOLD[_i] + _g
    PROMO_CUMUL_RUBY[_i + 1] = PROMO_CUMUL_RUBY[_i] + _rb
    PROMO_CUMUL_LEG[_i  + 1] = PROMO_CUMUL_LEG[_i]  + _l
    PROMO_CUMUL_MYTH[_i + 1] = PROMO_CUMUL_MYTH[_i] + _m


def gear_promo_cost(from_promo: int, to_promo: int) -> tuple[int, int, int, int, int]:
    """Returns (enh_rune, gold_bars, ruby, leg_stones, myth_stones)."""
    f = max(0, min(from_promo, MAX_PROMOTION))
    t = max(0, min(to_promo,   MAX_PROMOTION))
    return (
        max(0, PROMO_CUMUL_RUNE[t] - PROMO_CUMUL_RUNE[f]),
        max(0, PROMO_CUMUL_GOLD[t] - PROMO_CUMUL_GOLD[f]),
        max(0, PROMO_CUMUL_RUBY[t] - PROMO_CUMUL_RUBY[f]),
        max(0, PROMO_CUMUL_LEG[t]  - PROMO_CUMUL_LEG[f]),
        max(0, PROMO_CUMUL_MYTH[t] - PROMO_CUMUL_MYTH[f]),
    )


def promo_label(step: int, lang: str = "pt") -> str:
    """Human-readable label for a promotion step (0-25)."""
    if step == 0:
        return "0★" + (" — Sem promoção" if lang == "pt" else " — No promotion")
    star = (step - 1) // 5 + 1
    leg  = (step - 1) % 5 + 1
    return f"★{star} · {leg}/5"


def promo_star_idx(step: int) -> int:
    """Map promotion step (0-25) to behemoth STAR_IMAGES platinum index (51-75)."""
    if step == 0:
        return 0
    return 50 + step  # platinum tier: 51 = ★1 1/5, 75 = ★5 5/5


# ── Combined calculator ───────────────────────────────────────────────────────

def calc_gear_piece(
    from_lv: int = 0,
    to_lv: int = 0,
    from_promo: int = 0,
    to_promo: int = 0,
    needs_mark: bool = False,
) -> dict:
    """Calculate total resources for upgrading one gear piece."""
    lv_rune, lv_ruby = gear_level_cost(from_lv, to_lv)
    pr_rune, pr_gold, pr_ruby, pr_leg, pr_myth = gear_promo_cost(from_promo, to_promo)
    return {
        "enh_rune":    lv_rune + pr_rune,
        "ruby":        lv_ruby + pr_ruby,
        "gold_bars":   pr_gold,
        "leg_stones":  pr_leg,
        "myth_stones": pr_myth,
        "marks":       1 if needs_mark else 0,
        # breakdown
        "lv_enh_rune": lv_rune,
        "lv_ruby":     lv_ruby,
        "pr_enh_rune": pr_rune,
        "pr_ruby":     pr_ruby,
    }
