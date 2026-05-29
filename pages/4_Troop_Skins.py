"""
pages/4_Troop_Skins.py — Troop Skin Calculator page.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Troop Skin Calculator", page_icon="🧢", layout="wide")

# ── Language ───────────────────────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "pt"

with st.sidebar:
    st.markdown("### 🌐 Idioma / Language")
    lang_pick = st.radio(
        "", ["🇧🇷 Português", "🇬🇧 English"],
        index=0 if st.session_state.lang == "pt" else 1,
        horizontal=True, label_visibility="collapsed", key="lang_skin",
    )
    st.session_state.lang = "pt" if "Português" in lang_pick else "en"
    st.divider()
    st.page_link("app.py", label="← Home")
    st.divider()
    st.warning(
        "⚠️ **Versão Beta**\nAlgumas funcionalidades podem estar incompletas ou mudar."
        if st.session_state.lang == "pt" else
        "⚠️ **Beta Version**\nSome features may be incomplete or subject to change."
    )
    st.divider()

    # ── Inventário (sidebar) ───────────────────────────────────────────────────
    lang = st.session_state.lang
    def t(pt, en): return pt if lang == "pt" else en

    st.header("📦 " + t("Inventário", "Inventory"))

    st.subheader("🏅 " + t("Medalhas (universais)", "Medals (universal)"))
    medal_stock = st.number_input(
        t("Total de Medalhas no estoque", "Total Medals in Stock"),
        min_value=0, value=0, step=10_000, format="%d",
    )

    st.divider()
    st.subheader("🎟️ " + t("Tokens / Cópias", "Tokens / Copies"))
    st.caption(t(
        "Por raridade. Inclua tokens e cópias juntos.",
        "Rarity-specific. Enter total tokens + copies combined.",
    ))
    token_stock = {}
    for rar, emoji in [("Legendary", "🟡"), ("Epic", "🟣"), ("Rare", "🔵")]:
        rar_pt = {"Legendary": "Lendária", "Epic": "Épica", "Rare": "Rara"}[rar]
        token_stock[rar] = st.number_input(
            f"{emoji} {t(rar_pt, rar)} — {t('Tokens / Cópias', 'Tokens / Copies')}",
            min_value=0, value=0, step=1, format="%d", key=f"tok_{rar}",
        )

    st.divider()
    st.subheader("📋 " + t("Cópias por Skin", "Skin-Specific Copies"))
    st.caption(t("Opcional — rastreie por skin se necessário.", "Optional — track per skin if needed."))

lang = st.session_state.lang

# ── Game data ──────────────────────────────────────────────────────────────────
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

MILESTONES  = [10, 20, 30, 40, 45, 50]
STAR_LABELS = {10: "⭐", 20: "⭐⭐", 30: "⭐⭐⭐", 40: "⭐⭐⭐⭐", 45: "⭐⭐⭐⭐⭐", 50: "⭐⭐⭐⭐⭐⭐ MAX"}
MS_TOKENS   = {10: 1, 20: 1, 30: 2, 40: 3, 45: 3, 50: 3}
TOK_CUM     = {10: 1, 20: 2, 30: 4, 40: 7, 45: 10, 50: 13}

HONOR_MEDALS = {"Legendary": 50_000, "Epic": 25_000, "Rare": 12_500}
RATIO        = {"Legendary": 1, "Epic": 2, "Rare": 4}

RAR_PT = {"Legendary": "Lendária", "Epic": "Épica", "Rare": "Rara"}


def cum_medals(level: int, rarity: str) -> int:
    return LEG_CUM[max(1, min(50, level))] // RATIO[rarity]


def tokens_for_milestones(cur_lv: int, tgt_lv: int) -> int:
    return sum(MS_TOKENS[m] for m in MILESTONES if cur_lv < m <= tgt_lv)


def tok_cum_paid(cur_lv: int) -> int:
    return sum(MS_TOKENS[m] for m in MILESTONES if cur_lv >= m)


def honor_medals_needed(cur_hl: int, tgt_hl: int, rarity: str, tokens_for_honor: int) -> int:
    hl_needed    = max(0, tgt_hl - cur_hl)
    hl_by_tokens = min(tokens_for_honor * 5, hl_needed)
    hl_by_medals = max(0, hl_needed - hl_by_tokens)
    return hl_by_medals * HONOR_MEDALS[rarity]


def best_reachable_milestone(cur_lv: int, medal_stock: int, token_stock: int, rarity: str) -> int:
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


# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🧢 " + t("Calculadora de Troop Skin", "Troop Skin Calculator"))
st.caption(t(
    "Planeje medalhas, tokens e o caminho até o nível máximo e Honor.",
    "Plan medals, tokens, and your path to max level and Honor.",
))

# ── Skin-specific copies (sidebar continued) ───────────────────────────────────
skin_copies = {}
with st.sidebar:
    for rar, skins in SKINS.items():
        emoji = "🟡" if rar == "Legendary" else ("🟣" if rar == "Epic" else "🔵")
        rar_label = t(RAR_PT[rar], rar)
        with st.expander(f"{emoji} {rar_label}"):
            for skin in skins:
                skin_copies[skin] = st.number_input(
                    skin, min_value=0, value=0, step=1,
                    key=f"copy_{skin}", format="%d",
                )

# ── Seleção de skin ────────────────────────────────────────────────────────────
col_sel1, col_sel2 = st.columns(2)
with col_sel1:
    rar_opts  = list(SKINS.keys())
    rar_labels_pt = [t(RAR_PT[r], r) for r in rar_opts]
    rar_sel_label = st.selectbox(t("🎯 Raridade", "🎯 Rarity"), rar_labels_pt)
    rarity = rar_opts[rar_labels_pt.index(rar_sel_label)]
with col_sel2:
    skin = st.selectbox(t("🎯 Skin", "🎯 Skin"), SKINS[rarity])

st.divider()

# ── Inputs de nível e honor ────────────────────────────────────────────────────
col_lv, col_hl = st.columns(2)
with col_lv:
    st.subheader(t("🎮 Nível (1–50)", "🎮 Level (1–50)"))
    c1, c2 = st.columns(2)
    cur_lv = c1.number_input(t("Atual", "Current"), min_value=1, max_value=50, value=1, key="cur_lv")
    tgt_lv = c2.number_input(t("Alvo",  "Target"),  min_value=1, max_value=50, value=50, key="tgt_lv")

with col_hl:
    st.subheader(t("🏆 Honor Level (0–150)", "🏆 Honor Level (0–150)"))
    st.caption(t(
        "⚠️ Disponível após Nível 50 + tokens do milestone Nível 50.",
        "⚠️ Unlocks after Level 50 + Level 50 milestone tokens.",
    ))
    c3, c4 = st.columns(2)
    cur_hl = c3.number_input(t("Atual", "Current"), min_value=0, max_value=150, value=0, key="cur_hl")
    tgt_hl = c4.number_input(t("Alvo",  "Target"),  min_value=0, max_value=150, value=0, key="tgt_hl")

tokens_for_honor = st.number_input(
    t("🎟️ Tokens a usar em Honor Levels", "🎟️ Tokens to use for Honor Levels"),
    min_value=0, value=0, step=1, format="%d",
    help=t(
        "1 token = 5 Honor Levels (HL 1–100) · 1 token = 0,5 levels (HL 101–150). "
        "Os restantes serão cobertos por medalhas.",
        "1 token = 5 Honor Levels (HL 1–100) · 1 token = 0.5 levels (HL 101–150). "
        "Remaining honor levels will be covered by medals.",
    ),
)

st.divider()

# ── Cálculos ───────────────────────────────────────────────────────────────────
med_levels  = max(0, cum_medals(tgt_lv, rarity) - cum_medals(cur_lv, rarity)) if tgt_lv > cur_lv else 0
med_honor   = honor_medals_needed(cur_hl, tgt_hl, rarity, tokens_for_honor)
med_total   = med_levels + med_honor
med_missing = max(0, med_total - medal_stock)
med_surplus = max(0, medal_stock - med_total)

tok_milestones = tokens_for_milestones(cur_lv, tgt_lv)
tok_total      = tok_milestones + tokens_for_honor
tok_avail      = token_stock[rarity]
tok_missing    = max(0, tok_total - tok_avail)
tok_surplus    = max(0, tok_avail - tok_total)

skin_copy_stock = skin_copies.get(skin, 0)

# ── Resultados ─────────────────────────────────────────────────────────────────
st.subheader("📊 " + t("Necessário para atingir o alvo", "Required to Reach Target"))

col_m, col_t = st.columns(2)

with col_m:
    st.markdown(f"**🏅 {t('Medalhas', 'Medals')}**")
    st.metric(t("Níveis (1–50)",         "Levels (1–50)"),        f"{med_levels:,}")
    st.metric(t("Honor Levels (1–150)",  "Honor Levels (1–150)"), f"{med_honor:,}",
              help=t("Apenas HLs não cobertos por tokens.", "Only honor levels not covered by tokens."))
    st.metric(t("TOTAL de Medalhas",     "TOTAL Medals Required"), f"{med_total:,}")
    st.metric(t("Medalhas no estoque",   "Medals in Stock"),       f"{medal_stock:,}")
    if med_missing > 0:
        st.error(t(f"❗ Medalhas faltando: **{med_missing:,}**", f"❗ Medals Still Needed: **{med_missing:,}**"))
    else:
        st.success(t(f"✅ Saldo de medalhas: **{med_surplus:,}**", f"✅ Medal Surplus: **{med_surplus:,}**"))

with col_t:
    st.markdown(f"**🎟️ {t('Tokens / Cópias', 'Tokens / Copies')}**")
    st.metric(t("Buffs de Milestone",    "Milestone Buffs"),       f"{tok_milestones}",
              help="Lv10=1 · Lv20=1 · Lv30=2 · Lv40=3 · Lv45=3 · Lv50=3")
    st.metric(t("Honor Levels",          "Honor Levels"),          f"{tokens_for_honor}")
    st.metric(t("TOTAL de Tokens",       "TOTAL Tokens Required"), f"{tok_total}")
    st.metric(t("Tokens no estoque",     "Tokens in Stock"),       f"{tok_avail:,}")
    st.metric(f"{t('Cópias de', 'Copies of')} '{skin}'",          f"{skin_copy_stock:,}")
    if tok_missing > 0:
        st.error(t(f"❗ Tokens faltando: **{tok_missing}**", f"❗ Tokens Still Needed: **{tok_missing}**"))
    else:
        st.success(t(f"✅ Saldo de tokens: **{tok_surplus}**", f"✅ Token Surplus: **{tok_surplus}**"))

st.divider()

# ── Simulação ──────────────────────────────────────────────────────────────────
st.subheader("🔭 " + t(
    "Simulação — Até onde você chega com o estoque atual?",
    "Simulation — What Can You Reach With Your Current Stock?",
))

best_ms  = best_reachable_milestone(cur_lv, medal_stock, tok_avail, rarity)
next_ms  = next_milestone(best_ms)
paid_tok = tok_cum_paid(cur_lv)

if best_ms == 0:
    st.warning(t(
        "⚠️ Seu estoque atual não é suficiente para atingir o próximo milestone a partir do nível atual.",
        "⚠️ Your current stock is not enough to reach the next milestone from your current level.",
    ))
else:
    reach_label = f"{t('Nível', 'Level')} {best_ms} {STAR_LABELS[best_ms]}"
    st.success(t(
        f"✅ Milestone mais avançado alcançável: **{reach_label}**",
        f"✅ Furthest milestone reachable: **{reach_label}**",
    ))

next_med_need = max(0, cum_medals(next_ms, rarity) - cum_medals(cur_lv, rarity) - medal_stock)
next_tok_need = max(0, TOK_CUM.get(next_ms, 0) - paid_tok - tok_avail)

col_s1, col_s2, col_s3 = st.columns(3)
col_s1.metric(t("🔜 Próximo Milestone", "🔜 Next Milestone"),
              f"{t('Nível','Level')} {next_ms} {STAR_LABELS[next_ms]}")
col_s2.metric(t("🏅 Medalhas para o próximo", "🏅 Medals Missing for Next"), f"{next_med_need:,}")
col_s3.metric(t("🎟️ Tokens para o próximo",   "🎟️ Tokens Missing for Next"), f"{next_tok_need}")

col_s4, col_s5 = st.columns(2)
col_s4.metric(t("🏅 Saldo de medalhas após alvo", "🏅 Medal Surplus After Target"), f"{med_surplus:,}")
col_s5.metric(t("🎟️ Saldo de tokens após alvo",   "🎟️ Token Surplus After Target"), f"{tok_surplus}")

st.divider()

# ── Tabela de referência ────────────────────────────────────────────────────────
with st.expander(t(
    f"📊 Referência — Custo de medalhas por nível ({t(RAR_PT[rarity], rarity)})",
    f"📊 Reference — Medal Cost Per Level ({rarity})",
)):
    rows = []
    for lv in range(1, 51):
        prev = LEG_CUM.get(lv - 1, 0)
        cost = (LEG_CUM[lv] - prev) // RATIO[rarity]
        rows.append({
            t("Nível", "Level"):             f"{lv} {STAR_LABELS.get(lv, '')}",
            t("Custo de Medalhas", "Medal Cost"): cost if lv > 1 else 0,
            t("Tokens no Milestone", "Tokens at Milestone"): MS_TOKENS.get(lv, "—"),
            t("Medalhas Acumuladas", "Cumulative Medals"): LEG_CUM[lv] // RATIO[rarity],
        })

    def highlight_ms(row):
        lv_num = int(row[t("Nível","Level")].split()[0])
        return (["background-color: #e65100; color: white"] * len(row)
                if lv_num in MILESTONES else [""] * len(row))

    st.dataframe(
        pd.DataFrame(rows).style.apply(highlight_ms, axis=1),
        use_container_width=True, hide_index=True,
    )

    totals = {
        t("Total Medalhas (Nível 1→50)",  "Total Medals (Lv 1→50)"):    f"{LEG_CUM[50] // RATIO[rarity]:,}",
        t("Total Tokens (Nível 1→50)",    "Total Tokens (Lv 1→50)"):    "13",
        t("Medalhas Honor (HL 1→150)",    "Honor Medals (HL 1→150)"):   f"{HONOR_MEDALS[rarity] * 150:,}",
        t("Tokens Honor (HL 1→150)",      "Honor Tokens (HL 1→150)"):   "120",
    }
    st.table(pd.DataFrame(totals.items(), columns=["", "Value"]).set_index(""))
