"""
pages/3_Pets.py — Pet Calculator page.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from pet_engine import (
    PETS, PROMO_LIST, TIER_TARGETS, TIER_RANK, FACTION_EMOJI,
    FOOD_AT_LEVEL, MAX_LEVEL,
    calc_milestone, calc_to_target, max_level_with_food, get_stats,
)

st.set_page_config(page_title="Pet Calculator", page_icon="🐾", layout="wide")

# ── Language ───────────────────────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "pt"

with st.sidebar:
    st.markdown("### 🌐 Idioma / Language")
    lang_pick = st.radio(
        "", ["🇧🇷 Português", "🇬🇧 English"],
        index=0 if st.session_state.lang == "pt" else 1,
        horizontal=True, label_visibility="collapsed", key="lang_pet",
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

lang = st.session_state.lang
def t(pt, en): return pt if lang == "pt" else en

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🐾 " + t("Calculadora de Pets", "Pet Calculator"))
st.caption(t(
    "Calcula recursos necessários para evoluir e promover seus pets.",
    "Calculates resources needed to level up and promote your pets.",
))

_FS = {True: t("★ Exclusivo da Facção", "★ Faction-Specific"),
       False: t("Universal", "Universal"),
       None: "—"}

# ── RECURSOS ──────────────────────────────────────────────────────────────────
st.subheader("📦 " + t("Recursos", "Resources"))
rc1, rc2, rc3 = st.columns(3)
with rc1:
    inv_food = st.number_input(t("🍗 Pet Food", "🍗 Pet Food"),
                                min_value=0, value=0, step=1000, key="pet_food")
with rc2:
    inv_ess = st.number_input(t("💎 Pet Essence", "💎 Pet Essence"),
                               min_value=0, value=0, step=100, key="pet_ess")
with rc3:
    inv_box = st.number_input(t("🎁 Rare Pet Choice Box", "🎁 Rare Pet Choice Box"),
                               min_value=0, value=0, step=1, key="pet_box")

# ── INVENTÁRIO ─────────────────────────────────────────────────────────────────
st.divider()
st.subheader("🐣 " + t("Inventário de Pets", "Pet Inventory"))
st.caption(t(
    "Informe quantas cópias de cada pet você possui. "
    "Marque 'Excluir de Qualquer?' para pets que não quer usar como qualquer pet.",
    "Enter how many copies of each pet you own. "
    "Check 'Exclude from Any?' for pets you don't want counted as universal copies.",
))

_col_pet  = t("Pet", "Pet")
_col_fac  = t("Facção", "Faction")
_col_type = t("Tipo", "Type")
_col_cop  = t("Cópias", "Copies (same)")
_col_exc  = t("Excluir de Qualquer?", "Exclude from Any pet?")
_col_sk   = t("Habilidade Ativa", "Active Skill")
_col_pas  = t("Passiva", "Passive")

inv_rows = []
for name, faction, fs, skill, passive in PETS:
    inv_rows.append({
        _col_pet:  f"{FACTION_EMOJI[faction]} {name}",
        _col_fac:  faction,
        _col_type: _FS[fs],
        _col_cop:  0,
        _col_exc:  False,
        _col_sk:   skill,
        _col_pas:  passive,
    })

edited_inv = st.data_editor(
    pd.DataFrame(inv_rows),
    use_container_width=True,
    hide_index=True,
    disabled=[_col_pet, _col_fac, _col_type, _col_sk, _col_pas],
    column_config={
        _col_cop: st.column_config.NumberColumn(min_value=0, step=1),
        _col_exc: st.column_config.CheckboxColumn(),
    },
    key="pet_inv_table",
)

inv_copies  = {PETS[i][0]: int(edited_inv.iloc[i][_col_cop]) for i in range(len(PETS))}
inv_exclude = {PETS[i][0]: bool(edited_inv.iloc[i][_col_exc]) for i in range(len(PETS))}

# ── CALCULADORA ────────────────────────────────────────────────────────────────
st.divider()
st.subheader("🧮 " + t("Calculadora", "Calculator"))

pet_names    = [p[0] for p in PETS]
promo_labels = [p[1] for p in PROMO_LIST]
promo_data   = {p[1]: p for p in PROMO_LIST}  # label -> full tuple

cc1, cc2, cc3, cc4 = st.columns([2, 2, 1, 1])
with cc1:
    selected_pet = st.selectbox(t("Pet selecionado", "Selected pet"), pet_names, key="calc_pet")
with cc2:
    current_promo_lbl = st.selectbox(t("Promoção atual", "Current promotion"),
                                      promo_labels, key="calc_promo")
with cc3:
    current_level = st.number_input(t("Nível atual", "Current level"),
                                     min_value=1, max_value=MAX_LEVEL, value=1, key="calc_lvl")
with cc4:
    use_boxes = st.checkbox(t("Usar Choice Boxes?", "Use Choice Boxes?"),
                             value=True, key="calc_boxes")

promo_min_lvl, _, promo_tier, _, _ = promo_data[current_promo_lbl]
promo_rank = TIER_RANK[promo_tier]

if current_level < promo_min_lvl:
    st.warning(t(
        f"⚠️ Nível {current_level} está abaixo do mínimo para a promoção selecionada (mín. {promo_min_lvl}).",
        f"⚠️ Level {current_level} is below the minimum for the selected promotion (min. {promo_min_lvl}).",
    ))

pet_info = next(p for p in PETS if p[0] == selected_pet)
_, pet_faction, pet_fs, pet_skill, pet_passive = pet_info

# Copies for selected pet (same copies + choice boxes if enabled)
inv_same_selected = inv_copies[selected_pet] + (inv_box if use_boxes else 0)

# Total "any" copies: all pets except selected pet, excluding marked ones
total_any = sum(
    inv_copies[name]
    for name, *_ in PETS
    if name != selected_pet and not inv_exclude[name]
)

# Pet info card
ic1, ic2 = st.columns([1, 3])
with ic1:
    st.metric(t("Facção", "Faction"), f"{FACTION_EMOJI[pet_faction]} {pet_faction}")
    st.metric(t("Tipo", "Type"), _FS[pet_fs])
with ic2:
    if pet_skill != "—":
        st.markdown(f"**🎯 {t('Habilidade Ativa','Active Skill')}:** {pet_skill}")
    if pet_passive != "—":
        st.markdown(f"**⚡ {t('Passiva','Passive')}:** {pet_passive}")

max_lvl = max_level_with_food(current_level, inv_food)
if max_lvl > current_level:
    st.info(t(
        f"🍗 Com seu estoque de comida, pode chegar até o nível **{max_lvl}**.",
        f"🍗 With your food stock, you can reach level **{max_lvl}**.",
    ))
else:
    st.info(t(
        f"🍗 Sem comida suficiente para subir além do nível atual ({current_level}).",
        f"🍗 Not enough food to level up beyond current level ({current_level}).",
    ) if inv_food == 0 else t(
        f"🍗 Com sua comida atual, pode chegar ao nível **{max_lvl}**.",
        f"🍗 With your current food, you can reach level **{max_lvl}**.",
    ))

# ── MARCOS DE TIER ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("**📌 " + t("Marcos de Tier — recursos restantes", "Tier Milestones — remaining resources") + "**")
st.caption(t(
    "Quanto ainda falta a partir do seu estado atual para atingir cada tier.",
    "How much you still need from your current state to reach each tier.",
))

tier_cfgs = [
    ("EPIC",      "⚔️ EPIC ☆",      1),
    ("LEGENDARY", "👑 LEGENDARY ☆",  2),
    ("MYTHIC",    "💀 MYTHIC",       3),
]

t_cols = st.columns(3)
for (tier, label, rank), col in zip(tier_cfgs, t_cols):
    reached     = promo_rank >= rank
    in_progress = promo_rank == rank - 1
    status = ("✅ " + t("Alcançado", "Reached") if reached
               else "🔜 " + t("Em progresso", "In progress") if in_progress
               else "🔒 " + t("Bloqueado", "Locked"))

    with col:
        st.markdown(f"**{label}**")
        st.caption(status)
        if reached:
            st.success(t("Tier já alcançado!", "Tier already reached!"))
        else:
            ms = calc_milestone(
                tier, current_level, promo_min_lvl, current_promo_lbl,
                inv_food, inv_ess, inv_same_selected, total_any,
            )
            st.metric(t("🍗 Comida", "🍗 Food"),          f"{ms['food']:,}")
            st.metric(f"📦 {selected_pet}", f"{ms['same']:,}")
            st.metric(t("🎲 Qualquer pet", "🎲 Any pet"),   f"{ms['any']:,}")
            if ms["essence"] > 0:
                st.metric(t("💎 Essência", "💎 Essence"), f"{ms['essence']:,}")

# ── NÍVEL ALVO (OPCIONAL) ──────────────────────────────────────────────────────
st.markdown("---")
st.markdown("**🎯 " + t("Nível alvo (opcional)", "Target level (optional)") + "**")

tgt_col, _ = st.columns([1, 3])
with tgt_col:
    target_level = st.number_input(
        t("Nível alvo", "Target level"),
        min_value=1, max_value=MAX_LEVEL,
        value=min(current_level + 10, MAX_LEVEL),
        key="calc_tgt",
    )

if target_level > current_level:
    res = calc_to_target(current_level, target_level)
    tm1, tm2, tm3, tm4 = st.columns(4)
    tm1.metric(t("🍗 Comida",         "🍗 Food"),         f"{res['food']:,}")
    tm2.metric(t("💎 Essência",        "💎 Essence"),      f"{res['essence']:,}" if res["essence"] else "—")
    tm3.metric(f"📦 {selected_pet}",                        f"{res['same']:,}"    if res["same"]    else "—")
    tm4.metric(t("🎲 Qualquer pet",    "🎲 Any pet"),   f"{res['any']:,}"     if res["any"]     else "—")
elif target_level == current_level:
    st.info(t("Selecione um nível alvo maior que o atual.", "Select a target level higher than current."))

# ── ESTATÍSTICAS ───────────────────────────────────────────────────────────────
with st.expander(t("📊 Estatísticas no nível atual", "📊 Stats at current level")):
    conv, atku, atkf, hpu, hpf, lcap = get_stats(current_level)
    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("Conv. Rate",                    f"{conv:.2f}")
    s2.metric(t("Atk% (Universal)",  "Atk% (Universal)"),  atku)
    s3.metric(t("Atk% (Facção)",     "Atk% (Faction)"),    atkf)
    s4.metric(t("HP% (Universal)",   "HP% (Universal)"),   hpu)
    s5.metric(t("HP% (Facção)",      "HP% (Faction)"),     hpf)
    st.caption(t(f"Level cap de habilidade: {lcap}", f"Skill level cap: {lcap}"))
