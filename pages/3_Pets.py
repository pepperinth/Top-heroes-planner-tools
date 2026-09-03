"""
pages/3_Pets.py — Pet Calculator page.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from pet_engine import (
    PETS, PET_FLAGS, PROMO_LIST, TIER_RANK, PROMO_INDEX, FACTION_EMOJI,
    MAX_LEVEL, TIER_MIN_LEVEL, TIER_TARGET_PROMO_LABEL,
    FOOD_AT_LEVEL, ESS_AT_LEVEL, promo_cum,
    calc_milestone, calc_to_target, calc_to_promo, max_level_with_food, get_stats,
    calc_rebirth, REBIRTH_BOX_PETS,
)
from events_data import EVENTS, get_milestone_status
from behemoth_engine import FACTION_ICONS, FACTION_ICON_DIR
from ui_utils import inject_global_css, section_header, FACTION_COLORS, RARITY_COLORS
import persistence

_BASE = os.path.dirname(os.path.dirname(__file__))

# English pet faction → Portuguese icon key
_FACTION_KEY = {"League": "Liga", "Horde": "Horda", "Nature": "Natureza"}
# Portuguese display names (All = cross-faction)
_FACTION_PT  = {"League": "Liga", "Horde": "Horda", "Nature": "Natureza", "All": "Qualquer"}

def _faction_icon(faction_en: str, width: int = 32):
    if faction_en not in _FACTION_KEY:
        return   # cross-faction pets have no single icon
    path = os.path.join(_BASE, FACTION_ICON_DIR, FACTION_ICONS[_FACTION_KEY[faction_en]])
    st.image(path, width=width)

st.set_page_config(page_title="Pet Calculator", page_icon="🐾", layout="wide")

# ── Persistence ────────────────────────────────────────────────────────────────
_cm = persistence.new_manager("pets")

if "pet_initialized" not in st.session_state:
    _saved = persistence.load(_cm, "th_pets")
    if _saved:
        st.session_state["pet_food"]       = int(_saved.get("pet_food", 0))
        st.session_state["pet_ess"]        = int(_saved.get("pet_ess", 0))
        st.session_state["pet_box"]        = int(_saved.get("pet_box", 0))
        st.session_state["inv_common_pet"] = int(_saved.get("inv_common_pet", 0))
        if "pet_plan" in _saved:
            st.session_state["pet_plan"] = _saved["pet_plan"]
        if "pet_inv_table" in _saved:
            st.session_state["pet_inv_table"] = _saved["pet_inv_table"]
    st.session_state["pet_initialized"] = True


def _pets_save():
    persistence.save(_cm, "th_pets", {
        "pet_food":       st.session_state.get("pet_food", 0),
        "pet_ess":        st.session_state.get("pet_ess", 0),
        "pet_box":        st.session_state.get("pet_box", 0),
        "inv_common_pet": st.session_state.get("inv_common_pet", 0),
        "pet_plan":       st.session_state.get("pet_plan", []),
        "pet_inv_table":  st.session_state.get("pet_inv_table", {}),
    })


# ── Language ───────────────────────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "en"

with st.sidebar:
    st.markdown("### 🌐 Idioma / Language")
    lang_pick = st.radio(
        "", ["🇧🇷 Português", "🇬🇧 English"],
        index=0 if st.session_state.lang == "pt" else 1,
        horizontal=True, label_visibility="collapsed", key="lang_pet",
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

_PROMO_PT = {"RARE": "RARO", "EPIC": "ÉPICO", "LEGENDARY": "LENDÁRIO", "MYTHIC": "MÍTICO"}
def tpromo(lbl: str) -> str:
    if lang != "pt":
        return lbl
    for en, pt in _PROMO_PT.items():
        lbl = lbl.replace(en, pt)
    return lbl

_FS = {True: t("★ Exclusivo da Facção", "★ Faction-Specific"),
       False: t("Universal", "Universal"),
       None: "—"}

# ── Header ─────────────────────────────────────────────────────────────────────
inject_global_css()
st.title("🐾 " + t("Calculadora de Pets", "Pet Calculator"))
st.caption(t(
    "Calcula recursos necessários para evoluir e promover seus pets.",
    "Calculates resources needed to level up and promote your pets.",
))

# ── RECURSOS (compartilhado entre abas) ───────────────────────────────────────
st.subheader("📦 " + t("Recursos", "Resources"))
rc1, rc2, rc3, rc4 = st.columns(4)
with rc1:
    inv_food = st.number_input(t("🍗 Ração de Pet", "🍗 Pet Food"),
                                min_value=0, value=0, step=1000, key="pet_food",
                                on_change=_pets_save)
with rc2:
    inv_ess = st.number_input(t("💎 Essência de Pet", "💎 Pet Essence"),
                               min_value=0, value=0, step=100, key="pet_ess",
                               on_change=_pets_save)
with rc3:
    inv_box = st.number_input(t("🎁 Caixa de Pet Raro (escolha)", "🎁 Rare Pet Choice Box"),
                               min_value=0, value=0, step=1, key="pet_box",
                               on_change=_pets_save)
with rc4:
    inv_common = st.number_input(
        t("🐾 Pets Comuns", "🐾 Common Pets"),
        min_value=0, value=0, step=1, key="inv_common_pet",
        on_change=_pets_save,
        help=t(
            "Cópias de pets Comuns para usar como material de EXP.",
            "Common pet copies to use as EXP material.",
        ),
    )

# ── INVENTÁRIO DE PETS (compartilhado entre abas) ──────────────────────────────
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
_col_cop  = t("Cópias", "Copies")
_col_exc  = t("Excluir de Qualquer?", "Exclude from Any pet?")
_col_sk   = t("Habilidade Ativa", "Active Skill")
_col_pas  = t("Passiva", "Passive")

inv_rows = []
for name, faction, fs, skill, passive in PETS:
    inv_rows.append({
        _col_pet:  f"{FACTION_EMOJI[faction]} {name}",
        _col_fac:  _FACTION_PT[faction] if lang == "pt" else faction,
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
    on_change=_pets_save,
)

_safe_cop = edited_inv[_col_cop].fillna(0)
_safe_exc = edited_inv[_col_exc].fillna(False)
inv_copies  = {PETS[i][0]: int(_safe_cop.iloc[i])  for i in range(len(PETS))}
inv_exclude = {PETS[i][0]: bool(_safe_exc.iloc[i]) for i in range(len(PETS))}

# Total "any" disponível (sem exclusões + choice boxes)
total_any_inv = sum(
    inv_copies[name] for name, *_ in PETS if not inv_exclude[name]
) + inv_box

# ── ABAS ───────────────────────────────────────────────────────────────────────
st.divider()
tab_calc, tab_plan, tab_rebirth, tab_help = st.tabs([
    "🧮 " + t("Calculadora", "Calculator"),
    "📋 " + t("Planejador de Lote", "Batch Planner"),
    "🔄 " + t("Renascimento", "Rebirth"),
    "📖 " + t("Instruções & Referência", "Instructions & Reference"),
])

pet_names    = [p[0] for p in PETS]
promo_labels = [p[1] for p in PROMO_LIST]
promo_data   = {p[1]: p for p in PROMO_LIST}

# ══════════════════════════════════════════════════════════════════════════════
# ABA 1 — CALCULADORA
# ══════════════════════════════════════════════════════════════════════════════
with tab_calc:
    cc1, cc2, cc3, cc4 = st.columns([2, 2, 1, 1])
    with cc1:
        selected_pet = st.selectbox(t("Pet selecionado", "Selected pet"), pet_names, key="calc_pet")
    with cc2:
        current_promo_lbl = st.selectbox(t("Promoção atual", "Current promotion"),
                                          promo_labels, key="calc_promo",
                                          format_func=tpromo)
    with cc3:
        current_level = st.number_input(t("Nível atual", "Current level"),
                                         min_value=1, max_value=MAX_LEVEL, value=1, key="calc_lvl")
    with cc4:
        use_boxes = st.checkbox(t("Usar Choice Boxes?", "Use Choice Boxes?"),
                                 value=True, key="calc_boxes")

    _higher_promos = [p[1] for p in PROMO_LIST
                      if PROMO_INDEX[p[1]] > PROMO_INDEX[current_promo_lbl]]
    _tpr_col, _ = st.columns([2, 4])
    with _tpr_col:
        if _higher_promos:
            target_promo_lbl = st.selectbox(
                t("⭐ Promoção alvo", "⭐ Target promotion"),
                _higher_promos, key="calc_tgt_promo",
                format_func=tpromo,
            )
        else:
            target_promo_lbl = None
            st.success(t("✅ Promoção máxima alcançada!", "✅ Maximum promotion reached!"))

    promo_min_lvl, _, promo_tier, _, _, _ = promo_data[current_promo_lbl]
    promo_rank = TIER_RANK[promo_tier]

    if current_level < promo_min_lvl:
        st.warning(t(
            f"⚠️ Nível {current_level} está abaixo do mínimo para a promoção selecionada (mín. {promo_min_lvl}).",
            f"⚠️ Level {current_level} is below the minimum for the selected promotion (min. {promo_min_lvl}).",
        ))

    pet_info = next(p for p in PETS if p[0] == selected_pet)
    _, pet_faction, pet_fs, pet_skill, pet_passive = pet_info
    _pet_flags = PET_FLAGS.get(selected_pet, set())
    _any_promo = "any_promo" in _pet_flags

    # For any_promo pets: copies of this pet count as "any"; choice boxes don't apply
    if _any_promo:
        inv_same_selected = 0
        total_any = sum(
            inv_copies[name] for name, *_ in PETS if not inv_exclude[name]
        )  # includes selected pet itself — all count as any
    else:
        inv_same_selected = inv_copies[selected_pet] + (inv_box if use_boxes else 0)
        total_any = sum(
            inv_copies[name] for name, *_ in PETS
            if name != selected_pet and not inv_exclude[name]
        )

    ic1, ic2 = st.columns([1, 3])
    with ic1:
        _faction_icon(pet_faction, width=32)
        faction_disp = _FACTION_PT[pet_faction] if lang == "pt" else pet_faction
        st.caption(f"**{t('Facção','Faction')}:** {faction_disp}")
        st.caption(f"**{t('Tipo','Type')}:** {_FS[pet_fs]}")
    if "no_choice_box" in _pet_flags:
        st.info(t(
            "ℹ️ **Dart** não está disponível em Caixas de Escolha de Pet Raro.",
            "ℹ️ **Dart** is not available from Rare Pet Choice Boxes.",
        ))
    if _any_promo:
        st.info(t(
            "🌐 **Dart** aceita qualquer pet como cópia de promoção — não há requisito de cópia específica.",
            "🌐 **Dart** accepts any pet as a promotion copy — no same-pet requirement.",
        ))
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

    if target_promo_lbl:
        st.markdown("---")
        _tgt_entry = next(p for p in PROMO_LIST if p[1] == target_promo_lbl)
        _tgt_fc = FACTION_COLORS.get(_FACTION_KEY.get(pet_faction, "Liga"), "#5C3D1E")
        st.markdown(
            f'<div style="border-left:5px solid {_tgt_fc};padding:5px 14px;'
            f'border-radius:0 8px 8px 0;background:{_tgt_fc}14;font-weight:700;margin:8px 0 6px;">'
            f'🎯 {t("Recursos para atingir", "Resources to reach")} {tpromo(target_promo_lbl)} '
            f'({t("nível mín.", "min. level")} {_tgt_entry[0]})</div>',
            unsafe_allow_html=True,
        )
        _res_promo = calc_to_promo(
            target_promo_lbl, current_level, current_promo_lbl,
            inv_food, inv_ess, inv_same_selected, total_any,
            any_promo=_any_promo,
        )
        _pm1, _pm2, _pm3, _pm4 = st.columns(4)
        _pm1.metric(t("🍗 Comida", "🍗 Food"),          f"{_res_promo['food']:,}")
        _pm2.metric(t("💎 Essência", "💎 Essence"),       f"{_res_promo['essence']:,}" if _res_promo['essence'] else "—")
        _pm3.metric(f"📦 {selected_pet}",                f"{_res_promo['same']:,}"    if _res_promo['same']    else "—")
        _pm4.metric(t("🎲 Qualquer pet", "🎲 Any pet"),  f"{_res_promo['any']:,}"     if _res_promo['any']     else "—")
        if current_level < _tgt_entry[0]:
            st.caption(t(
                f"⚠️ Nível mínimo para {tpromo(target_promo_lbl)}: **{_tgt_entry[0]}** (atual: {current_level})",
                f"⚠️ Minimum level for {target_promo_lbl}: **{_tgt_entry[0]}** (current: {current_level})",
            ))

        with st.expander(t("📋 Custo por passo de promoção", "📋 Cost per promotion step")):
            _step_rows = []
            for _p in PROMO_LIST:
                if (PROMO_INDEX[_p[1]] > PROMO_INDEX[current_promo_lbl]
                        and PROMO_INDEX[_p[1]] <= PROMO_INDEX[target_promo_lbl]):
                    _step_rows.append({
                        t("Promoção", "Promotion"):               tpromo(_p[1]),
                        t("Nível mín.", "Min Lvl"):               _p[0],
                        f"📦 {selected_pet}":                     _p[3] if _p[3] else "—",
                        t("🎲 Qualquer pet", "🎲 Any pet"):       _p[4] if _p[4] else "—",
                        t("💎 Essência promoção", "💎 Promo Ess"): _p[5] if _p[5] else "—",
                    })
            if _step_rows:
                st.dataframe(pd.DataFrame(_step_rows), use_container_width=True, hide_index=True)
                st.caption(t(
                    "Valores por linha = custo individual para atingir aquela promoção a partir da anterior. "
                    "O total acima já desconta seu inventário atual.",
                    "Values per row = individual cost to reach that promotion from the previous one. "
                    "The totals above already subtract your current inventory.",
                ))

    st.markdown("---")
    _pet_fc = FACTION_COLORS.get(_FACTION_KEY.get(pet_faction, "Liga"), "#5C3D1E")
    st.markdown(
        f'<div style="border-left:5px solid {_pet_fc};padding:5px 14px;'
        f'border-radius:0 8px 8px 0;background:{_pet_fc}14;font-weight:700;margin:8px 0 6px;">'
        f'📌 {t("Marcos de Tier","Tier Milestones")}</div>',
        unsafe_allow_html=True,
    )
    st.caption(t(
        "Custo total de promoções a partir do estado atual. Expanda cada tier para ver o detalhamento por passo.",
        "Total promotion cost from your current state. Expand each tier to see the per-step breakdown.",
    ))

    tier_cfgs = [
        ("EPIC",      f"⚔️ {tpromo('EPIC ☆')} (lv {TIER_MIN_LEVEL['EPIC']})",           1),
        ("LEGENDARY", f"👑 {tpromo('LEGENDARY ☆')} (lv {TIER_MIN_LEVEL['LEGENDARY']})", 2),
        ("MYTHIC",    f"💀 {tpromo('MYTHIC')} (lv {TIER_MIN_LEVEL['MYTHIC']})",         3),
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
                target_label  = TIER_TARGET_PROMO_LABEL[tier]
                tgt_same_cum, tgt_any_cum, tgt_promo_ess_cum = promo_cum(target_label)
                cur_same_cum, cur_any_cum, cur_promo_ess_cum = promo_cum(current_promo_lbl)
                tgt_min_lvl   = TIER_MIN_LEVEL[tier]

                # Gross cost from current state to this milestone (no inventory deducted)
                need_food = max(0, FOOD_AT_LEVEL.get(tgt_min_lvl, 0) - FOOD_AT_LEVEL.get(current_level, 0))
                need_ess  = max(0,
                    (ESS_AT_LEVEL.get(tgt_min_lvl, 0) - ESS_AT_LEVEL.get(current_level, 0))
                    + (tgt_promo_ess_cum - cur_promo_ess_cum))
                if _any_promo:
                    need_same = 0
                    need_any  = max(0, (tgt_any_cum - cur_any_cum) + (tgt_same_cum - cur_same_cum))
                    have_any  = total_any  # total_any already includes all copies of Dart
                    surplus_same = 0
                else:
                    need_same    = max(0, tgt_same_cum - cur_same_cum)
                    need_any     = max(0, tgt_any_cum  - cur_any_cum)
                    surplus_same = max(0, inv_same_selected - need_same)
                    have_any     = total_any + surplus_same

                _cr = t("Recurso", "Resource")
                _cn = t("Necessário", "Need")
                _ch = t("Tenho", "Have")
                _cm = t("Falta", "Missing")

                _rows = [
                    {_cr: t("🍗 Food", "🍗 Food"),
                     _cn: f"{need_food:,}",
                     _ch: f"{inv_food:,}",
                     _cm: f"{max(0, need_food - inv_food):,}"},
                ]
                if not _any_promo:
                    _rows.append({_cr: f"📦 {selected_pet}",
                                  _cn: f"{need_same:,}",
                                  _ch: f"{inv_same_selected:,}",
                                  _cm: f"{max(0, need_same - inv_same_selected):,}"})
                _rows += [
                    {_cr: t("🎲 Any pet", "🎲 Any pet"),
                     _cn: f"{need_any:,}",
                     _ch: f"{have_any:,}",
                     _cm: f"{max(0, need_any - have_any):,}"},
                ]
                if need_ess > 0:
                    _rows.append({
                        _cr: t("💎 Essence", "💎 Essence"),
                        _cn: f"{need_ess:,}",
                        _ch: f"{inv_ess:,}",
                        _cm: f"{max(0, need_ess - inv_ess):,}",
                    })
                st.dataframe(pd.DataFrame(_rows), use_container_width=True, hide_index=True)

                # ── Per-step breakdown expander (Proposta C) ──────────────────
                _steps = [p for p in PROMO_LIST
                          if PROMO_INDEX[p[1]] > PROMO_INDEX[current_promo_lbl]
                          and PROMO_INDEX[p[1]] <= PROMO_INDEX[target_label]]
                with st.expander(t("📋 Ver por passo de promoção", "📋 View per promotion step")):
                    _sr = []
                    for _p in _steps:
                        _sr.append({
                            t("Promoção", "Promotion"):         _p[1],
                            t("Lv", "Lv"):                      _p[0],
                            f"📦 {selected_pet}":               _p[3] if _p[3] else "—",
                            t("🎲 Qualquer", "🎲 Any"):         _p[4] if _p[4] else "—",
                            t("💎 Ess. promo", "💎 Promo Ess"): _p[5] if _p[5] else "—",
                        })
                    st.dataframe(pd.DataFrame(_sr), use_container_width=True, hide_index=True)

                    _tot_same = sum(p[3] for p in _steps)
                    _tot_any  = sum(p[4] for p in _steps)
                    _tot_ess  = sum(p[5] for p in _steps)
                    st.caption(
                        t("**Total bruto:**", "**Gross total:**") + f" "
                        f"{_tot_same} {selected_pet} · {_tot_any} any"
                        + (f" · {_tot_ess:,} {t('ess. promo','promo ess.')}" if _tot_ess else "")
                    )
                    if surplus_same:
                        st.caption(t(
                            f"ℹ️ {surplus_same} {selected_pet} excedentes contados como any.",
                            f"ℹ️ {surplus_same} surplus {selected_pet} counted as any.",
                        ))

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
        tm1.metric(t("🍗 Comida",      "🍗 Food"),     f"{res['food']:,}")
        tm2.metric(t("💎 Essência",    "💎 Essence"),   f"{res['essence']:,}" if res["essence"] else "—")
        tm3.metric(f"📦 {selected_pet}",                f"{res['same']:,}"    if res["same"]    else "—")
        tm4.metric(t("🎲 Qualquer pet","🎲 Any pet"),   f"{res['any']:,}"     if res["any"]     else "—")
    elif target_level == current_level:
        st.info(t("Selecione um nível alvo maior que o atual.", "Select a target level higher than current."))

    with st.expander(t("📊 Estatísticas no nível atual", "📊 Stats at current level")):
        conv, atku, atkf, hpu, hpf, lcap = get_stats(current_level)
        s1, s2, s3, s4, s5 = st.columns(5)
        s1.metric("Conv. Rate",                   f"{conv:.2f}")
        s2.metric(t("Atk% (Universal)", "Atk% (Universal)"), atku)
        s3.metric(t("Atk% (Facção)",    "Atk% (Faction)"),   atkf)
        s4.metric(t("HP% (Universal)",  "HP% (Universal)"),  hpu)
        s5.metric(t("HP% (Facção)",     "HP% (Faction)"),    hpf)
        st.caption(t(f"Level cap de habilidade: {lcap}", f"Skill level cap: {lcap}"))

    # ── Impacto nos Eventos Regulares ─────────────────────────────────────────
    st.markdown("---")
    st.markdown("**📅 " + t("Impacto nos Eventos Regulares", "Regular Event Impact") + "**")

    unreached = [(tier, label) for tier, label, rank in tier_cfgs if promo_rank < rank]
    if not unreached:
        st.info(t("✅ Todos os tiers já foram alcançados!", "✅ All tiers have already been reached!"))
    else:
        tier_opts   = [label for _, label in unreached]
        sel_label   = st.selectbox(
            t("Calcular impacto para o tier:", "Calculate impact for tier:"),
            tier_opts, key="calc_evt_tier",
        )
        sel_tier = next(tier for tier, label in unreached if label == sel_label)

        # Gross cost from current state to milestone (resources that will actually be SPENT)
        ms_g = calc_milestone(sel_tier, current_level, current_promo_lbl, 0, 0, 0, 0)

        ev_pet_c  = next(e for e in EVENTS if e["sheet"] == "Pet_Ranking")
        ev_pcname = ev_pet_c.get("name_pt", ev_pet_c["name"]) if lang == "pt" else ev_pet_c["name"]

        tot_rare_c   = ms_g["same"] + ms_g["any"]
        pts_food_c   = ms_g["food"]    * 0.3
        pts_ess_c    = ms_g["essence"] * 15
        pts_rare_c   = tot_rare_c      * 900
        pts_common_c = inv_common      * 150
        pts_evt_c    = pts_food_c + pts_ess_c + pts_rare_c + pts_common_c

        st.caption(t(
            f"Recursos gastos ao promover **{selected_pet}** de **{tpromo(current_promo_lbl)}** "
            f"(lv {current_level}) até **{sel_label}** e os pontos gerados no evento:",
            f"Resources spent promoting **{selected_pet}** from **{current_promo_lbl}** "
            f"(lv {current_level}) to **{sel_label}**, and the event points they generate:",
        ))

        _es = t("Fonte do gasto", "What's spent")
        _eq = t("Qtd gasta", "Amount spent")
        _er = t("Taxa", "Rate")
        _ep = t("Pontos", "Points")

        _evt_rows = []
        if ms_g["food"] > 0:
            _evt_rows.append({
                _es: t("🍗 Pet Food (subir de nível até o mín. do tier)", "🍗 Pet Food (leveling up to tier min. level)"),
                _eq: f"{ms_g['food']:,}",
                _er: "× 0.3",
                _ep: f"{pts_food_c:,.0f}",
            })
        if ms_g["essence"] > 0:
            _evt_rows.append({
                _es: t("💎 Pet Essence (custo das promoções LEGENDARY+)", "💎 Pet Essence (LEGENDARY+ promotion cost)"),
                _eq: f"{ms_g['essence']:,}",
                _er: "× 15",
                _ep: f"{pts_ess_c:,.0f}",
            })
        if tot_rare_c > 0:
            _evt_rows.append({
                _es: t(
                    f"🐾 Cópias Raras usadas nas promoções "
                    f"({ms_g['same']} {selected_pet} + {ms_g['any']} any)",
                    f"🐾 Rare copies used in promotions "
                    f"({ms_g['same']} {selected_pet} + {ms_g['any']} any)",
                ),
                _eq: f"{tot_rare_c:,}",
                _er: "× 900",
                _ep: f"{pts_rare_c:,.0f}",
            })
        _evt_rows.append({
            _es: t(
                f"🐾 Pets Comuns do inventário (usados como material de EXP)",
                f"🐾 Common pets from inventory (used as EXP material)",
            ),
            _eq: f"{inv_common:,}",
            _er: "× 150",
            _ep: f"{pts_common_c:,.0f}",
        })

        st.dataframe(pd.DataFrame(_evt_rows), use_container_width=True, hide_index=True)

        _tot_col, _ = st.columns([1, 2])
        with _tot_col:
            st.metric(f"📊 {t('Total de pontos','Total points')} — {ev_pcname}", f"{pts_evt_c:,.0f}")

        ms_icons_c2 = "  ".join(
            f"✅ {s['value']:,}" if s["reached"] else f"⬜ {s['value']:,}"
            for s in get_milestone_status(ev_pet_c["milestones"], pts_evt_c)
        )
        st.caption(f"Milestones: {ms_icons_c2}")

        if st.button("📅 " + t("Enviar para Eventos", "Send to Events"), key="send_pet_calc_evt"):
            st.session_state["_pts_to_send_Pet_Ranking"]    = int(pts_evt_c)
            st.session_state["_calc_contrib_Pet_Ranking_1"] = int(pts_ess_c)
            st.session_state["_calc_contrib_Pet_Ranking_2"] = int(pts_food_c)
            st.session_state["_calc_contrib_Pet_Ranking_3"] = int(pts_common_c)
            st.session_state["_calc_contrib_Pet_Ranking_4"] = int(pts_rare_c)
            st.session_state["_calc_sent_Pet_Ranking"]      = True
            st.success(t(
                f"✅ {pts_evt_c:,.0f} pts enviados para **{ev_pcname}**! Acesse Eventos Regulares para ver.",
                f"✅ {pts_evt_c:,.0f} pts sent to **{ev_pcname}**! Go to Regular Events to see them.",
            ))

# ══════════════════════════════════════════════════════════════════════════════
# ABA 2 — PLANEJADOR DE LOTE
# ══════════════════════════════════════════════════════════════════════════════
with tab_plan:
    st.caption(t(
        "Monte um plano com múltiplos pets e veja o custo total consolidado de recursos.",
        "Build a plan with multiple pets and see the total consolidated resource cost.",
    ))

    if "pet_plan" not in st.session_state:
        st.session_state["pet_plan"] = []

    # ── Formulário de entrada ──────────────────────────────────────────────────
    st.markdown("**➕ " + t("Adicionar pet ao plano", "Add pet to plan") + "**")
    bp1, bp2, bp3, bp4, bp5 = st.columns([2, 2, 1, 1, 1])
    with bp1:
        bp_pet = st.selectbox(t("Pet", "Pet"), pet_names, key="bp_pet")
    with bp2:
        bp_promo = st.selectbox(t("Promoção atual", "Current promotion"), promo_labels,
                                key="bp_promo", format_func=tpromo)
    with bp3:
        bp_lvl = st.number_input(t("Nível atual", "Current level"), 1, MAX_LEVEL, 1, key="bp_lvl")
    with bp4:
        bp_tier = st.selectbox(t("Promoção alvo", "Target promotion"),
                                promo_labels, key="bp_tier", format_func=tpromo)
    with bp5:
        bp_tgt_lvl = st.number_input(t("Nível alvo", "Target level"), 1, MAX_LEVEL, 1, key="bp_tgt_lvl")

    if st.button("➕ " + t("Adicionar", "Add"), key="bp_add"):
        if PROMO_INDEX[bp_tier] <= PROMO_INDEX[bp_promo]:
            st.warning(t(
                f"⚠️ {bp_pet} já está em '{tpromo(bp_promo)}' — alvo '{tpromo(bp_tier)}' já alcançado ou igual.",
                f"⚠️ {bp_pet} is already at '{bp_promo}' — target '{bp_tier}' already reached or equal.",
            ))
        else:
            ms = calc_to_promo(bp_tier, bp_lvl, bp_promo, 0, 0, 0, 0)
            effective_tgt_lvl = max(bp_tgt_lvl, ms["min_lvl"])
            bp_food = max(0, FOOD_AT_LEVEL.get(effective_tgt_lvl, 0) - FOOD_AT_LEVEL.get(bp_lvl, 0))
            st.session_state["pet_plan"].append({
                "pet":    bp_pet,
                "promo":  bp_promo,
                "cur_lv": bp_lvl,
                "target": bp_tier,
                "tgt_lv": effective_tgt_lvl,
                "food":    bp_food,
                "same":    ms["same"],
                "any":     ms["any"],
                "essence": ms["essence"],
            })
            _pets_save()

    plan = st.session_state["pet_plan"]

    if not plan:
        st.info(t("Nenhum pet no plano ainda. Adicione acima ↑", "No pets in plan yet. Add above ↑"))
    else:
        st.divider()

        # ── Tabela do plano ────────────────────────────────────────────────────
        _cp = t("Pet", "Pet")
        _cr = t("Promoção", "Promo")
        _cl = t("Nível", "Lvl")
        _ct = t("Promo alvo", "Target Promo")
        _ctl = t("Nível alvo", "Target Lvl")
        _cf = "🍗 " + t("Comida", "Food")
        _cs = "📦 " + t("Cópias", "Copies")
        _ca = "🎲 " + t("Qualquer", "Any")
        _ce = "💎 " + t("Essência", "Essence")

        rows = [{_cp: e["pet"], _cr: tpromo(e["promo"]), _cl: e["cur_lv"],
                 _ct: tpromo(e["target"]), _ctl: e.get("tgt_lv", "—"),
                 _cf: e["food"], _cs: e["same"], _ca: e["any"], _ce: e["essence"]}
                for e in plan]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # ── Totais ─────────────────────────────────────────────────────────────
        total_food = sum(e["food"]    for e in plan)
        total_any  = sum(e["any"]     for e in plan)
        total_ess  = sum(e["essence"] for e in plan)

        st.markdown("**📊 " + t("Totais vs. estoque", "Totals vs. stock") + "**")
        tc1, tc2, tc3 = st.columns(3)

        with tc1:
            st.metric(t("🍗 Comida total", "🍗 Total Food"), f"{total_food:,}",
                      help=t(f"Estoque: {inv_food:,}", f"Stock: {inv_food:,}"))
            miss = max(0, total_food - inv_food)
            if miss > 0:
                st.error(t(f"❗ Faltam: {miss:,}", f"❗ Missing: {miss:,}"))
            else:
                st.success(t(f"✅ Saldo: {inv_food - total_food:,}", f"✅ Surplus: {inv_food - total_food:,}"))

        with tc2:
            st.metric(t("🎲 Qualquer total", "🎲 Total Any"), f"{total_any:,}",
                      help=t(f"Estoque: {total_any_inv:,}", f"Stock: {total_any_inv:,}"))
            miss = max(0, total_any - total_any_inv)
            if miss > 0:
                st.error(t(f"❗ Faltam: {miss:,}", f"❗ Missing: {miss:,}"))
            else:
                st.success(t(f"✅ Saldo: {total_any_inv - total_any:,}", f"✅ Surplus: {total_any_inv - total_any:,}"))

        with tc3:
            st.metric(t("💎 Essência total", "💎 Total Essence"), f"{total_ess:,}",
                      help=t(f"Estoque: {inv_ess:,}", f"Stock: {inv_ess:,}"))
            miss = max(0, total_ess - inv_ess)
            if miss > 0:
                st.error(t(f"❗ Faltam: {miss:,}", f"❗ Missing: {miss:,}"))
            else:
                st.success(t("✅ Suficiente", "✅ Sufficient"))

        # ── Cópias por pet ─────────────────────────────────────────────────────
        same_needed = {}
        for e in plan:
            same_needed[e["pet"]] = same_needed.get(e["pet"], 0) + e["same"]

        pets_needing_copies = {k: v for k, v in same_needed.items() if v > 0}
        if pets_needing_copies:
            st.markdown("**📦 " + t("Cópias necessárias por pet", "Copies needed per pet") + "**")
            copy_rows = []
            for pname, needed in pets_needing_copies.items():
                stock = inv_copies.get(pname, 0)
                miss  = max(0, needed - stock)
                copy_rows.append({
                    t("Pet", "Pet"):           pname,
                    t("Necessário", "Needed"): needed,
                    t("Estoque", "Stock"):     stock,
                    t("Faltam", "Missing"):    miss,
                })
            st.dataframe(pd.DataFrame(copy_rows), use_container_width=True, hide_index=True)

        # ── Impacto nos Eventos Regulares ─────────────────────────────────────
        st.divider()
        st.markdown("**📅 " + t("Impacto nos Eventos Regulares", "Regular Event Impact") + "**")

        ev_pet   = next(e for e in EVENTS if e["sheet"] == "Pet_Ranking")
        ev_pname = ev_pet.get("name_pt", ev_pet["name"]) if lang == "pt" else ev_pet["name"]

        pts_food_e   = total_food * 0.3
        pts_ess_e    = total_ess * 15
        tot_rare_e   = sum(e["same"] + e["any"] for e in plan)
        pts_rare_e   = tot_rare_e * 900
        pts_common_e = inv_common * 150
        pts_evt      = pts_food_e + pts_ess_e + pts_rare_e + pts_common_e

        ea1, ea2, ea3, ea4, ea5 = st.columns(5)
        ea1.metric(t("🍗 Comida", "🍗 Food"),           f"{pts_food_e:,.0f} pts")
        ea2.metric(t("💎 Essência", "💎 Essence"),       f"{pts_ess_e:,.0f} pts")
        ea3.metric(t("🐾 Raros", "🐾 Rare"),             f"{pts_rare_e:,.0f} pts",
                   help=t(f"{tot_rare_e} cópias × 900", f"{tot_rare_e} copies × 900"))
        ea4.metric(t("🐾 Comuns", "🐾 Common"),          f"{pts_common_e:,.0f} pts",
                   help=t(f"{inv_common} pets × 150", f"{inv_common} pets × 150"))
        ea5.metric(f"📊 {ev_pname}",                    f"{pts_evt:,.0f} pts")

        ms_icons_p = "  ".join(
            f"✅ {s['value']:,}" if s["reached"] else f"⬜ {s['value']:,}"
            for s in get_milestone_status(ev_pet["milestones"], pts_evt)
        )
        st.caption(f"Milestones: {ms_icons_p}")

        if st.button("📅 " + t("Enviar para Eventos", "Send to Events"), key="send_pet_evt"):
            st.session_state["_pts_to_send_Pet_Ranking"]    = int(pts_evt)
            st.session_state["_calc_contrib_Pet_Ranking_1"] = int(total_ess * 15)
            st.session_state["_calc_contrib_Pet_Ranking_2"] = int(total_food * 0.3)
            st.session_state["_calc_contrib_Pet_Ranking_3"] = int(inv_common * 150)
            st.session_state["_calc_contrib_Pet_Ranking_4"] = int(tot_rare_e * 900)
            st.session_state["_calc_sent_Pet_Ranking"]      = True
            st.success(t(
                f"✅ {pts_evt:,.0f} pts enviados para **{ev_pname}**! Acesse Eventos Regulares para ver.",
                f"✅ {pts_evt:,.0f} pts sent to **{ev_pname}**! Go to Regular Events to see them.",
            ))

        st.divider()
        if st.button("🗑️ " + t("Limpar plano", "Clear plan"), key="bp_clear"):
            st.session_state["pet_plan"] = []
            st.session_state["_pts_to_send_Pet_Ranking"] = 0
            st.session_state["_calc_sent_Pet_Ranking"]   = False
            for _k in range(5):
                st.session_state.pop(f"_calc_contrib_Pet_Ranking_{_k}", None)
            _pets_save()
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# ABA 3 — RENASCIMENTO
# ══════════════════════════════════════════════════════════════════════════════
with tab_rebirth:
    st.caption(t(
        "Selecione um pet e seu estado atual para ver o que é recuperado ao renascer.",
        "Select a pet and its current state to see what is recovered on rebirth.",
    ))

    rb1, rb2, rb3 = st.columns(3)
    with rb1:
        rb_pet = st.selectbox(t("Pet", "Pet"),
                              pet_names, key="rb_pet")
    with rb2:
        rb_promo = st.selectbox(t("Promoção atual", "Current promotion"),
                                promo_labels, key="rb_promo",
                                format_func=tpromo)
    with rb3:
        rb_lvl = st.number_input(t("Nível atual", "Current level"),
                                 min_value=1, max_value=MAX_LEVEL,
                                 value=1, key="rb_lvl")

    rb = calc_rebirth(int(rb_lvl), rb_promo)

    rb_pet_info  = next(p for p in PETS if p[0] == rb_pet)
    rb_faction   = rb_pet_info[1]
    rb_pet_flags = PET_FLAGS.get(rb_pet, set())
    rb_any_promo = "any_promo" in rb_pet_flags

    rb_fc = FACTION_COLORS.get(_FACTION_KEY.get(rb_faction, "Liga"), "#5C3D1E")
    st.markdown(
        f'<div style="border-left:5px solid {rb_fc};padding:5px 14px;'
        f'border-radius:0 8px 8px 0;background:{rb_fc}14;font-weight:700;margin:12px 0 6px;">'
        f'🔄 {t("Recursos Recuperados", "Resources Recovered")} — '
        f'{rb_pet} · {tpromo(rb_promo)} · {t("lv","lv")} {rb_lvl}</div>',
        unsafe_allow_html=True,
    )

    _box_pets = ", ".join(REBIRTH_BOX_PETS)

    _rr1, _rr2, _rr3, _rr4 = st.columns(4)
    if rb_any_promo:
        _rr1.metric(t("🐾 Cópias do pet", "🐾 Pet copies"),
                    f"{rb['same_copies']:,}",
                    help=t("Todas as cópias (any) usadas + 1 base",
                           "All copies (any) used + 1 base"))
        _rr2.metric(t("🎁 Caixas aleatórias", "🎁 Random boxes"),
                    "—",
                    help=t("Pet any_promo não usa caixas separadas",
                           "any_promo pet has no separate box return"))
    else:
        _rr1.metric(t("🐾 Cópias do pet", "🐾 Pet copies"),
                    f"{rb['same_copies']:,}",
                    help=t(f"Cópias específicas de {rb_pet} devolvidas (cumulativo + 1 base)",
                           f"Specific {rb_pet} copies returned (cumulative + 1 base)"))
        _rr2.metric(t("🎁 Caixas aleatórias", "🎁 Random boxes"),
                    f"{rb['any_boxes']:,}",
                    help=t(f"Pode dar: {_box_pets}",
                           f"Can give: {_box_pets}"))
    _rr3.metric(t("🍗 Pet Food", "🍗 Pet Food"), f"{rb['food']:,}",
                help=t("Metade do total gasto até este nível",
                       "Half of total spent reaching this level"))
    _rr4.metric(t("💎 Pet Essence", "💎 Pet Essence"), f"{rb['essence']:,}",
                help=t("Metade da essência de nível + essência de promoção",
                       "Half of level-up + promotion essence"))

    st.divider()

    # ── Impacto no evento ────────────────────────────────────────────────────
    ev_pet_rb   = next(e for e in EVENTS if e["sheet"] == "Pet_Ranking")
    ev_pname_rb = ev_pet_rb.get("name_pt", ev_pet_rb["name"]) if lang == "pt" else ev_pet_rb["name"]

    st.markdown(f"**📅 {t('Impacto no Evento', 'Event Impact')} — {ev_pname_rb}**")
    st.caption(t(
        "O renascimento libera todos os pets gastos. Cada pet raro liberado conta para o evento (× 900 pts).",
        "Rebirth releases all spent pets. Each released rare pet counts toward the event (× 900 pts).",
    ))

    _ei_rows = []
    if not rb_any_promo and rb["same_copies"] > 0:
        _ei_rows.append({
            t("Origem", "Source"):  t(f"🐾 Cópias específicas de {rb_pet}", f"🐾 Specific {rb_pet} copies"),
            t("Pets", "Pets"):      rb["same_copies"],
            t("Taxa", "Rate"):      "× 900",
            t("Pontos", "Points"):  f"{rb['same_copies'] * 900:,}",
        })
    if not rb_any_promo and rb["any_boxes"] > 0:
        _ei_rows.append({
            t("Origem", "Source"):  t(f"🎁 Caixas aleatórias ({_box_pets})", f"🎁 Random boxes ({_box_pets})"),
            t("Pets", "Pets"):      rb["any_boxes"],
            t("Taxa", "Rate"):      "× 900",
            t("Pontos", "Points"):  f"{rb['any_boxes'] * 900:,}",
        })
    if rb_any_promo and rb["event_pets"] > 0:
        _ei_rows.append({
            t("Origem", "Source"):  t(f"🐾 Cópias de {rb_pet} (aceita qualquer)", f"🐾 {rb_pet} copies (any accepted)"),
            t("Pets", "Pets"):      rb["event_pets"],
            t("Taxa", "Rate"):      "× 900",
            t("Pontos", "Points"):  f"{rb['event_pts']:,}",
        })

    if _ei_rows:
        st.dataframe(pd.DataFrame(_ei_rows), use_container_width=True, hide_index=True)

    _ep1, _ep2 = st.columns(2)
    _ep1.metric(t("🐾 Total de pets liberados", "🐾 Total pets released"),
                f"{rb['event_pets']:,}")
    _ep2.metric(f"📊 {t('Total de pontos', 'Total points')} — {ev_pname_rb}",
                f"{rb['event_pts']:,}")

    ms_rb = "  ".join(
        f"✅ {s['value']:,}" if s["reached"] else f"⬜ {s['value']:,}"
        for s in get_milestone_status(ev_pet_rb["milestones"], rb["event_pts"])
    )
    st.caption(f"Milestones: {ms_rb}")

    if st.button("📅 " + t("Enviar para Eventos", "Send to Events"), key="send_rb_evt"):
        st.session_state["_pts_to_send_Pet_Ranking"]    = int(rb["event_pts"])
        st.session_state["_calc_contrib_Pet_Ranking_4"] = int(rb["event_pts"])
        st.session_state["_calc_sent_Pet_Ranking"]      = True
        st.success(t(
            f"✅ {rb['event_pts']:,} pts enviados para **{ev_pname_rb}**!",
            f"✅ {rb['event_pts']:,} pts sent to **{ev_pname_rb}**!",
        ))

# ══════════════════════════════════════════════════════════════════════════════
# ABA 4 — INSTRUÇÕES & REFERÊNCIA
# ══════════════════════════════════════════════════════════════════════════════
with tab_help:
    _hi1, _hi2 = st.tabs([
        "📖 " + t("Como usar", "How to use"),
        "📊 " + t("Referência de dados", "Data reference"),
    ])

    with _hi1:
        st.markdown(t(
            """
### Calculadora de Pets — Como usar

**Inventário de Recursos** (topo da página)
- **Pet Food**: comida para subir nível dos pets
- **Pet Essence**: essência para promoções
- **Rare Pet Choice Box**: caixa que abre como pet Raro de escolha
- **Pets Comuns**: cópias de pets comuns usados como material de EXP

**Inventário de Pets**
Informe quantas cópias de cada pet você possui.
Marque *"Excluir de Qualquer?"* para não contar cópias de um pet como wildcard.

**Aba Calculadora**
1. Selecione o pet, sua promoção atual e nível atual
2. Escolha o tier alvo (EPIC / LEGENDARY / MYTHIC)
3. Veja o custo detalhado: comida, cópias (mesmas e qualquer), essência

**Aba Planejador de Lote**
1. Adicione múltiplos pets com seus objetivos
2. Veja o custo total consolidado de todos os pets
3. Compare com seu inventário — o app mostra o que falta
""",
            """
### Pet Calculator — How to use

**Resource Inventory** (top of page)
- **Pet Food**: food to level up pets
- **Pet Essence**: essence for promotions
- **Rare Pet Choice Box**: opens as a Rare pet of your choice
- **Common Pets**: common pet copies used as EXP material

**Pet Inventory**
Enter how many copies of each pet you own.
Check *"Exclude from Any?"* to not count a pet's copies as wildcards.

**Calculator tab**
1. Select the pet, its current promotion and current level
2. Choose the target tier (EPIC / LEGENDARY / MYTHIC)
3. See the detailed cost: food, copies (same and any), essence

**Batch Planner tab**
1. Add multiple pets with their goals
2. See the total consolidated cost for all pets
3. Compare against your inventory — the app shows what's missing
""",
        ))

    with _hi2:
        st.subheader(t("🐾 Tiers de Promoção", "🐾 Promotion Tiers"))
        st.caption(t(
            "Requisitos mínimos de nível e custo estimado por tier.",
            "Minimum level requirements and estimated cost per tier.",
        ))
        _pt_rows = []
        for _promo in PROMO_LIST:
            _min_lv, _promo_label_ref, _tier, _, _, _ = _promo
            _pt_rows.append({
                t("Promoção", "Promotion"): _promo_label_ref,
                t("Tier", "Tier"):          _tier,
                t("Nível mín.", "Min Lvl"): _min_lv,
            })
        import pandas as _pd3
        st.dataframe(_pd3.DataFrame(_pt_rows), use_container_width=True, hide_index=True)

