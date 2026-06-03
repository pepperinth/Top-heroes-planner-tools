"""
pages/3_Pets.py — Pet Calculator page.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from pet_engine import (
    PETS, PROMO_LIST, TIER_RANK, FACTION_EMOJI,
    MAX_LEVEL,
    calc_milestone, calc_to_target, max_level_with_food, get_stats,
)
from events_data import EVENTS, get_milestone_status
from behemoth_engine import FACTION_ICONS, FACTION_ICON_DIR

_BASE = os.path.dirname(os.path.dirname(__file__))

# English pet faction → Portuguese icon key
_FACTION_KEY = {"League": "Liga", "Horde": "Horda", "Nature": "Natureza"}
# Portuguese display names
_FACTION_PT  = {"League": "Liga", "Horde": "Horda", "Nature": "Natureza"}

def _faction_icon(faction_en: str, width: int = 32):
    path = os.path.join(_BASE, FACTION_ICON_DIR, FACTION_ICONS[_FACTION_KEY[faction_en]])
    st.image(path, width=width)

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

_FS = {True: t("★ Exclusivo da Facção", "★ Faction-Specific"),
       False: t("Universal", "Universal"),
       None: "—"}

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🐾 " + t("Calculadora de Pets", "Pet Calculator"))
st.caption(t(
    "Calcula recursos necessários para evoluir e promover seus pets.",
    "Calculates resources needed to level up and promote your pets.",
))

# ── RECURSOS (compartilhado entre abas) ───────────────────────────────────────
st.subheader("📦 " + t("Recursos", "Resources"))
rc1, rc2, rc3, rc4 = st.columns(4)
with rc1:
    inv_food = st.number_input(t("🍗 Pet Food", "🍗 Pet Food"),
                                min_value=0, value=0, step=1000, key="pet_food")
with rc2:
    inv_ess = st.number_input(t("💎 Pet Essence", "💎 Pet Essence"),
                               min_value=0, value=0, step=100, key="pet_ess")
with rc3:
    inv_box = st.number_input(t("🎁 Rare Pet Choice Box", "🎁 Rare Pet Choice Box"),
                               min_value=0, value=0, step=1, key="pet_box")
with rc4:
    inv_common = st.number_input(
        t("🐾 Pets Comuns", "🐾 Common Pets"),
        min_value=0, value=0, step=1, key="inv_common_pet",
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
)

inv_copies  = {PETS[i][0]: int(edited_inv.iloc[i][_col_cop]) for i in range(len(PETS))}
inv_exclude = {PETS[i][0]: bool(edited_inv.iloc[i][_col_exc]) for i in range(len(PETS))}

# Total "any" disponível (sem exclusões + choice boxes)
total_any_inv = sum(
    inv_copies[name] for name, *_ in PETS if not inv_exclude[name]
) + inv_box

# ── ABAS ───────────────────────────────────────────────────────────────────────
st.divider()
tab_calc, tab_plan = st.tabs([
    "🧮 " + t("Calculadora", "Calculator"),
    "📋 " + t("Planejador de Lote", "Batch Planner"),
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
                st.metric(t("🍗 Comida", "🍗 Food"),         f"{ms['food']:,}")
                st.metric(f"📦 {selected_pet}",               f"{ms['same']:,}")
                st.metric(t("🎲 Qualquer pet", "🎲 Any pet"), f"{ms['any']:,}")
                if ms["essence"] > 0:
                    st.metric(t("💎 Essência", "💎 Essence"), f"{ms['essence']:,}")

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

        ms_g = calc_milestone(sel_tier, current_level, promo_min_lvl, current_promo_lbl, 0, 0, 0, 0)

        ev_pet_c   = next(e for e in EVENTS if e["sheet"] == "Pet_Ranking")
        ev_pcname  = ev_pet_c.get("name_pt", ev_pet_c["name"]) if lang == "pt" else ev_pet_c["name"]

        pts_food_c   = ms_g["food"] * 0.3
        pts_ess_c    = ms_g["essence"] * 15
        tot_rare_c   = ms_g["same"] + ms_g["any"]
        pts_rare_c   = tot_rare_c * 900
        pts_common_c = inv_common * 150
        pts_evt_c    = pts_food_c + pts_ess_c + pts_rare_c + pts_common_c

        ec1, ec2, ec3, ec4, ec5 = st.columns(5)
        ec1.metric(t("🍗 Comida", "🍗 Food"),          f"{pts_food_c:,.0f} pts")
        ec2.metric(t("💎 Essência", "💎 Essence"),      f"{pts_ess_c:,.0f} pts")
        ec3.metric(t("🐾 Raros", "🐾 Rare"),            f"{pts_rare_c:,.0f} pts",
                   help=t(f"{tot_rare_c} cópias × 900", f"{tot_rare_c} copies × 900"))
        ec4.metric(t("🐾 Comuns", "🐾 Common"),         f"{pts_common_c:,.0f} pts",
                   help=t(f"{inv_common} pets × 150", f"{inv_common} pets × 150"))
        ec5.metric(f"📊 {ev_pcname}",                   f"{pts_evt_c:,.0f} pts")

        ms_icons_c2 = "  ".join(
            f"✅ {s['value']:,}" if s["reached"] else f"⬜ {s['value']:,}"
            for s in get_milestone_status(ev_pet_c["milestones"], pts_evt_c)
        )
        st.caption(f"Milestones: {ms_icons_c2}")

        if st.button("📅 " + t("Enviar para Eventos", "Send to Events"), key="send_pet_calc_evt"):
            st.session_state["_pts_to_send_Pet_Ranking"]    = int(pts_evt_c)
            st.session_state["_calc_contrib_Pet_Ranking_1"] = int(ms_g["essence"] * 15)
            st.session_state["_calc_contrib_Pet_Ranking_2"] = int(ms_g["food"] * 0.3)
            st.session_state["_calc_contrib_Pet_Ranking_3"] = int(inv_common * 150)
            st.session_state["_calc_contrib_Pet_Ranking_4"] = int(tot_rare_c * 900)
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
    bp1, bp2, bp3, bp4 = st.columns([2, 2, 1, 1])
    with bp1:
        bp_pet = st.selectbox(t("Pet", "Pet"), pet_names, key="bp_pet")
    with bp2:
        bp_promo = st.selectbox(t("Promoção atual", "Current promotion"), promo_labels, key="bp_promo")
    with bp3:
        bp_lvl = st.number_input(t("Nível atual", "Current level"), 1, MAX_LEVEL, 1, key="bp_lvl")
    with bp4:
        bp_tier = st.selectbox(t("Tier alvo", "Target tier"),
                                ["EPIC", "LEGENDARY", "MYTHIC"], key="bp_tier")

    if st.button("➕ " + t("Adicionar", "Add"), key="bp_add"):
        bp_info = promo_data[bp_promo]
        bp_promo_min_lvl, _, bp_promo_tier, _, _ = bp_info
        if TIER_RANK[bp_promo_tier] >= TIER_RANK[bp_tier]:
            st.warning(t(
                f"⚠️ {bp_pet} já está em {bp_promo_tier} — alvo {bp_tier} já alcançado.",
                f"⚠️ {bp_pet} is already at {bp_promo_tier} — target {bp_tier} already reached.",
            ))
        else:
            ms = calc_milestone(bp_tier, bp_lvl, bp_promo_min_lvl, bp_promo, 0, 0, 0, 0)
            st.session_state["pet_plan"].append({
                "pet":    bp_pet,
                "promo":  bp_promo,
                "cur_lv": bp_lvl,
                "target": bp_tier,
                "food":    ms["food"],
                "same":    ms["same"],
                "any":     ms["any"],
                "essence": ms["essence"],
            })

    plan = st.session_state["pet_plan"]

    if not plan:
        st.info(t("Nenhum pet no plano ainda. Adicione acima ↑", "No pets in plan yet. Add above ↑"))
    else:
        st.divider()

        # ── Tabela do plano ────────────────────────────────────────────────────
        _cp = t("Pet", "Pet")
        _cr = t("Promoção", "Promo")
        _cl = t("Nível", "Lvl")
        _ct = t("Alvo", "Target")
        _cf = "🍗 " + t("Comida", "Food")
        _cs = "📦 " + t("Cópias", "Copies")
        _ca = "🎲 " + t("Qualquer", "Any")
        _ce = "💎 " + t("Essência", "Essence")

        rows = [{_cp: e["pet"], _cr: e["promo"], _cl: e["cur_lv"], _ct: e["target"],
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
            st.rerun()
