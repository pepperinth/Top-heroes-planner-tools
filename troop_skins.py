"""
Top Heroes — Troop Skin Calculator
Streamlit app: mirrors the logic from TroopSkin_Calculator_v7.xlsx
"""

import streamlit as st

# ── Game data ──────────────────────────────────────────────────────────────
SKINS = {
    "Legendary": [
        "Heavy Cavalry", "Honor Guard", "Siege Vehicle", "Brave Fighter",
        "Skeleton Soldier", "Tree Spirit", "Desert Knight", "Divine Spirit",
    ],
    "Epic": [
        "Elegant Butler", "Drum Corps", "Bearskin Warrior", "Samurai",
        "Logistic Follower",
    ],
    "Rare": ["Shield Soldier", "Cavalry"],
}

# Cumulative medals (Legendary) to BE AT level N
LEG_CUM = {
    1: 0, 2: 1600, 3: 3900, 4: 7100, 5: 11500, 6: 17700, 7: 26400,
    8: 39400, 9: 56400, 10: 80400, 11: 114400, 12: 154400, 13: 202400,
    14: 260400, 15: 329400, 16: 412400, 17: 632400, 18: 776400,
    19: 948400, 20: 1155400, 21: 1383400, 22: 1632400, 23: 1905400,
    24: 2205400, 25: 2535400, 26: 2935400, 27: 3335400, 28: 3775400,
    29: 4259400, 30: 4791400, 31: 5351400, 32: 5941400, 33: 6556400,
    34: 7204400, 35: 7882400, 36: 8596400, 37: 9345400, 38: 10136400,
    39: 10960400, 40: 11832400, 41: 12732400, 42: 13650400, 43: 14595400,
    44: 15595400, 45: 16605400, 46: 17635400, 47: 18685400, 48: 19755400,
    49: 20845400, 50: 20845400,
}

MILESTONES = [10, 20, 30, 40, 45, 50]
STAR_LABELS = {10: "⭐", 20: "⭐⭐", 30: "⭐⭐⭐", 40: "⭐⭐⭐⭐", 45: "⭐⭐⭐⭐⭐", 50: "⭐⭐⭐⭐⭐⭐ MAX"}
MS_TOKENS = {10: 1, 20: 1, 30: 2, 40: 3, 45: 3, 50: 3}  # from source table images
TOK_CUM = {10: 1, 20: 2, 30: 4, 40: 7, 45: 10, 50: 13}  # cumulative tokens lv1→m

HONOR_MEDALS = {"Legendary": 50_000, "Epic": 25_000, "Rare": 12_500}
RATIO = {"Legendary": 1, "Epic": 2, "Rare": 4}


def cum_medals(level: int, rarity: str) -> int:
    lv = max(1, min(50, level))
    return LEG_CUM[lv] // RATIO[rarity]


def tokens_for_milestones(cur_lv: int, tgt_lv: int) -> int:
    return sum(
        MS_TOKENS[m] for m in MILESTONES if cur_lv < m <= tgt_lv
    )


def tok_cum_paid(cur_lv: int) -> int:
    """Tokens already spent at milestones at or below cur_lv."""
    return sum(MS_TOKENS[m] for m in MILESTONES if cur_lv >= m)


def honor_medals_needed(cur_hl: int, tgt_hl: int, rarity: str, tokens_for_honor: int) -> int:
    hl_needed = max(0, tgt_hl - cur_hl)
    hl_by_tokens = min(tokens_for_honor * 5, hl_needed)
    hl_by_medals = max(0, hl_needed - hl_by_tokens)
    return hl_by_medals * HONOR_MEDALS[rarity]


def best_reachable_milestone(
    cur_lv: int, medal_stock: int, token_stock: int, rarity: str
) -> int:
    paid = tok_cum_paid(cur_lv)
    best = 0
    for m in MILESTONES:
        med_need = cum_medals(m, rarity) - cum_medals(cur_lv, rarity)
        tok_need = TOK_CUM[m] - paid
        if med_need <= medal_stock and tok_need <= token_stock:
            best = m
    return best


def next_milestone(best: int) -> int:
    for m in MILESTONES:
        if m > best:
            return m
    return 50


# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Top Heroes — Troop Skin Calculator",
    page_icon="🧮",
    layout="wide",
)

st.title("🧮 Top Heroes — Troop Skin Calculator")
st.caption("Track medals, tokens, and plan your path to max level and honor.")

# ══════════════════════════════════════════════════════════════════════════
# SIDEBAR — Inventory
# ══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("📦 Inventory")

    st.subheader("🏅 Medals (universal)")
    medal_stock = st.number_input(
        "Total Medals in Stock", min_value=0, value=0, step=10_000, format="%d"
    )

    st.divider()
    st.subheader("🎟️ Tokens / Copies")
    st.caption("Rarity-specific. Enter total tokens + copies combined.")

    token_stock = {}
    for rar in ("Legendary", "Epic", "Rare"):
        emoji = "🟡" if rar == "Legendary" else ("🟣" if rar == "Epic" else "🔵")
        token_stock[rar] = st.number_input(
            f"{emoji} {rar} Tokens / Copies",
            min_value=0, value=0, step=1, format="%d",
        )

    st.divider()
    st.subheader("📋 Skin-Specific Copies")
    st.caption("Optional — track per skin if needed.")
    skin_copies = {}
    for rar, skins in SKINS.items():
        emoji = "🟡" if rar == "Legendary" else ("🟣" if rar == "Epic" else "🔵")
        with st.expander(f"{emoji} {rar}"):
            for skin in skins:
                skin_copies[skin] = st.number_input(
                    skin, min_value=0, value=0, step=1,
                    key=f"copy_{skin}", format="%d",
                )

# ══════════════════════════════════════════════════════════════════════════
# MAIN — Selection + Inputs
# ══════════════════════════════════════════════════════════════════════════
col_sel1, col_sel2 = st.columns(2)
with col_sel1:
    rarity = st.selectbox("🎯 Rarity", list(SKINS.keys()))
with col_sel2:
    skin = st.selectbox("🎯 Skin", SKINS[rarity])

st.divider()

col_lv, col_hl = st.columns(2)
with col_lv:
    st.subheader("🎮 Level (1–50)")
    c1, c2 = st.columns(2)
    cur_lv = c1.number_input("Current", min_value=1, max_value=50, value=1, key="cur_lv")
    tgt_lv = c2.number_input("Target",  min_value=1, max_value=50, value=50, key="tgt_lv")

with col_hl:
    st.subheader("🏆 Honor Level (0–150)")
    st.caption("⚠️ Unlocks after Level 50 + Level 50 milestone tokens.")
    c3, c4 = st.columns(2)
    cur_hl = c3.number_input("Current", min_value=0, max_value=150, value=0, key="cur_hl")
    tgt_hl = c4.number_input("Target",  min_value=0, max_value=150, value=150, key="tgt_hl")

tokens_for_honor = st.number_input(
    "🎟️ Tokens to use for Honor Levels",
    min_value=0, value=0, step=1, format="%d",
    help="1 token = 5 Honor Levels (HL 1–100) · 1 token = 0.5 levels (HL 101–150). "
         "Remaining honor levels will be covered by medals.",
)

st.divider()

# ══════════════════════════════════════════════════════════════════════════
# CALCULATIONS
# ══════════════════════════════════════════════════════════════════════════
med_levels   = max(0, cum_medals(tgt_lv, rarity) - cum_medals(cur_lv, rarity)) if tgt_lv > cur_lv else 0
med_honor    = honor_medals_needed(cur_hl, tgt_hl, rarity, tokens_for_honor)
med_total    = med_levels + med_honor
med_missing  = max(0, med_total - medal_stock)
med_surplus  = max(0, medal_stock - med_total)

tok_milestones = tokens_for_milestones(cur_lv, tgt_lv)
tok_honor      = tokens_for_honor
tok_total      = tok_milestones + tok_honor
tok_avail      = token_stock[rarity]
tok_missing    = max(0, tok_total - tok_avail)
tok_surplus    = max(0, tok_avail - tok_total)

skin_copy_stock = skin_copies.get(skin, 0)

# ── Results ────────────────────────────────────────────────────────────────
st.subheader("📊 Required to Reach Target")

col_m, col_t = st.columns(2)

with col_m:
    st.markdown("**🏅 Medals**")
    st.metric("Levels (1–50)",        f"{med_levels:,}")
    st.metric("Honor Levels (1–150)", f"{med_honor:,}",
              help="Only honor levels not covered by tokens.")
    st.metric("TOTAL Medals Required", f"{med_total:,}")
    st.metric("Medals in Stock",       f"{medal_stock:,}")
    if med_missing > 0:
        st.error(f"❗ Medals Still Needed: **{med_missing:,}**")
    else:
        st.success(f"✅ Medal Surplus: **{med_surplus:,}**")

with col_t:
    st.markdown("**🎟️ Tokens / Copies**")
    st.metric("Milestone Buffs",       f"{tok_milestones}",
              help="Lv10=1 · Lv20=1 · Lv30=2 · Lv40=3 · Lv45=3 · Lv50=3")
    st.metric("Honor Levels",          f"{tok_honor}")
    st.metric("TOTAL Tokens Required", f"{tok_total}")
    st.metric("Tokens in Stock",       f"{tok_avail:,}")
    st.metric(f"Copies of '{skin}'",   f"{skin_copy_stock:,}")
    if tok_missing > 0:
        st.error(f"❗ Tokens Still Needed: **{tok_missing}**")
    else:
        st.success(f"✅ Token Surplus: **{tok_surplus}**")

st.divider()

# ── Simulation ─────────────────────────────────────────────────────────────
st.subheader("🔭 Simulation — What Can You Reach With Your Current Stock?")

best_ms  = best_reachable_milestone(cur_lv, medal_stock, tok_avail, rarity)
next_ms  = next_milestone(best_ms)
paid_tok = tok_cum_paid(cur_lv)

if best_ms == 0:
    st.warning("⚠️ Your current stock is not enough to reach the next milestone from your current level.")
    reach_label = "Below Level 10 milestone"
else:
    reach_label = f"Level {best_ms} {STAR_LABELS[best_ms]}"
    st.success(f"✅ Furthest milestone reachable: **{reach_label}**")

# Next milestone gap
next_med_need = max(0, cum_medals(next_ms, rarity) - cum_medals(cur_lv, rarity) - medal_stock)
next_tok_need = max(0, TOK_CUM.get(next_ms, 0) - paid_tok - tok_avail)

col_s1, col_s2, col_s3 = st.columns(3)
col_s1.metric("🔜 Next Milestone", f"Level {next_ms} {STAR_LABELS[next_ms]}")
col_s2.metric("🏅 Medals Missing for Next Milestone", f"{next_med_need:,}")
col_s3.metric("🎟️ Tokens Missing for Next Milestone", f"{next_tok_need}")

col_s4, col_s5 = st.columns(2)
col_s4.metric("🏅 Medal Surplus After Target",  f"{med_surplus:,}")
col_s5.metric("🎟️ Token Surplus After Target",  f"{tok_surplus}")

st.divider()

# ── Milestone reference ────────────────────────────────────────────────────
with st.expander("📊 Reference — Medal Cost Per Level & Milestone Tokens"):
    st.caption(f"Costs shown for **{rarity}**. Orange rows = milestones requiring tokens.")
    rows = []
    for lv in range(1, 51):
        prev = LEG_CUM.get(lv - 1, 0)
        cost = (LEG_CUM[lv] - prev) // RATIO[rarity]
        is_ms = lv in MILESTONES
        rows.append({
            "Level": f"{lv} {STAR_LABELS.get(lv, '')}",
            "Medal Cost": cost if lv > 1 else 0,
            "Tokens at Milestone": MS_TOKENS.get(lv, "—"),
            "Cumulative Medals": LEG_CUM[lv] // RATIO[rarity],
        })

    import pandas as pd
    df = pd.DataFrame(rows)
    # Highlight milestone rows
    def highlight_ms(row):
        lv_num = int(row["Level"].split()[0])
        if lv_num in MILESTONES:
            return ["background-color: #e65100; color: white"] * len(row)
        return [""] * len(row)

    st.dataframe(
        df.style.apply(highlight_ms, axis=1),
        use_container_width=True,
        hide_index=True,
    )

    totals = {
        "Total Medals (Lv 1→50)": f"{LEG_CUM[49] // RATIO[rarity]:,}",
        "Total Tokens (Lv 1→50)": "13",
        "Honor Medals (HL 1→150)": f"{HONOR_MEDALS[rarity] * 150:,}",
        "Honor Tokens (HL 1→150)": "120",
    }
    st.table(pd.DataFrame(totals.items(), columns=["", "Value"]).set_index(""))
