"""
pages/4_Troop_Skins.py — Troop Skin Calculator page.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from events_data import EVENTS, get_milestone_status
from ui_utils import inject_global_css, section_header, RARITY_COLORS
import persistence

st.set_page_config(page_title="Troop Skin Calculator", page_icon="🧢", layout="wide")

_cm = persistence.new_manager("skins")

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
    st.caption("🍪 " + (
        "Inventário e plano salvos no seu browser."
        if st.session_state.lang == "pt" else
        "Inventory and plan saved in your browser."
    ))
    st.divider()
    st.page_link("app.py", label="← Home")
    st.divider()
    st.warning(
        "⚠️ **Versão Beta**\nAlgumas funcionalidades podem estar incompletas ou mudar."
        if st.session_state.lang == "pt" else
        "⚠️ **Beta Version**\nSome features may be incomplete or subject to change."
    )

lang = st.session_state.lang
def t(pt, en): return pt if lang == "pt" else en

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

# ── Persistence (init + save — placed after SKINS so we can iterate it) ────────
if "skins_initialized" not in st.session_state:
    _saved = persistence.load(_cm, "th_skins")
    if _saved:
        st.session_state["medal_stock"] = int(_saved.get("medal_stock", 0))
        for _rar in ["Legendary", "Epic", "Rare"]:
            st.session_state[f"tok_{_rar}"] = int(_saved.get(f"tok_{_rar}", 0))
        for _rar, _skins_list in SKINS.items():
            for _sn in _skins_list:
                if f"copy_{_sn}" in _saved:
                    st.session_state[f"copy_{_sn}"] = int(_saved[f"copy_{_sn}"])
        if "skin_plan" in _saved:
            st.session_state["skin_plan"] = _saved["skin_plan"]
    st.session_state["skins_initialized"] = True


def _skins_save():
    _data = {
        "medal_stock":   st.session_state.get("medal_stock", 0),
        "tok_Legendary": st.session_state.get("tok_Legendary", 0),
        "tok_Epic":      st.session_state.get("tok_Epic", 0),
        "tok_Rare":      st.session_state.get("tok_Rare", 0),
        "skin_plan":     st.session_state.get("skin_plan", []),
    }
    for _rar, _skins_list in SKINS.items():
        for _sn in _skins_list:
            _data[f"copy_{_sn}"] = st.session_state.get(f"copy_{_sn}", 0)
    persistence.save(_cm, "th_skins", _data)


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
RAR_PT       = {"Legendary": "Lendária", "Epic": "Épica", "Rare": "Rara"}


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
inject_global_css()
st.title("🧢 " + t("Calculadora de Troop Skin", "Troop Skin Calculator"))
st.caption(t(
    "Planeje medalhas, tokens e o caminho até o nível máximo e Honor.",
    "Plan medals, tokens, and your path to max level and Honor.",
))

# ── INVENTÁRIO (compartilhado entre abas) ──────────────────────────────────────
st.divider()
st.subheader("📦 " + t("Inventário", "Inventory"))

inv1, inv2, inv3, inv4 = st.columns(4)
with inv1:
    medal_stock = st.number_input(
        t("🏅 Medalhas", "🏅 Medals"),
        min_value=0, value=0, step=10_000, format="%d", key="medal_stock",
        on_change=_skins_save,
    )
token_stock = {}
for col, (rar, emoji) in zip([inv2, inv3, inv4],
                              [("Legendary", "🟡"), ("Epic", "🟣"), ("Rare", "🔵")]):
    with col:
        token_stock[rar] = st.number_input(
            f"{emoji} {t('Tokens', 'Tokens')} — {t(RAR_PT[rar], rar)}",
            min_value=0, value=0, step=1, format="%d", key=f"tok_{rar}",
            on_change=_skins_save,
        )

st.caption(t(
    "Tokens e cópias da mesma raridade contam juntos.",
    "Tokens and copies of the same rarity count together.",
))

with st.expander(t("📋 Cópias por Skin (opcional)", "📋 Skin-Specific Copies (optional)")):
    skin_copies = {}
    for rar, skins in SKINS.items():
        emoji = "🟡" if rar == "Legendary" else ("🟣" if rar == "Epic" else "🔵")
        st.markdown(f"**{emoji} {t(RAR_PT[rar], rar)}**")
        cols = st.columns(len(skins))
        for col, skin_name in zip(cols, skins):
            with col:
                skin_copies[skin_name] = st.number_input(
                    skin_name, min_value=0, value=0, step=1,
                    key=f"copy_{skin_name}", format="%d",
                    on_change=_skins_save,
                )
        st.divider()

# ── ABAS ───────────────────────────────────────────────────────────────────────
st.divider()
tab_calc, tab_plan, tab_help = st.tabs([
    "🧢 " + t("Calculadora", "Calculator"),
    "📋 " + t("Planejador de Lote", "Batch Planner"),
    "📖 " + t("Instruções & Referência", "Instructions & Reference"),
])

# ══════════════════════════════════════════════════════════════════════════════
# ABA 1 — CALCULADORA
# ══════════════════════════════════════════════════════════════════════════════
with tab_calc:
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        rar_opts      = list(SKINS.keys())
        rar_labels_pt = [t(RAR_PT[r], r) for r in rar_opts]
        rar_sel_label = st.selectbox(t("🎯 Raridade", "🎯 Rarity"), rar_labels_pt)
        rarity = rar_opts[rar_labels_pt.index(rar_sel_label)]
    with col_sel2:
        skin = st.selectbox(t("🎯 Skin", "🎯 Skin"), SKINS[rarity])

    st.divider()

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

    _rar_color = RARITY_COLORS.get(rarity, "#5C3D1E")
    results_header = lambda lbl: st.markdown(
        f'<div style="border-left:5px solid {_rar_color};padding:5px 14px;'
        f'border-radius:0 8px 8px 0;background:{_rar_color}14;font-weight:700;margin:10px 0 6px;">{lbl}</div>',
        unsafe_allow_html=True)
    results_header(f"📊 {t('Necessário para atingir o alvo','Required to Reach Target')}")
    col_m, col_t = st.columns(2)

    with col_m:
        st.markdown(f"**🏅 {t('Medalhas', 'Medals')}**")
        st.metric(t("Níveis (1–50)",        "Levels (1–50)"),         f"{med_levels:,}")
        st.metric(t("Honor Levels (1–150)", "Honor Levels (1–150)"),  f"{med_honor:,}",
                  help=t("Apenas HLs não cobertos por tokens.", "Only honor levels not covered by tokens."))
        st.metric(t("TOTAL de Medalhas",    "TOTAL Medals Required"),  f"{med_total:,}")
        st.metric(t("Medalhas no estoque",  "Medals in Stock"),        f"{medal_stock:,}")
        if med_missing > 0:
            st.error(t(f"❗ Medalhas faltando: **{med_missing:,}**", f"❗ Medals Still Needed: **{med_missing:,}**"))
        else:
            st.success(t(f"✅ Saldo: **{med_surplus:,}**", f"✅ Medal Surplus: **{med_surplus:,}**"))

    with col_t:
        st.markdown(f"**🎟️ {t('Tokens / Cópias', 'Tokens / Copies')}**")
        st.metric(t("Buffs de Milestone",  "Milestone Buffs"),         f"{tok_milestones}",
                  help="Lv10=1 · Lv20=1 · Lv30=2 · Lv40=3 · Lv45=3 · Lv50=3")
        st.metric(t("Honor Levels",        "Honor Levels"),            f"{tokens_for_honor}")
        st.metric(t("TOTAL de Tokens",     "TOTAL Tokens Required"),   f"{tok_total}")
        st.metric(t("Tokens no estoque",   "Tokens in Stock"),         f"{tok_avail:,}")
        st.metric(f"{t('Cópias de', 'Copies of')} '{skin}'",          f"{skin_copy_stock:,}")
        if tok_missing > 0:
            st.error(t(f"❗ Tokens faltando: **{tok_missing}**", f"❗ Tokens Still Needed: **{tok_missing}**"))
        else:
            st.success(t(f"✅ Saldo: **{tok_surplus}**", f"✅ Token Surplus: **{tok_surplus}**"))

    st.divider()
    st.subheader("🔭 " + t(
        "Simulação — Até onde você chega com o estoque atual?",
        "Simulation — What Can You Reach With Your Current Stock?",
    ))

    best_ms  = best_reachable_milestone(cur_lv, medal_stock, tok_avail, rarity)
    next_ms  = next_milestone(best_ms)
    paid_tok = tok_cum_paid(cur_lv)

    if best_ms == 0:
        st.warning(t(
            "⚠️ Seu estoque atual não é suficiente para atingir o próximo milestone.",
            "⚠️ Your current stock is not enough to reach the next milestone.",
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

    # ── Impacto nos Eventos Regulares ─────────────────────────────────────────
    st.divider()
    st.markdown("**📅 " + t("Impacto nos Eventos Regulares", "Regular Event Impact") + "**")

    ev_gear  = next(e for e in EVENTS if e["sheet"] == "Lord_Gear_Trial")
    ev_gname = ev_gear.get("name_pt", ev_gear["name"]) if lang == "pt" else ev_gear["name"]

    _pts_per_tok = 30 if rarity == "Rare" else 300 if rarity == "Epic" else 3000
    pts_med_c  = med_total / 200
    pts_tok_c  = tok_total * _pts_per_tok
    pts_gear_c = pts_med_c + pts_tok_c

    egc1, egc2, egc3 = st.columns(3)
    egc1.metric(t("🏅 Medalhas", "🏅 Medals"), f"{pts_med_c:,.1f} pts",
                help=t(f"{med_total:,} medalhas ÷ 200", f"{med_total:,} medals ÷ 200"))
    egc2.metric(f"🎟️ {t('Tokens', 'Tokens')} ({t(RAR_PT[rarity], rarity)})",
                f"{pts_tok_c:,.0f} pts",
                help=t(f"{tok_total} tokens × {_pts_per_tok}", f"{tok_total} tokens × {_pts_per_tok}"))
    egc3.metric(f"📊 {ev_gname}", f"{pts_gear_c:,.1f} pts")

    ms_icons_c = "  ".join(
        f"✅ {s['value']:,}" if s["reached"] else f"⬜ {s['value']:,}"
        for s in get_milestone_status(ev_gear["milestones"], pts_gear_c)
    )
    st.caption(f"Milestones: {ms_icons_c}")
    st.caption(t(
        "⚠️ Enviar sobrescreve qualquer envio anterior desta skin.",
        "⚠️ Sending overwrites any previous single-skin send.",
    ))

    if st.button("📅 " + t("Enviar para Eventos", "Send to Events"), key="send_skin_calc_evt"):
        st.session_state["_src_troop_skin_Lord_Gear_Trial"] = int(pts_gear_c)
        st.session_state["_calc_contrib_Lord_Gear_Trial_4"] = int((tok_total if rarity == "Rare"      else 0) * 30)
        st.session_state["_calc_contrib_Lord_Gear_Trial_5"] = int((tok_total if rarity == "Epic"      else 0) * 300)
        st.session_state["_calc_contrib_Lord_Gear_Trial_6"] = int((tok_total if rarity == "Legendary" else 0) * 3000)
        st.session_state["_calc_contrib_Lord_Gear_Trial_7"] = int(pts_med_c)
        st.session_state["_calc_sent_Lord_Gear_Trial"]      = True
        st.success(t(
            f"✅ {pts_gear_c:,.1f} pts enviados para **{ev_gname}**! Acesse Eventos Regulares para ver.",
            f"✅ {pts_gear_c:,.1f} pts sent to **{ev_gname}**! Go to Regular Events to see them.",
        ))

    st.divider()
    with st.expander(t(
        f"📊 Referência — Custo de medalhas por nível ({t(RAR_PT[rarity], rarity)})",
        f"📊 Reference — Medal Cost Per Level ({rarity})",
    )):
        rows = []
        for lv in range(1, 51):
            prev = LEG_CUM.get(lv - 1, 0)
            cost = (LEG_CUM[lv] - prev) // RATIO[rarity]
            rows.append({
                t("Nível", "Level"):                           f"{lv} {STAR_LABELS.get(lv, '')}",
                t("Custo de Medalhas", "Medal Cost"):          cost if lv > 1 else 0,
                t("Tokens no Milestone", "Tokens at MS"):      MS_TOKENS.get(lv, "—"),
                t("Medalhas Acumuladas", "Cumulative Medals"):  LEG_CUM[lv] // RATIO[rarity],
            })

        def highlight_ms(row):
            lv_num = int(row[t("Nível", "Level")].split()[0])
            return (["background-color: #e65100; color: white"] * len(row)
                    if lv_num in MILESTONES else [""] * len(row))

        st.dataframe(
            pd.DataFrame(rows).style.apply(highlight_ms, axis=1),
            use_container_width=True, hide_index=True,
        )
        totals = {
            t("Total Medalhas (Nível 1→50)",  "Total Medals (Lv 1→50)"):  f"{LEG_CUM[50] // RATIO[rarity]:,}",
            t("Total Tokens (Nível 1→50)",    "Total Tokens (Lv 1→50)"):  "13",
            t("Medalhas Honor (HL 1→150)",    "Honor Medals (HL 1→150)"): f"{HONOR_MEDALS[rarity] * 150:,}",
            t("Tokens Honor (HL 1→150)",      "Honor Tokens (HL 1→150)"): "120",
        }
        st.table(pd.DataFrame(totals.items(), columns=["", "Value"]).set_index(""))

# ══════════════════════════════════════════════════════════════════════════════
# ABA 2 — PLANEJADOR DE LOTE
# ══════════════════════════════════════════════════════════════════════════════
with tab_plan:
    st.caption(t(
        "Monte um plano com múltiplas skins e veja o custo total consolidado de medalhas e tokens.",
        "Build a plan with multiple skins and see the total consolidated medal and token cost.",
    ))

    if "skin_plan" not in st.session_state:
        st.session_state["skin_plan"] = []

    # ── Formulário de entrada ──────────────────────────────────────────────────
    st.markdown("**➕ " + t("Adicionar skin ao plano", "Add skin to plan") + "**")

    sp1, sp2 = st.columns(2)
    with sp1:
        sp_rar_opts      = list(SKINS.keys())
        sp_rar_labels_pt = [t(RAR_PT[r], r) for r in sp_rar_opts]
        sp_rar_label     = st.selectbox(t("Raridade", "Rarity"), sp_rar_labels_pt, key="sp_rar")
        sp_rar = sp_rar_opts[sp_rar_labels_pt.index(sp_rar_label)]
    with sp2:
        sp_skin = st.selectbox(t("Skin", "Skin"), SKINS[sp_rar], key="sp_skin")

    sp3, sp4, sp5, sp6 = st.columns(4)
    sp_cur_lv = sp3.number_input(t("Nível atual", "Current level"), 1, 50, 1, key="sp_cur_lv")
    sp_tgt_lv = sp4.number_input(t("Nível alvo",  "Target level"),  1, 50, 50, key="sp_tgt_lv")
    sp_cur_hl = sp5.number_input(t("HL atual", "Current HL"), 0, 150, 0, key="sp_cur_hl")
    sp_tgt_hl = sp6.number_input(t("HL alvo",  "Target HL"),  0, 150, 0, key="sp_tgt_hl")

    if st.button("➕ " + t("Adicionar", "Add"), key="sp_add"):
        if sp_tgt_lv < sp_cur_lv:
            st.warning(t("⚠️ Nível alvo menor que o atual.", "⚠️ Target level is below current level."))
        else:
            sp_med_lv = max(0, cum_medals(sp_tgt_lv, sp_rar) - cum_medals(sp_cur_lv, sp_rar))
            sp_med_hl = honor_medals_needed(sp_cur_hl, sp_tgt_hl, sp_rar, 0)
            sp_tokens  = tokens_for_milestones(sp_cur_lv, sp_tgt_lv)
            st.session_state["skin_plan"].append({
                "rarity":  sp_rar,
                "skin":    sp_skin,
                "cur_lv":  sp_cur_lv,
                "tgt_lv":  sp_tgt_lv,
                "cur_hl":  sp_cur_hl,
                "tgt_hl":  sp_tgt_hl,
                "medals":  sp_med_lv + sp_med_hl,
                "tokens":  sp_tokens,
            })
            _skins_save()

    plan = st.session_state["skin_plan"]

    if not plan:
        st.info(t("Nenhuma skin no plano ainda. Adicione acima ↑", "No skins in plan yet. Add above ↑"))
    else:
        st.divider()

        # ── Tabela do plano ────────────────────────────────────────────────────
        _sr = t("Raridade", "Rarity")
        _ss = t("Skin", "Skin")
        _scl = t("Nív. Atual", "Cur. Lv")
        _stl = t("Nív. Alvo",  "Tgt. Lv")
        _shl = t("HL Atual", "Cur. HL")
        _sth = t("HL Alvo",  "Tgt. HL")
        _sm  = "🏅 " + t("Medalhas", "Medals")
        _stk = "🎟️ " + t("Tokens",   "Tokens")

        rows = [{
            _sr: t(RAR_PT[e["rarity"]], e["rarity"]),
            _ss: e["skin"],
            _scl: e["cur_lv"], _stl: e["tgt_lv"],
            _shl: e["cur_hl"], _sth: e["tgt_hl"],
            _sm: e["medals"],  _stk: e["tokens"],
        } for e in plan]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # ── Totais ─────────────────────────────────────────────────────────────
        total_medals = sum(e["medals"] for e in plan)
        st.markdown("**📊 " + t("Totais vs. estoque", "Totals vs. stock") + "**")

        tm1, tm2, tm3, tm4 = st.columns(4)
        med_miss = max(0, total_medals - medal_stock)
        with tm1:
            st.metric(t("🏅 Medalhas total", "🏅 Total Medals"), f"{total_medals:,}",
                      help=t(f"Estoque: {medal_stock:,}", f"Stock: {medal_stock:,}"))
            if med_miss > 0:
                st.error(t(f"❗ Faltam: {med_miss:,}", f"❗ Missing: {med_miss:,}"))
            else:
                st.success(t(f"✅ Saldo: {medal_stock - total_medals:,}", f"✅ Surplus: {medal_stock - total_medals:,}"))

        for col, rar in zip([tm2, tm3, tm4], ["Legendary", "Epic", "Rare"]):
            emoji = "🟡" if rar == "Legendary" else ("🟣" if rar == "Epic" else "🔵")
            total_tok_rar = sum(e["tokens"] for e in plan if e["rarity"] == rar)
            stock_rar = token_stock[rar]
            tok_miss  = max(0, total_tok_rar - stock_rar)
            with col:
                st.metric(f"{emoji} {t('Tokens', 'Tokens')} {t(RAR_PT[rar], rar)}", f"{total_tok_rar}",
                          help=t(f"Estoque: {stock_rar}", f"Stock: {stock_rar}"))
                if total_tok_rar == 0:
                    st.caption(t("Nenhuma skin desta raridade", "No skins of this rarity"))
                elif tok_miss > 0:
                    st.error(t(f"❗ Faltam: {tok_miss}", f"❗ Missing: {tok_miss}"))
                else:
                    st.success(t(f"✅ Saldo: {stock_rar - total_tok_rar}", f"✅ Surplus: {stock_rar - total_tok_rar}"))

        st.caption(t(
            "⚠️ Medalhas para Honor Level calculadas sem uso de tokens. "
            "Ajuste no calculador individual para usar tokens em HLs.",
            "⚠️ Honor Level medals calculated assuming no tokens used. "
            "Adjust in the individual calculator to allocate tokens to HLs.",
        ))

        # ── Impacto nos Eventos Regulares ─────────────────────────────────────
        st.divider()
        st.markdown("**📅 " + t("Impacto nos Eventos Regulares", "Regular Event Impact") + "**")

        ev_gear_p  = next(e for e in EVENTS if e["sheet"] == "Lord_Gear_Trial")
        ev_gpname  = ev_gear_p.get("name_pt", ev_gear_p["name"]) if lang == "pt" else ev_gear_p["name"]

        tot_rar_tok = sum(e["tokens"] for e in plan if e["rarity"] == "Rare")
        tot_epi_tok = sum(e["tokens"] for e in plan if e["rarity"] == "Epic")
        tot_leg_tok = sum(e["tokens"] for e in plan if e["rarity"] == "Legendary")

        pts_med_p  = total_medals / 200
        pts_rar_p  = tot_rar_tok * 30
        pts_epi_p  = tot_epi_tok * 300
        pts_leg_p  = tot_leg_tok * 3000
        pts_gear_p = pts_med_p + pts_rar_p + pts_epi_p + pts_leg_p

        esg1, esg2, esg3, esg4, esg5 = st.columns(5)
        esg1.metric(t("🏅 Medalhas", "🏅 Medals"),          f"{pts_med_p:,.1f} pts")
        esg2.metric(f"🔵 {t('Tokens Raros', 'Rare Tokens')}", f"{pts_rar_p:,.0f} pts")
        esg3.metric(f"🟣 {t('Tokens Épicos', 'Epic Tokens')}", f"{pts_epi_p:,.0f} pts")
        esg4.metric(f"🟡 {t('Tokens Lend.', 'Leg. Tokens')}",  f"{pts_leg_p:,.0f} pts")
        esg5.metric(f"📊 {ev_gpname}",                       f"{pts_gear_p:,.1f} pts")

        ms_icons_p2 = "  ".join(
            f"✅ {s['value']:,}" if s["reached"] else f"⬜ {s['value']:,}"
            for s in get_milestone_status(ev_gear_p["milestones"], pts_gear_p)
        )
        st.caption(f"Milestones: {ms_icons_p2}")

        if st.button("📅 " + t("Enviar para Eventos", "Send to Events"), key="send_skin_plan_evt"):
            st.session_state["_src_troop_skin_Lord_Gear_Trial"] = int(pts_gear_p)
            st.session_state["_calc_contrib_Lord_Gear_Trial_4"] = int(pts_rar_p)
            st.session_state["_calc_contrib_Lord_Gear_Trial_5"] = int(pts_epi_p)
            st.session_state["_calc_contrib_Lord_Gear_Trial_6"] = int(pts_leg_p)
            st.session_state["_calc_contrib_Lord_Gear_Trial_7"] = int(pts_med_p)
            st.session_state["_calc_sent_Lord_Gear_Trial"]      = True
            st.success(t(
                f"✅ {pts_gear_p:,.1f} pts enviados para **{ev_gpname}**! Acesse Eventos Regulares para ver.",
                f"✅ {pts_gear_p:,.1f} pts sent to **{ev_gpname}**! Go to Regular Events to see them.",
            ))

        st.divider()
        if st.button("🗑️ " + t("Limpar plano", "Clear plan"), key="sp_clear"):
            st.session_state["skin_plan"] = []
            st.session_state.pop("_src_troop_skin_Lord_Gear_Trial", None)
            st.session_state["_calc_sent_Lord_Gear_Trial"] = False
            for _k in [4, 5, 6, 7]:
                st.session_state.pop(f"_calc_contrib_Lord_Gear_Trial_{_k}", None)
            _skins_save()
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# ABA 3 — INSTRUÇÕES & REFERÊNCIA
# ══════════════════════════════════════════════════════════════════════════════
with tab_help:
    _hi1, _hi2 = st.tabs([
        "📖 " + t("Como usar", "How to use"),
        "📊 " + t("Referência de dados", "Data reference"),
    ])

    with _hi1:
        st.markdown(t(
            """
### Calculadora de Troop Skins — Como usar

**Inventário** (topo da página)
- **Medalhas**: moeda principal para evoluir skins de nível 1 a 50
- **Tokens** (Lendário / Épico / Raro): desbloqueiam milestones de estrelas (lvl 10, 20, 30, 40, 45, 50)
- **Cópias por Skin**: informe cópias específicas de cada skin — são somadas ao pool de tokens da mesma raridade

**Aba Calculadora**
1. Selecione a raridade e a skin
2. Configure nível atual e alvo (Nível, 1–50)
3. Configure Honor atual e alvo (HL, 0–150)
4. Veja custo em medalhas, tokens e impact em eventos

**Aba Planejador de Lote**
1. Adicione múltiplas skins com seus objetivos
2. Veja o custo total e compare com seu inventário

**Sistema de Tokens**
Tokens são necessários em milestones de nível: 10★, 20★★, 30★★★, 40★★★★, 45★★★★★, 50 MAX
""",
            """
### Troop Skin Calculator — How to use

**Inventory** (top of page)
- **Medals**: main currency to level skins from 1 to 50
- **Tokens** (Legendary / Epic / Rare): unlock star milestones (lvl 10, 20, 30, 40, 45, 50)
- **Skin-specific copies**: enter copies for individual skins — they're added to the token pool of the same rarity

**Calculator tab**
1. Select rarity and skin
2. Set current and target level (1–50)
3. Set current and target Honor (HL, 0–150)
4. See medal cost, token cost, and event impact

**Batch Planner tab**
1. Add multiple skins with their goals
2. See total cost and compare against your inventory

**Token system**
Tokens are required at level milestones: 10★, 20★★, 30★★★, 40★★★★, 45★★★★★, 50 MAX
""",
        ))

    with _hi2:
        _rc1, _rc2 = st.columns(2)
        with _rc1:
            st.subheader(t("🏅 Medalhas por Nível (Lendária)", "🏅 Medals per Level (Legendary)"))
            st.caption(t(
                "Custo cumulativo de medalhas para atingir cada nível (Lendária). "
                "Épica = ÷2, Rara = ÷4.",
                "Cumulative medal cost to reach each level (Legendary). "
                "Epic = ÷2, Rare = ÷4.",
            ))
            import pandas as _pd4
            _lev_rows = [{"LVL": _lv, t("Medalhas Acum.", "Medals Cum."): f"{LEG_CUM[_lv]:,}"}
                         for _lv in [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]]
            st.dataframe(_pd4.DataFrame(_lev_rows).set_index("LVL"), use_container_width=True)
        with _rc2:
            st.subheader(t("🎟️ Tokens por Milestone", "🎟️ Tokens per Milestone"))
            _tok_rows = [{"★": STAR_LABELS[_m], t("Nível", "Level"): _m,
                          t("Tokens (cumulativo)", "Tokens (cumulative)"): TOK_CUM[_m]}
                         for _m in MILESTONES]
            st.dataframe(_pd4.DataFrame(_tok_rows), use_container_width=True, hide_index=True)

