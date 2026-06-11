"""
pages/6_Behemoth.py — Behemoth Calculator & Batch Planner.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from PIL import Image
import pandas as pd
from behemoth_engine import (
    MAGICITE_PER_LEVEL, MAGIC_CORE_AT_LEVEL, STAR_SEAL_COSTS,
    MAX_LEVEL, MAX_STARS, MAX_STARS_CALC,
    BEHEMOTHS, BEHEMOTH_NAMES, FACTION_ICONS, FACTION_ICON_DIR,
    get_behemoth, show_star_image,
    calc_level_resources, calc_star_resources, calc_total,
)
from ui_utils import inject_global_css, section_header, results_header, FACTION_COLORS
import persistence

_BASE = os.path.dirname(os.path.dirname(__file__))

st.set_page_config(page_title="Behemoth", page_icon="🦕", layout="wide")

# ── Persistence ────────────────────────────────────────────────────────────────
_cm = persistence.new_manager("behemoth")

if "beh_initialized" not in st.session_state:
    _saved = persistence.load(_cm, "th_behemoth")
    if _saved:
        st.session_state["calc_inv_mag"]       = int(_saved.get("inv_mag", 0))
        st.session_state["calc_inv_core"]      = int(_saved.get("inv_core", 0))
        st.session_state["calc_inv_seal_spec"] = int(_saved.get("inv_seal_spec", 0))
        st.session_state["calc_inv_seal_univ"] = int(_saved.get("inv_seal_univ", 0))
        if "plan" in _saved:
            st.session_state["behemoth_plan"] = _saved["plan"]
    st.session_state["beh_initialized"] = True


def _beh_save():
    persistence.save(_cm, "th_behemoth", {
        "inv_mag":       st.session_state.get("calc_inv_mag", 0),
        "inv_core":      st.session_state.get("calc_inv_core", 0),
        "inv_seal_spec": st.session_state.get("calc_inv_seal_spec", 0),
        "inv_seal_univ": st.session_state.get("calc_inv_seal_univ", 0),
        "plan":          st.session_state.get("behemoth_plan", []),
    })


# ── Language ───────────────────────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "pt"

with st.sidebar:
    st.markdown("### 🌐 Idioma / Language")
    lang_pick = st.radio(
        "", ["🇧🇷 Português", "🇬🇧 English"],
        index=0 if st.session_state.lang == "pt" else 1,
        horizontal=True, label_visibility="collapsed", key="lang_behemoth",
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

# ── Helpers ────────────────────────────────────────────────────────────────────
_TIERS_PT = ["Dourada", "Vermelha", "Platinada"]
_TIERS_EN = ["Gold",    "Red",     "Platinum"]

def _star_label(star: int) -> str:
    if star == 0:
        return "0 — " + t("Sem estrelas", "No stars")
    tier_idx  = (star - 1) // 25
    vis       = ((star - 1) % 25) // 5 + 1
    leg       = (star - 1) % 5 + 1
    tier      = (_TIERS_PT if lang == "pt" else _TIERS_EN)[tier_idx] if tier_idx < 3 else f"Tier {tier_idx+1}"
    done      = t("completa", "complete")
    legs_word = t("pernas", "legs")
    prefix    = f"{star} — ⭐ {vis} {tier}"
    return f"{prefix} {done}" if leg == 5 else f"{prefix} · {leg}/5 {legs_word}"

_STAR_OPTS = [_star_label(s) for s in range(MAX_STARS_CALC + 1)]

def _show_star_img(star: int):
    show_star_image(star, _BASE, st)

def _faction_icon(faction_key: str, width: int = 40):
    path = os.path.join(_BASE, FACTION_ICON_DIR, FACTION_ICONS[faction_key])
    st.image(path, width=width)

def _faction_label(b: dict) -> str:
    f = b["faction"] if lang == "pt" else b["faction_en"]
    return f"{f} — {b['name']}"

def _behemoth_selector(key: str, label: str, default_idx: int = 0) -> dict:
    opts = [_faction_label(b) for b in BEHEMOTHS]
    sel = st.selectbox(label, opts, index=default_idx, key=key)
    beh = BEHEMOTHS[opts.index(sel)]
    col_icon, col_name = st.columns([1, 6])
    with col_icon:
        _faction_icon(beh["faction"], width=36)
    with col_name:
        faction_name = beh["faction"] if lang == "pt" else beh["faction_en"]
        st.caption(f"**{beh['name']}** · {faction_name}")
    return beh

def _net_label(inv: int, needed: int) -> str:
    net = max(0, needed - inv)
    if inv == 0:
        return ""
    if net == 0:
        return "✅ " + t("Suficiente", "Sufficient")
    return f"⚠️ {t('Faltam', 'Still need')} {net:,}"

def _render_metric_with_net(label: str, needed: int, inv: int):
    delta = f"−{inv:,} " + t("em estoque", "in stock") if inv > 0 else None
    st.metric(label, f"{needed:,}", delta=delta,
              delta_color="inverse" if inv > 0 else "off")
    msg = _net_label(inv, needed)
    if msg:
        if msg.startswith("✅"):
            st.success(msg)
        else:
            st.warning(msg)

# ── Header ─────────────────────────────────────────────────────────────────────
inject_global_css()
st.title("🦕 " + t("Calculadora de Behemoth", "Behemoth Calculator"))
st.caption(t(
    "Calcula Magicite, Núcleos Mágicos e Selos necessários para evoluir seu Behemoth.",
    "Calculates Magicite, Magic Cores and Seals needed to upgrade your Behemoth.",
))

tab_calc, tab_plan, tab_ref = st.tabs([
    "🧮 " + t("Calculadora", "Calculator"),
    "📋 " + t("Planejador de Lote", "Batch Planner"),
    "📖 " + t("Referência", "Reference"),
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — CALCULATOR
# ══════════════════════════════════════════════════════════════════════════════
with tab_calc:

    # ── Behemoth selector ─────────────────────────────────────────────────────
    st.subheader("🦕 " + t("Selecione o Behemoth", "Select Behemoth"))
    beh = _behemoth_selector("calc_beh_sel", t("Behemoth", "Behemoth"))
    faction_key = beh["faction"]
    faction_name = beh["faction"] if lang == "pt" else beh["faction_en"]

    st.markdown("---")

    # ── Current / Target ──────────────────────────────────────────────────────
    col_cur, col_tgt = st.columns(2, gap="large")

    with col_cur:
        st.subheader("📍 " + t("Estado Atual", "Current State"))
        cur_lvl = st.number_input(
            t("Nível atual", "Current level"),
            min_value=1, max_value=MAX_LEVEL, value=1, step=1,
            key="calc_cur_lvl",
        )
        cur_star_sel = st.selectbox(
            t("Estrelas atuais", "Current stars"),
            _STAR_OPTS, index=0, key="calc_cur_star_sel",
        )
        cur_star = _STAR_OPTS.index(cur_star_sel)
        _show_star_img(cur_star)

    with col_tgt:
        st.subheader("🎯 " + t("Estado Alvo", "Target State"))
        tgt_lvl = st.number_input(
            t("Nível alvo", "Target level"),
            min_value=1, max_value=MAX_LEVEL, value=MAX_LEVEL, step=1,
            key="calc_tgt_lvl",
        )
        tgt_star_sel = st.selectbox(
            t("Estrelas alvo", "Target stars"),
            _STAR_OPTS, index=MAX_STARS_CALC, key="calc_tgt_star_sel",
        )
        tgt_star = _STAR_OPTS.index(tgt_star_sel)
        _show_star_img(tgt_star)

    # ── Inventory ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🎒 " + t("Inventário (opcional)", "Inventory (optional)"))

    ic1, ic2, ic3, ic4 = st.columns(4)
    with ic1:
        inv_mag = st.number_input(
            f"🔮 Magicite ({faction_name})",
            min_value=0, value=0, step=100, key="calc_inv_mag",
            on_change=_beh_save,
        )
    with ic2:
        inv_core = st.number_input(
            t("💠 Núcleos Mágicos", "💠 Magic Cores"),
            min_value=0, value=0, step=1, key="calc_inv_core",
            on_change=_beh_save,
        )
    with ic3:
        inv_seal_spec = st.number_input(
            f"🔑 {t('Selo de', 'Seal of')} {beh['name']}",
            min_value=0, value=0, step=1, key="calc_inv_seal_spec",
            on_change=_beh_save,
        )
    with ic4:
        inv_seal_univ = st.number_input(
            t("🔑 Selos Universais", "🔑 Universal Seals"),
            min_value=0, value=0, step=1, key="calc_inv_seal_univ",
            on_change=_beh_save,
        )

    # ── Validation & results ──────────────────────────────────────────────────
    st.markdown("---")
    errors = []
    if tgt_lvl < cur_lvl:
        errors.append(t("⚠️ Nível alvo deve ser ≥ nível atual.", "⚠️ Target level must be ≥ current level."))
    if tgt_star < cur_star:
        errors.append(t("⚠️ Estrelas alvo devem ser ≥ estrelas atuais.", "⚠️ Target stars must be ≥ current stars."))
    for e in errors:
        st.error(e)

    if not errors:
        res = calc_total(cur_lvl, tgt_lvl, cur_star, tgt_star)
        total_mag   = res["magicite"]
        total_cores = res["magic_cores"]
        total_seals = res["seals"]
        milestones  = res["core_milestones"]
        inv_seal_total = inv_seal_spec + inv_seal_univ
        nothing = (tgt_lvl == cur_lvl and tgt_star == cur_star)

        if nothing:
            st.info(t("Nível e estrelas alvo iguais ao atual. Nada a calcular.",
                      "Target matches current state. Nothing to calculate."))
        else:
            _beh_fc = FACTION_COLORS.get(faction_key, "#5C3D1E")
            results_header(f"📊 {t('Resumo de Recursos','Resource Summary')}", faction_key)
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                _render_metric_with_net(
                    f"🔮 Magicite ({faction_name}) " + t("necessário", "needed"),
                    total_mag, inv_mag,
                )
            with mc2:
                _render_metric_with_net(
                    t("💠 Núcleos Mágicos necessários", "💠 Magic Cores needed"),
                    total_cores, inv_core,
                )
            with mc3:
                seal_delta_lbl = None
                if inv_seal_total > 0:
                    seal_delta_lbl = f"−{inv_seal_total:,} " + t("em estoque", "in stock")
                    if inv_seal_spec > 0 and inv_seal_univ > 0:
                        seal_delta_lbl += f" ({inv_seal_spec:,} " + t("espec.", "spec.") + f" + {inv_seal_univ:,} " + t("univ.", "univ.") + ")"
                st.metric(
                    f"🔑 {t('Selos necessários', 'Seals needed')}",
                    f"{total_seals:,}",
                    delta=seal_delta_lbl,
                    delta_color="inverse" if inv_seal_total > 0 else "off",
                )
                msg = _net_label(inv_seal_total, total_seals)
                if msg:
                    if msg.startswith("✅"):
                        st.success(msg)
                    else:
                        st.warning(msg)

            if milestones:
                with st.expander(t("💠 Detalhamento de Núcleos por milestone",
                                   "💠 Magic Core breakdown by milestone")):
                    for lvl, cores in sorted(milestones.items()):
                        st.markdown(f"- **{t('Nível','Level')} {lvl}:** {cores:,} {t('Núcleos','Cores')}")

            if tgt_lvl > cur_lvl:
                with st.expander(t("🔮 Detalhamento de Magicite por nível",
                                   "🔮 Magicite breakdown by level")):
                    rows_exp = []
                    for lvl in range(cur_lvl + 1, tgt_lvl + 1):
                        mag  = MAGICITE_PER_LEVEL.get(lvl, 0)
                        core = MAGIC_CORE_AT_LEVEL.get(lvl)
                        core_str = f" + 💠 {core:,}" if core else ""
                        rows_exp.append(f"- **{t('Nível','Level')} {lvl}:** 🔮 {mag:,}{core_str}")
                    st.markdown("\n".join(rows_exp))

            if tgt_star > cur_star:
                with st.expander(t("🔑 Detalhamento de Selos por estrela",
                                   "🔑 Seal cost by star")):
                    for s in range(cur_star + 1, tgt_star + 1):
                        st.markdown(f"- ⭐ **{t('Estrela','Star')} {s}:** {STAR_SEAL_COSTS[s-1]:,} {t('selos','seals')}")

        # ── Event Impact ──────────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("📅 " + t("Impacto nos Eventos Regulares", "Regular Event Impact"))

        if nothing or (total_mag == 0 and total_cores == 0):
            st.info(t("Sem recursos a gastar — nenhum impacto nos eventos.",
                      "No resources to spend — no event impact."))
        else:
            pts_rr_mag  = total_mag   * 0.0025
            pts_rr_core = total_cores * 0.5
            pts_rr_seal = total_seals * 30
            pts_rr      = pts_rr_mag + pts_rr_core + pts_rr_seal
            pts_hd_mag  = total_mag   * 0.015
            pts_hd_core = total_cores * 3
            pts_hd_seal = total_seals * 180
            pts_hd      = pts_hd_mag + pts_hd_core + pts_hd_seal

            ec1, ec2 = st.columns(2)
            with ec1:
                st.markdown(f"**⚜️ {t('Corrida de Relíquias','Relic Race')}**")
                st.markdown(f"- 🔮 Magicite → **{pts_rr_mag:,.0f} pts** *(×0.0025/u)*")
                if total_cores > 0:
                    st.markdown(f"- 💠 {t('Núcleos','Cores')} → **{pts_rr_core:,.0f} pts** *(×0.5/u)*")
                if total_seals > 0:
                    st.markdown(f"- 🔑 {t('Selos','Seals')} → **{pts_rr_seal:,.0f} pts** *(×30/u)*")
                st.markdown(f"**{t('Total','Total')}: {pts_rr:,.0f} pts**")
            with ec2:
                st.markdown(f"**👤 {t('Desenvolvimento de Heróis','Hero Development')}**")
                st.markdown(f"- 🔮 Magicite → **{pts_hd_mag:,.0f} pts** *(×0.015/u)*")
                if total_cores > 0:
                    st.markdown(f"- 💠 {t('Núcleos','Cores')} → **{pts_hd_core:,.0f} pts** *(×3/u)*")
                if total_seals > 0:
                    st.markdown(f"- 🔑 {t('Selos','Seals')} → **{pts_hd_seal:,.0f} pts** *(×180/u)*")
                st.markdown(f"**{t('Total','Total')}: {pts_hd:,.0f} pts**")

            if st.button("📅 " + t("Enviar para Eventos", "Send to Events"), key="send_beh_calc_evt"):
                st.session_state["_src_behemoth_Relic_Race"]        = int(pts_rr)
                st.session_state["_calc_contrib_Relic_Race_0"]      = int(pts_rr_mag)
                st.session_state["_calc_contrib_Relic_Race_1"]      = int(pts_rr_core)
                st.session_state["_calc_contrib_Relic_Race_2"]      = int(pts_rr_seal)
                st.session_state["_calc_sent_Relic_Race"]           = True
                st.session_state["_src_behemoth_Hero_Development"]  = int(pts_hd)
                st.session_state["_calc_contrib_Hero_Development_7"]= int(pts_hd_mag)
                st.session_state["_calc_contrib_Hero_Development_8"]= int(pts_hd_core)
                st.session_state["_calc_contrib_Hero_Development_9"]= int(pts_hd_seal)
                st.session_state["_calc_sent_Hero_Development"]     = True
                st.success(t("✅ Enviado! Acesse Eventos Regulares para ver o impacto.",
                             "✅ Sent! Go to Regular Events to see the impact."))

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — BATCH PLANNER
# ══════════════════════════════════════════════════════════════════════════════
with tab_plan:

    if "behemoth_plan" not in st.session_state:
        st.session_state["behemoth_plan"] = []

    plan: list[dict] = st.session_state["behemoth_plan"]

    # ── Add entry ─────────────────────────────────────────────────────────────
    st.subheader("➕ " + t("Adicionar ao plano", "Add to plan"))

    pa1, pa2 = st.columns([2, 3], gap="large")

    with pa1:
        plan_beh = _behemoth_selector("plan_beh_sel", t("Behemoth", "Behemoth"))

    with pa2:
        lc1, lc2 = st.columns(2)
        with lc1:
            p_cur_lvl = st.number_input(t("Nível atual","Current level"),
                min_value=1, max_value=MAX_LEVEL, value=1, step=1, key="plan_cur_lvl")
            p_cur_star_sel = st.selectbox(t("Estrelas atuais","Current stars"),
                _STAR_OPTS, index=0, key="plan_cur_star_sel")
            p_cur_star = _STAR_OPTS.index(p_cur_star_sel)
        with lc2:
            p_tgt_lvl = st.number_input(t("Nível alvo","Target level"),
                min_value=1, max_value=MAX_LEVEL, value=MAX_LEVEL, step=1, key="plan_tgt_lvl")
            p_tgt_star_sel = st.selectbox(t("Estrelas alvo","Target stars"),
                _STAR_OPTS, index=MAX_STARS_CALC, key="plan_tgt_star_sel")
            p_tgt_star = _STAR_OPTS.index(p_tgt_star_sel)

    plan_errors = []
    if p_tgt_lvl < p_cur_lvl:
        plan_errors.append(t("Nível alvo deve ser ≥ nível atual.", "Target level must be ≥ current level."))
    if p_tgt_star < p_cur_star:
        plan_errors.append(t("Estrelas alvo devem ser ≥ estrelas atuais.", "Target stars must be ≥ current stars."))
    for e in plan_errors:
        st.error(e)

    if not plan_errors:
        if st.button("➕ " + t("Adicionar", "Add"), key="plan_add"):
            r = calc_total(p_cur_lvl, p_tgt_lvl, p_cur_star, p_tgt_star)
            plan.append({
                "name":     plan_beh["name"],
                "faction":  plan_beh["faction"],
                "f_en":     plan_beh["faction_en"],
                "cur_lvl":  p_cur_lvl,  "tgt_lvl": p_tgt_lvl,
                "cur_star": p_cur_star, "tgt_star": p_tgt_star,
                "magicite": r["magicite"],
                "cores":    r["magic_cores"],
                "seals":    r["seals"],
            })
            _beh_save()
            st.rerun()

    # ── Plan table ────────────────────────────────────────────────────────────
    st.markdown("---")

    if not plan:
        st.info(t("Plano vazio. Adicione Behemoths acima.", "Plan is empty. Add Behemoths above."))
    else:
        section_header(f"📋 {t('Plano atual','Current plan')}")

        rows_tbl = []
        for i, e in enumerate(plan):
            faction_disp = e["faction"] if lang == "pt" else e["f_en"]
            rows_tbl.append({
                "#": i + 1,
                t("Behemoth","Behemoth"): e["name"],
                t("Facção","Faction"): faction_disp,
                t("Nível","Level"): f"{e['cur_lvl']} → {e['tgt_lvl']}",
                "⭐": f"{e['cur_star']} → {e['tgt_star']}",
                "🔮 Magicite": f"{e['magicite']:,}",
                "💠 " + t("Núcleos","Cores"): f"{e['cores']:,}",
                "🔑 " + t("Selos","Seals"): f"{e['seals']:,}",
            })
        df = pd.DataFrame(rows_tbl).set_index("#")
        st.dataframe(df, use_container_width=True)

        # Remove individual entry
        rem_idx = st.number_input(t("Remover entrada #","Remove entry #"),
            min_value=1, max_value=len(plan), value=1, step=1, key="plan_rem_idx")
        if st.button(t("🗑️ Remover","🗑️ Remove"), key="plan_rem"):
            plan.pop(rem_idx - 1)
            _beh_save()
            st.rerun()

        # ── Totals ────────────────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("📊 " + t("Totais", "Totals"))

        # Magicite by faction
        mag_by_faction = {}
        for e in plan:
            mag_by_faction[e["faction"]] = mag_by_faction.get(e["faction"], 0) + e["magicite"]

        total_cores_plan = sum(e["cores"] for e in plan)

        # Seals by behemoth
        seals_by_beh = {}
        for e in plan:
            seals_by_beh[e["name"]] = seals_by_beh.get(e["name"], 0) + e["seals"]

        # Inventory for planner
        st.markdown(f"**🎒 {t('Inventário do plano','Plan inventory')}**")
        inv_cols = st.columns(3 + len(mag_by_faction))

        inv_mag_plan = {}
        col_i = 0
        for fk, fmag in mag_by_faction.items():
            fname = fk if lang == "pt" else next(b["faction_en"] for b in BEHEMOTHS if b["faction"] == fk)
            with inv_cols[col_i]:
                inv_mag_plan[fk] = st.number_input(
                    f"🔮 Magicite ({fname})",
                    min_value=0, value=0, step=100, key=f"plan_inv_mag_{fk}",
                )
            col_i += 1

        with inv_cols[col_i]:
            inv_core_plan = st.number_input(
                t("💠 Núcleos Mágicos","💠 Magic Cores"),
                min_value=0, value=0, step=1, key="plan_inv_core",
            )
        col_i += 1
        with inv_cols[col_i]:
            inv_seal_univ_plan = st.number_input(
                t("🔑 Selos Universais","🔑 Universal Seals"),
                min_value=0, value=0, step=1, key="plan_inv_seal_univ",
            )

        st.markdown("")

        # Magicite totals per faction
        st.markdown(f"##### 🔮 {t('Magicite por Facção','Magicite by Faction')}")
        mc = st.columns(len(mag_by_faction))
        for i, (fk, total) in enumerate(mag_by_faction.items()):
            fname = fk if lang == "pt" else next(b["faction_en"] for b in BEHEMOTHS if b["faction"] == fk)
            inv_f = inv_mag_plan.get(fk, 0)
            with mc[i]:
                col_ico, col_met = st.columns([1, 4])
                with col_ico:
                    _faction_icon(fk, width=28)
                with col_met:
                    _render_metric_with_net(f"Magicite ({fname})", total, inv_f)

        # Cores total
        st.markdown(f"##### 💠 {t('Núcleos Mágicos','Magic Cores')}")
        _render_metric_with_net(t("💠 Núcleos Mágicos totais","💠 Total Magic Cores"),
                                total_cores_plan, inv_core_plan)

        # Seals per behemoth
        st.markdown(f"##### 🔑 {t('Selos por Behemoth','Seals by Behemoth')}")
        if inv_seal_univ_plan > 0:
            st.caption(t(
                f"Você tem {inv_seal_univ_plan:,} Selos Universais — distribua conforme precisar.",
                f"You have {inv_seal_univ_plan:,} Universal Seals — distribute as needed.",
            ))
        seal_rows = []
        for bname, stotal in seals_by_beh.items():
            beh_info = get_behemoth(bname)
            faction_disp = beh_info["faction"] if lang == "pt" else beh_info["faction_en"]
            seal_rows.append({
                t("Behemoth","Behemoth"): bname,
                t("Facção","Faction"): faction_disp,
                "🔑 " + t("Selos necessários","Seals needed"): stotal,
            })
        df_seals = pd.DataFrame(seal_rows)
        st.dataframe(df_seals, use_container_width=True, hide_index=True)

        # ── Event Impact ──────────────────────────────────────────────────────
        total_mag_plan = sum(e["magicite"] for e in plan)
        if total_mag_plan > 0 or total_cores_plan > 0:
            st.markdown("---")
            st.subheader("📅 " + t("Impacto nos Eventos Regulares", "Regular Event Impact"))

            total_seals_plan = sum(e["seals"] for e in plan)
            pts_rr_mag  = total_mag_plan   * 0.0025
            pts_rr_core = total_cores_plan * 0.5
            pts_rr_seal = total_seals_plan * 30
            pts_rr      = pts_rr_mag + pts_rr_core + pts_rr_seal
            pts_hd_mag  = total_mag_plan   * 0.015
            pts_hd_core = total_cores_plan * 3
            pts_hd_seal = total_seals_plan * 180
            pts_hd      = pts_hd_mag + pts_hd_core + pts_hd_seal

            pe1, pe2 = st.columns(2)
            with pe1:
                st.markdown(f"**⚜️ {t('Corrida de Relíquias','Relic Race')}**")
                st.markdown(f"- 🔮 Magicite → **{pts_rr_mag:,.0f} pts**")
                if total_cores_plan > 0:
                    st.markdown(f"- 💠 {t('Núcleos','Cores')} → **{pts_rr_core:,.0f} pts**")
                if total_seals_plan > 0:
                    st.markdown(f"- 🔑 {t('Selos','Seals')} → **{pts_rr_seal:,.0f} pts**")
                st.markdown(f"**{t('Total','Total')}: {pts_rr:,.0f} pts**")
            with pe2:
                st.markdown(f"**👤 {t('Desenvolvimento de Heróis','Hero Development')}**")
                st.markdown(f"- 🔮 Magicite → **{pts_hd_mag:,.0f} pts**")
                if total_cores_plan > 0:
                    st.markdown(f"- 💠 {t('Núcleos','Cores')} → **{pts_hd_core:,.0f} pts**")
                if total_seals_plan > 0:
                    st.markdown(f"- 🔑 {t('Selos','Seals')} → **{pts_hd_seal:,.0f} pts**")
                st.markdown(f"**{t('Total','Total')}: {pts_hd:,.0f} pts**")

            if st.button("📅 " + t("Enviar para Eventos", "Send to Events"), key="send_beh_plan_evt"):
                st.session_state["_src_behemoth_Relic_Race"]        = int(pts_rr)
                st.session_state["_calc_contrib_Relic_Race_0"]      = int(pts_rr_mag)
                st.session_state["_calc_contrib_Relic_Race_1"]      = int(pts_rr_core)
                st.session_state["_calc_contrib_Relic_Race_2"]      = int(pts_rr_seal)
                st.session_state["_calc_sent_Relic_Race"]           = True
                st.session_state["_src_behemoth_Hero_Development"]  = int(pts_hd)
                st.session_state["_calc_contrib_Hero_Development_7"]= int(pts_hd_mag)
                st.session_state["_calc_contrib_Hero_Development_8"]= int(pts_hd_core)
                st.session_state["_calc_contrib_Hero_Development_9"]= int(pts_hd_seal)
                st.session_state["_calc_sent_Hero_Development"]     = True
                st.success(t("✅ Enviado!", "✅ Sent!"))

        st.markdown("---")
        if st.button("🗑️ " + t("Limpar plano", "Clear plan"), key="plan_clear"):
            st.session_state["behemoth_plan"] = []
            st.session_state.pop("_src_behemoth_Relic_Race", None)
            st.session_state.pop("_src_behemoth_Hero_Development", None)
            st.session_state["_calc_sent_Relic_Race"]       = False
            st.session_state["_calc_sent_Hero_Development"] = False
            _beh_save()
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — REFERENCE
# ══════════════════════════════════════════════════════════════════════════════
with tab_ref:
    ref1, ref2 = st.columns(2, gap="large")

    with ref1:
        st.subheader(t("🔮 Custo por Nível (Magicite)", "🔮 Level Costs (Magicite)"))
        st.caption(t(
            "Magicite necessário para avançar até cada nível (por facção). "
            "Níveis com 💠 exigem Núcleos Mágicos (universais).",
            "Magicite needed to advance to each level (per faction). "
            "Levels with 💠 require Magic Cores (universal).",
        ))
        rows_lvl = []
        for lvl in range(2, MAX_LEVEL + 1):
            mag  = MAGICITE_PER_LEVEL.get(lvl, 0)
            core = MAGIC_CORE_AT_LEVEL.get(lvl)
            cell = f"{mag:,}"
            if core:
                cell += f"  +  💠 {core:,}"
            rows_lvl.append({"#": lvl, t("Magicite", "Magicite"): cell})
        df_lvl = pd.DataFrame(rows_lvl).set_index("#")
        st.dataframe(df_lvl, use_container_width=True, height=400)

    with ref2:
        st.subheader(t("🔑 Custo por Estrela (Selos)", "🔑 Star Costs (Seals)"))
        st.caption(t(
            "Selos necessários para cada estrela (específicos ou universais).",
            "Seals needed for each star (specific or universal).",
        ))
        rows_star = []
        cumulative = 0
        for i, cost in enumerate(STAR_SEAL_COSTS):
            cumulative += cost
            rows_star.append({
                "⭐": i + 1,
                t("Selos", "Seals"): cost,
                t("Acumulado", "Cumulative"): cumulative,
            })
        df_star = pd.DataFrame(rows_star).set_index("⭐")
        st.dataframe(df_star, use_container_width=True, height=400)
