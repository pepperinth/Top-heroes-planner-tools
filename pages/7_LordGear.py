"""
pages/7_LordGear.py — Lord Gear & Sacred Codex Calculator.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from lord_gear_engine import (
    GEAR_MILESTONES, GEAR_LEVEL_OPTS_PT, GEAR_LEVEL_OPTS_EN,
    GEAR_PIECES, GEAR_PIECE_NAMES_PT, GEAR_PIECE_NAMES_EN,
    TIER_BADGE, TIER_COLOR,
    MAX_GEAR_LEVEL, MAX_CODEX_STARS,
    CODEX_STAR_COSTS,
    get_gear_piece,
    calc_gear_resources, calc_codex_resources, calc_combined, calc_event_pts,
    show_resource_image, show_codex_image,
)
from behemoth_engine import FACTION_ICONS, FACTION_ICON_DIR
from ui_utils import inject_global_css, section_header, results_header, FACTION_COLORS

_BASE = os.path.dirname(os.path.dirname(__file__))

st.set_page_config(page_title="Lord Gear", page_icon="⚙️", layout="wide")

# ── Language ───────────────────────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "pt"

with st.sidebar:
    st.markdown("### 🌐 Idioma / Language")
    lang_pick = st.radio(
        "", ["🇧🇷 Português", "🇬🇧 English"],
        index=0 if st.session_state.lang == "pt" else 1,
        horizontal=True, label_visibility="collapsed", key="lang_lordgear",
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

# ── Helpers ────────────────────────────────────────────────────────────────────
_LEVEL_OPTS = GEAR_LEVEL_OPTS_PT if lang == "pt" else GEAR_LEVEL_OPTS_EN

def _faction_icon(faction: str, width: int = 36):
    path = os.path.join(_BASE, FACTION_ICON_DIR, FACTION_ICONS[faction])
    st.image(path, width=width)

def _gear_selector(key: str, label: str, default_idx: int = 0) -> dict:
    names = GEAR_PIECE_NAMES_PT if lang == "pt" else GEAR_PIECE_NAMES_EN
    sel   = st.selectbox(label, names, index=default_idx, key=key)
    piece = GEAR_PIECES[names.index(sel)]
    ci, cn = st.columns([1, 6])
    with ci:
        _faction_icon(piece["faction"], width=32)
    with cn:
        faction_name = piece["faction"] if lang == "pt" else piece["faction_en"]
        type_name    = piece["type_pt"] if lang == "pt" else piece["type_en"]
        tier_col     = "#888888"
        st.caption(f"**{faction_name}** · {type_name}")
    return piece

def _level_idx(opt: str) -> int:
    return _LEVEL_OPTS.index(opt)

def _tier_badge(level_idx: int) -> str:
    return TIER_BADGE[GEAR_MILESTONES[level_idx][4]]

def _tier_color(level_idx: int) -> str:
    return TIER_COLOR[GEAR_MILESTONES[level_idx][4]]

def _level_name(level_idx: int) -> str:
    return GEAR_MILESTONES[level_idx][1] if lang == "pt" else GEAR_MILESTONES[level_idx][2]

def _net_label(inv: int, needed: int) -> str:
    if inv == 0:
        return ""
    net = max(0, needed - inv)
    if net == 0:
        return "✅ " + t("Suficiente", "Sufficient")
    return f"⚠️ {t('Faltam','Still need')} {net:,}"

def _render_metric_net(label: str, needed: int, inv: int):
    delta = f"−{inv:,} " + t("em estoque", "in stock") if inv > 0 else None
    st.metric(label, f"{needed:,}", delta=delta,
              delta_color="inverse" if inv > 0 else "off")
    msg = _net_label(inv, needed)
    if msg:
        st.success(msg) if msg.startswith("✅") else st.warning(msg)

def _render_event_impact(rm: int, mt: int, ori: int, db: int, send_key: str):
    pts = calc_event_pts(rm, mt, ori, db)
    total = pts["total"]
    if total == 0:
        st.info(t("Sem recursos a gastar — nenhum impacto no evento.",
                  "No resources to spend — no event impact."))
        return

    st.subheader("📅 " + t("Impacto nos Eventos Regulares", "Regular Event Impact"))
    st.markdown(f"**⚙️ {t('Desafio de Equipamento do Lorde','Lord Gear Trial')}**")

    ec1, ec2, ec3, ec4 = st.columns(4)
    with ec1:
        show_resource_image("rm", _BASE, st)
        st.metric(t("Metal Refinado", "Refined Metal"),
                  f"{pts['rm']:,.0f} pts", f"×0.1/u · {rm:,}")
    with ec2:
        show_resource_image("mt", _BASE, st)
        st.metric(t("Fio Mágico", "Magic Thread"),
                  f"{pts['mt']:,.0f} pts", f"×10/u · {mt:,}")
    with ec3:
        show_resource_image("ori", _BASE, st)
        st.metric("Oricalco / Orichalcum",
                  f"{pts['ori']:,.0f} pts", f"×15/u · {ori:,}")
    with ec4:
        show_resource_image("db", _BASE, st)
        st.metric(t("Sangue de Dragão", "Dragon Blood"),
                  f"{pts['db']:,.0f} pts", f"×60/u · {db:,}")

    st.markdown(f"**{t('Total estimado','Estimated total')}: {total:,.0f} pts**")

    if st.button("📅 " + t("Enviar para Eventos", "Send to Events"), key=send_key):
        st.session_state["_src_lord_gear_Lord_Gear_Trial"]         = int(total)
        st.session_state["_calc_contrib_Lord_Gear_Trial_0"]        = int(pts["rm"])
        st.session_state["_calc_contrib_Lord_Gear_Trial_1"]        = int(pts["mt"])
        st.session_state["_calc_contrib_Lord_Gear_Trial_2"]        = int(pts["ori"])
        st.session_state["_calc_contrib_Lord_Gear_Trial_3"]        = int(pts["db"])
        st.session_state["_calc_sent_Lord_Gear_Trial"]             = True
        st.success(t("✅ Enviado! Acesse Eventos Regulares para ver o impacto.",
                     "✅ Sent! Go to Regular Events to see the impact."))

# ── Header ─────────────────────────────────────────────────────────────────────
inject_global_css()
st.title("⚙️ " + t("Equipamento do Lorde & Códex Sagrado", "Lord Gear & Sacred Codex"))
st.caption(t(
    "Calcula Metal Refinado, Fio Mágico, Oricalco e Sangue de Dragão para evoluir o Equipamento do Lorde e o Códex Sagrado.",
    "Calculates Refined Metal, Magic Thread, Orichalcum and Dragon Blood to upgrade Lord Gear and Sacred Codex.",
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

    # ── Gear piece selector ───────────────────────────────────────────────────
    st.subheader("⚙️ " + t("Selecione o Equipamento do Lorde", "Select Lord Gear"))
    piece = _gear_selector("calc_piece_sel", t("Equipamento", "Equipment"))
    st.markdown("---")

    # ── Current / Target columns ──────────────────────────────────────────────
    col_cur, col_tgt = st.columns(2, gap="large")

    with col_cur:
        st.subheader("📍 " + t("Estado Atual", "Current State"))
        cur_gear_sel = st.selectbox(
            t("Nível atual do Equipamento do Lorde", "Current Lord Gear level"),
            _LEVEL_OPTS, index=0, key="calc_cur_gear",
        )
        cur_gear = _level_idx(cur_gear_sel)
        st.caption(
            f"{_tier_badge(cur_gear)} {_level_name(cur_gear)}",
        )

        st.markdown("")
        show_codex_image(_BASE, st, height=22)
        cur_codex = st.number_input(
            t("Estrelas atuais do Códex Sagrado", "Current Sacred Codex stars"),
            min_value=0, max_value=MAX_CODEX_STARS, value=0, step=1,
            key="calc_cur_codex",
        )

    with col_tgt:
        st.subheader("🎯 " + t("Estado Alvo", "Target State"))
        tgt_gear_sel = st.selectbox(
            t("Nível alvo do Equipamento do Lorde", "Target Lord Gear level"),
            _LEVEL_OPTS, index=MAX_GEAR_LEVEL, key="calc_tgt_gear",
        )
        tgt_gear = _level_idx(tgt_gear_sel)
        st.caption(
            f"{_tier_badge(tgt_gear)} {_level_name(tgt_gear)}",
        )

        st.markdown("")
        show_codex_image(_BASE, st, height=22)
        tgt_codex = st.number_input(
            t("Estrelas alvo do Códex Sagrado", "Target Sacred Codex stars"),
            min_value=0, max_value=MAX_CODEX_STARS, value=MAX_CODEX_STARS, step=1,
            key="calc_tgt_codex",
        )

    # ── Inventory ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🎒 " + t("Inventário (opcional)", "Inventory (optional)"))
    st.caption(t(
        "Todos os recursos são universais — não há separação por facção.",
        "All resources are universal — no faction split.",
    ))

    ic1, ic2, ic3, ic4 = st.columns(4)
    with ic1:
        show_resource_image("rm", _BASE, st)
        inv_rm = st.number_input(t("Metal Refinado", "Refined Metal"),
                                 min_value=0, value=0, step=100, key="calc_inv_rm")
    with ic2:
        show_resource_image("mt", _BASE, st)
        inv_mt = st.number_input(t("Fio Mágico", "Magic Thread"),
                                 min_value=0, value=0, step=1, key="calc_inv_mt")
    with ic3:
        show_resource_image("ori", _BASE, st)
        inv_ori = st.number_input("Oricalco / Orichalcum",
                                  min_value=0, value=0, step=1, key="calc_inv_ori")
    with ic4:
        show_resource_image("db", _BASE, st)
        inv_db = st.number_input(t("Sangue de Dragão", "Dragon Blood"),
                                 min_value=0, value=0, step=1, key="calc_inv_db")

    # ── Validation ────────────────────────────────────────────────────────────
    st.markdown("---")
    errors = []
    if tgt_gear < cur_gear:
        errors.append(t("⚠️ Nível alvo deve ser ≥ nível atual.",
                        "⚠️ Target level must be ≥ current level."))
    if tgt_codex < cur_codex:
        errors.append(t("⚠️ Estrelas alvo do Codex devem ser ≥ atuais.",
                        "⚠️ Target Codex stars must be ≥ current stars."))
    for e in errors:
        st.error(e)

    if not errors:
        res  = calc_combined(cur_gear, tgt_gear, cur_codex, tgt_codex)
        g_res = calc_gear_resources(cur_gear, tgt_gear)
        c_res = calc_codex_resources(cur_codex, tgt_codex)

        nothing = (tgt_gear == cur_gear and tgt_codex == cur_codex)

        if nothing:
            st.info(t("Nível e estrelas alvo iguais ao atual. Nada a calcular.",
                      "Target matches current state. Nothing to calculate."))
        else:
            results_header(f"📊 {t('Resumo de Recursos','Resource Summary')}", piece["faction"])

            # Total combined metrics
            mc1, mc2, mc3, mc4 = st.columns(4)
            with mc1:
                show_resource_image("rm", _BASE, st)
                _render_metric_net(t("Metal Refinado necessário", "Refined Metal needed"),
                                   res["rm"], inv_rm)
            with mc2:
                show_resource_image("mt", _BASE, st)
                _render_metric_net(t("Fio Mágico necessário", "Magic Thread needed"),
                                   res["mt"], inv_mt)
            with mc3:
                show_resource_image("ori", _BASE, st)
                _render_metric_net(t("Oricalco necessário", "Orichalcum needed"),
                                   res["ori"], inv_ori)
            with mc4:
                show_resource_image("db", _BASE, st)
                _render_metric_net(t("Sangue de Dragão necessário", "Dragon Blood needed"),
                                   res["db"], inv_db)

            # Breakdown if both components are non-zero
            if (tgt_gear != cur_gear) and (tgt_codex != cur_codex):
                with st.expander(t("📋 Detalhamento por componente", "📋 Breakdown by component")):
                    dc1, dc2 = st.columns(2)
                    with dc1:
                        st.markdown(f"**⚙️ {t('Equipamento do Lorde','Lord Gear')}** ({_level_name(cur_gear)} → {_level_name(tgt_gear)})")
                        bk1, bk2, bk3, bk4 = st.columns(4)
                        with bk1:
                            show_resource_image("rm", _BASE, st)
                            st.caption(f"{g_res['rm']:,}")
                        with bk2:
                            show_resource_image("mt", _BASE, st)
                            st.caption(f"{g_res['mt']:,}")
                        with bk3:
                            show_resource_image("ori", _BASE, st)
                            st.caption(f"{g_res['ori']:,}")
                        with bk4:
                            show_resource_image("db", _BASE, st)
                            st.caption(f"{g_res['db']:,}")
                    with dc2:
                        st.markdown(f"**📜 {t('Códex Sagrado','Sacred Codex')}** (★{cur_codex} → ★{tgt_codex})")
                        bk1, bk2, bk3 = st.columns(3)
                        with bk1:
                            show_resource_image("mt", _BASE, st)
                            st.caption(f"{c_res['mt']:,}")
                        with bk2:
                            show_resource_image("ori", _BASE, st)
                            st.caption(f"{c_res['ori']:,}")
                        with bk3:
                            show_resource_image("db", _BASE, st)
                            st.caption(f"{c_res['db']:,}")

            # Level-by-level breakdown
            if tgt_gear != cur_gear:
                with st.expander(t("⚙️ Detalhamento por nível", "⚙️ Level-by-level breakdown")):
                    rows_lv = []
                    for i in range(cur_gear + 1, tgt_gear + 1):
                        r = calc_gear_resources(i - 1, i)
                        rows_lv.append({
                            t("Nível", "Level"): _LEVEL_OPTS[i],
                            "RM": f"{r['rm']:,}",
                            "MT": f"{r['mt']:,}",
                            "Ori": f"{r['ori']:,}",
                            "DB": f"{r['db']:,}",
                        })
                    _lv_hdr = st.columns([3, 1, 1, 1, 1])
                    for col, label in zip(_lv_hdr[1:], ["rm", "mt", "ori", "db"]):
                        with col:
                            show_resource_image(label, _BASE, st)
                    st.dataframe(pd.DataFrame(rows_lv), use_container_width=True, hide_index=True)

            # Codex star breakdown
            if tgt_codex != cur_codex:
                with st.expander(t("📜 Detalhamento por estrela (Códex Sagrado)", "📜 Star-by-star (Sacred Codex)")):
                    rows_cx = []
                    for i in range(cur_codex, tgt_codex):
                        e = CODEX_STAR_COSTS[i]
                        rows_cx.append({
                            "★": e[0],
                            "MT": e[1],
                            "Ori": e[2],
                            "DB": e[3],
                        })
                    _cx_hdr = st.columns([1, 1, 1, 1])
                    for col, label in zip(_cx_hdr[1:], ["mt", "ori", "db"]):
                        with col:
                            show_resource_image(label, _BASE, st)
                    st.dataframe(pd.DataFrame(rows_cx), use_container_width=True, hide_index=True)

            # ── Event Impact ──────────────────────────────────────────────────
            st.markdown("---")
            _render_event_impact(res["rm"], res["mt"], res["ori"], res["db"],
                                 send_key="send_gear_calc_evt")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — BATCH PLANNER
# ══════════════════════════════════════════════════════════════════════════════
with tab_plan:

    if "lordgear_plan" not in st.session_state:
        st.session_state["lordgear_plan"] = []

    plan: list[dict] = st.session_state["lordgear_plan"]

    # ── Add entry ─────────────────────────────────────────────────────────────
    st.subheader("➕ " + t("Adicionar ao plano", "Add to plan"))

    entry_type = st.radio(
        t("Tipo de entrada", "Entry type"),
        [t("Equipamento do Lorde", "Lord Gear"), t("Códex Sagrado", "Sacred Codex")],
        horizontal=True, key="plan_entry_type",
    )
    is_codex = entry_type == t("Códex Sagrado", "Sacred Codex")

    if not is_codex:
        pa1, pa2 = st.columns([2, 3], gap="large")
        with pa1:
            plan_piece = _gear_selector("plan_piece_sel", t("Equipamento", "Equipment"))
        with pa2:
            lc1, lc2 = st.columns(2)
            with lc1:
                p_cur_gear_sel = st.selectbox(t("Nível atual", "Current level"),
                    _LEVEL_OPTS, index=0, key="plan_cur_gear")
                p_cur_gear = _level_idx(p_cur_gear_sel)
            with lc2:
                p_tgt_gear_sel = st.selectbox(t("Nível alvo", "Target level"),
                    _LEVEL_OPTS, index=MAX_GEAR_LEVEL, key="plan_tgt_gear")
                p_tgt_gear = _level_idx(p_tgt_gear_sel)

        plan_errors = []
        if p_tgt_gear < p_cur_gear:
            plan_errors.append(t("Nível alvo deve ser ≥ nível atual.",
                                 "Target level must be ≥ current level."))
        for e in plan_errors:
            st.error(e)

        if not plan_errors:
            if st.button("➕ " + t("Adicionar", "Add"), key="plan_add_gear"):
                r = calc_gear_resources(p_cur_gear, p_tgt_gear)
                plan.append({
                    "type":     "gear",
                    "piece":    plan_piece["name_pt"],
                    "faction":  plan_piece["faction"],
                    "f_en":     plan_piece["faction_en"],
                    "type_pt":  plan_piece["type_pt"],
                    "type_en":  plan_piece["type_en"],
                    "cur":      p_cur_gear,
                    "tgt":      p_tgt_gear,
                    "rm":       r["rm"],
                    "mt":       r["mt"],
                    "ori":      r["ori"],
                    "db":       r["db"],
                })
                st.rerun()
    else:
        show_codex_image(_BASE, st, height=22)
        cx1, cx2 = st.columns(2)
        with cx1:
            p_cur_codex = st.number_input(t("Estrelas atuais", "Current stars"),
                min_value=0, max_value=MAX_CODEX_STARS, value=0, step=1, key="plan_cur_codex")
        with cx2:
            p_tgt_codex = st.number_input(t("Estrelas alvo", "Target stars"),
                min_value=0, max_value=MAX_CODEX_STARS, value=MAX_CODEX_STARS, step=1,
                key="plan_tgt_codex")

        if p_tgt_codex < p_cur_codex:
            st.error(t("Estrelas alvo devem ser ≥ atuais.", "Target stars must be ≥ current."))
        else:
            if st.button("➕ " + t("Adicionar Codex", "Add Codex"), key="plan_add_codex"):
                r = calc_codex_resources(p_cur_codex, p_tgt_codex)
                plan.append({
                    "type":    "codex",
                    "piece":   t("Códex Sagrado", "Sacred Codex"),
                    "faction": "—",
                    "f_en":    "—",
                    "type_pt": "Códex",
                    "type_en": "Codex",
                    "cur":     p_cur_codex,
                    "tgt":     p_tgt_codex,
                    "rm":      0,
                    "mt":      r["mt"],
                    "ori":     r["ori"],
                    "db":      r["db"],
                })
                st.rerun()

    # ── Plan table ────────────────────────────────────────────────────────────
    st.markdown("---")

    if not plan:
        st.info(t("Plano vazio. Adicione entradas acima.",
                  "Plan is empty. Add entries above."))
    else:
        section_header(f"📋 {t('Plano atual','Current plan')}")

        rows_tbl = []
        for i, e in enumerate(plan):
            faction_disp = e["faction"] if lang == "pt" else e["f_en"]
            type_disp    = e["type_pt"] if lang == "pt" else e["type_en"]
            if e["type"] == "gear":
                cur_label = _LEVEL_OPTS[e["cur"]]
                tgt_label = _LEVEL_OPTS[e["tgt"]]
            else:
                cur_label = f"★{e['cur']}"
                tgt_label = f"★{e['tgt']}"
            rows_tbl.append({
                "#": i + 1,
                t("Equipamento", "Equipment"): e["piece"],
                t("Facção", "Faction"): faction_disp,
                t("Tipo", "Type"): type_disp,
                t("De → Para", "From → To"): f"{cur_label} → {tgt_label}",
                "RM": f"{e['rm']:,}",
                "MT": f"{e['mt']:,}",
                "Ori": f"{e['ori']:,}",
                "DB": f"{e['db']:,}",
            })
        df = pd.DataFrame(rows_tbl).set_index("#")
        st.dataframe(df, use_container_width=True)

        rem_idx = st.number_input(t("Remover entrada #", "Remove entry #"),
            min_value=1, max_value=len(plan), value=1, step=1, key="plan_rem_idx")
        if st.button(t("🗑️ Remover", "🗑️ Remove"), key="plan_rem"):
            plan.pop(rem_idx - 1)
            st.rerun()

        # ── Totals ────────────────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("📊 " + t("Totais", "Totals"))

        total_rm  = sum(e["rm"]  for e in plan)
        total_mt  = sum(e["mt"]  for e in plan)
        total_ori = sum(e["ori"] for e in plan)
        total_db  = sum(e["db"]  for e in plan)

        st.markdown(f"**🎒 {t('Inventário do plano','Plan inventory')}**")
        pi1, pi2, pi3, pi4 = st.columns(4)
        with pi1:
            show_resource_image("rm", _BASE, st)
            inv_rm_p = st.number_input(t("Metal Refinado", "Refined Metal"),
                min_value=0, value=0, step=100, key="plan_inv_rm")
        with pi2:
            show_resource_image("mt", _BASE, st)
            inv_mt_p = st.number_input(t("Fio Mágico", "Magic Thread"),
                min_value=0, value=0, step=1, key="plan_inv_mt")
        with pi3:
            show_resource_image("ori", _BASE, st)
            inv_ori_p = st.number_input("Oricalco / Orichalcum",
                min_value=0, value=0, step=1, key="plan_inv_ori")
        with pi4:
            show_resource_image("db", _BASE, st)
            inv_db_p = st.number_input(t("Sangue de Dragão", "Dragon Blood"),
                min_value=0, value=0, step=1, key="plan_inv_db")

        st.markdown("")
        tm1, tm2, tm3, tm4 = st.columns(4)
        with tm1:
            show_resource_image("rm", _BASE, st)
            _render_metric_net(t("Metal Refinado total", "Total Refined Metal"),
                               total_rm, inv_rm_p)
        with tm2:
            show_resource_image("mt", _BASE, st)
            _render_metric_net(t("Fio Mágico total", "Total Magic Thread"),
                               total_mt, inv_mt_p)
        with tm3:
            show_resource_image("ori", _BASE, st)
            _render_metric_net(t("Oricalco total", "Total Orichalcum"),
                               total_ori, inv_ori_p)
        with tm4:
            show_resource_image("db", _BASE, st)
            _render_metric_net(t("Sangue de Dragão total", "Total Dragon Blood"),
                               total_db, inv_db_p)

        # ── Event Impact ──────────────────────────────────────────────────────
        if total_rm + total_mt + total_ori + total_db > 0:
            st.markdown("---")
            _render_event_impact(total_rm, total_mt, total_ori, total_db,
                                 send_key="send_gear_plan_evt")

        st.markdown("---")
        if st.button("🗑️ " + t("Limpar plano", "Clear plan"), key="plan_clear"):
            st.session_state["lordgear_plan"] = []
            st.session_state.pop("_src_lord_gear_Lord_Gear_Trial", None)
            st.session_state["_calc_sent_Lord_Gear_Trial"] = False
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — REFERENCE
# ══════════════════════════════════════════════════════════════════════════════
with tab_ref:
    ref1, ref2 = st.columns(2, gap="large")

    with ref1:
        st.subheader(t("⚙️ Custo por Nível (Equipamento do Lorde)", "⚙️ Cost per Level (Lord Gear)"))
        st.caption(t(
            "Custo acumulado de cada milestone a partir do anterior.",
            "Incremental cost of each milestone from the previous one.",
        ))
        _ref_hdr = st.columns([3, 1, 1, 1, 1])
        for col, label in zip(_ref_hdr[1:], ["rm", "mt", "ori", "db"]):
            with col:
                show_resource_image(label, _BASE, st)
        ref_rows = []
        for i in range(1, len(GEAR_MILESTONES)):
            res = calc_gear_resources(i - 1, i)
            tier = GEAR_MILESTONES[i][4]
            badge = TIER_BADGE[tier]
            name = GEAR_MILESTONES[i][1] if lang == "pt" else GEAR_MILESTONES[i][2]
            ref_rows.append({
                "#": i,
                t("Nível", "Level"): f"{badge} {name}",
                "RM": f"{res['rm']:,}" if res['rm'] else "—",
                "MT": f"{res['mt']:,}" if res['mt'] else "—",
                "Ori": f"{res['ori']:,}" if res['ori'] else "—",
                "DB": f"{res['db']:,}" if res['db'] else "—",
            })
        st.dataframe(pd.DataFrame(ref_rows).set_index("#"),
                     use_container_width=True, height=600)

    with ref2:
        st.subheader(t("📜 Custo por Estrela (Códex Sagrado)", "📜 Star Cost (Sacred Codex)"))
        st.caption(t(
            "Sem Metal Refinado — Códex Sagrado usa apenas MT, Oricalco e Sangue de Dragão.",
            "No Refined Metal — Sacred Codex uses only MT, Orichalcum and Dragon Blood.",
        ))
        _cx_ref_hdr = st.columns([1, 1, 1, 1, 1, 1, 1])
        for col, label in zip(_cx_ref_hdr[1:4], ["mt", "ori", "db"]):
            with col:
                show_resource_image(label, _BASE, st)
        for col, label in zip(_cx_ref_hdr[4:], ["mt", "ori", "db"]):
            with col:
                show_resource_image(label, _BASE, st)
        acum = t("Acum.", "Cum.")
        codex_rows = []
        cum_mt = cum_ori = cum_db = 0
        for e in CODEX_STAR_COSTS:
            cum_mt += e[1]; cum_ori += e[2]; cum_db += e[3]
            codex_rows.append({
                "★": e[0],
                "MT": e[1],
                "Ori": e[2],
                "DB": e[3] if e[3] else "—",
                f"MT {acum}": cum_mt,
                f"Ori {acum}": cum_ori,
                f"DB {acum}": cum_db,
            })
        st.dataframe(pd.DataFrame(codex_rows).set_index("★"),
                     use_container_width=True, height=600)
