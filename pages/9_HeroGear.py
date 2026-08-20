"""
pages/9_HeroGear.py — Hero Gear & Promotion Calculator.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd

from hero_gear_engine import (
    GEAR_SETS, GEAR_SET_NAMES_PT, GEAR_SET_NAMES_EN, GEAR_SET_COLORS,
    GEAR_PIECES_PT, GEAR_PIECES_EN, GEAR_PIECE_ICONS,
    MAX_GEAR_LEVEL, MAX_PROMOTION,
    GEAR_LV_RUNE, GEAR_LV_RUBY, GEAR_LV_CUMUL_RUNE, GEAR_LV_CUMUL_RUBY,
    PROMO_STEP_COSTS,
    PROMO_CUMUL_RUNE, PROMO_CUMUL_GOLD, PROMO_CUMUL_RUBY,
    PROMO_CUMUL_LEG, PROMO_CUMUL_MYTH,
    show_resource_image, gear_level_cost, gear_promo_cost,
    promo_label, promo_star_idx, calc_gear_piece,
)
from behemoth_engine import show_star_image, FACTION_ICONS, FACTION_ICON_DIR
from ui_utils import inject_global_css, results_header
import persistence

_BASE = os.path.dirname(os.path.dirname(__file__))

st.set_page_config(page_title="Hero Gear", page_icon="⚔️", layout="wide")

# ── Persistence: init manager and load saved state on first run ────────────────
_cm = persistence.new_manager("herogear")

if "hg_initialized" not in st.session_state:
    _saved = persistence.load(_cm, "th_herogear")
    if _saved:
        _inv = _saved.get("inventory", {})
        st.session_state["hg_inv_rune"]  = int(_inv.get("enh_rune", 0))
        st.session_state["hg_inv_ruby"]  = int(_inv.get("ruby", 0))
        st.session_state["hg_inv_gold"]  = int(_inv.get("gold_bar", 0))
        st.session_state["hg_inv_leg"]   = int(_inv.get("leg_stone", 0))
        st.session_state["hg_inv_myth"]  = int(_inv.get("myth_stone", 0))
        st.session_state["hg_inv_marks"] = int(_inv.get("marks", 0))
        _restored = []
        for _e in _saved.get("plan", []):
            try:
                _res = calc_gear_piece(
                    _e["from_lv"], _e["to_lv"],
                    _e["from_promo"], _e["to_promo"],
                    _e.get("needs_mark", False),
                )
                _restored.append({**_e, "res": _res})
            except Exception:
                pass
        st.session_state["hg_plan"] = _restored
    st.session_state["hg_initialized"] = True


def _hg_save():
    """Persist current inventory + plan to the browser cookie."""
    persistence.save(_cm, "th_herogear", {
        "inventory": {
            "enh_rune":  st.session_state.get("hg_inv_rune", 0),
            "ruby":      st.session_state.get("hg_inv_ruby", 0),
            "gold_bar":  st.session_state.get("hg_inv_gold", 0),
            "leg_stone": st.session_state.get("hg_inv_leg", 0),
            "myth_stone":st.session_state.get("hg_inv_myth", 0),
            "marks":     st.session_state.get("hg_inv_marks", 0),
        },
        "plan": [
            {k: v for k, v in _e.items() if k != "res"}
            for _e in st.session_state.get("hg_plan", [])
        ],
    })


# ── Language ───────────────────────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "en"

with st.sidebar:
    st.markdown("### 🌐 Idioma / Language")
    lang_pick = st.radio(
        "", ["🇧🇷 Português", "🇬🇧 English"],
        index=0 if st.session_state.lang == "pt" else 1,
        horizontal=True, label_visibility="collapsed", key="lang_herogear",
    )
    st.session_state.lang = "pt" if "Português" in lang_pick else "en"
    st.divider()

    st.markdown("### 📦 " + ("Inventário" if st.session_state.lang == "pt" else "Inventory"))
    inv_rune  = st.number_input("🔷 Enhancement Rune", min_value=0, value=0,
                                step=1000, key="hg_inv_rune", on_change=_hg_save)
    inv_ruby  = st.number_input("🔴 Ruby", min_value=0, value=0,
                                step=1000, key="hg_inv_ruby", on_change=_hg_save)
    inv_gold  = st.number_input("🟡 Gold Bar", min_value=0, value=0,
                                step=10, key="hg_inv_gold", on_change=_hg_save)
    inv_leg   = st.number_input("🟠 " + ("Pedra Lendária" if st.session_state.lang == "pt" else "Legendary Stone"),
                                min_value=0, value=0, step=1, key="hg_inv_leg", on_change=_hg_save)
    inv_myth  = st.number_input("🔴 " + ("Pedra Mítica" if st.session_state.lang == "pt" else "Mythic Stone"),
                                min_value=0, value=0, step=1, key="hg_inv_myth", on_change=_hg_save)
    inv_marks = st.number_input(
        "🔖 " + ("Marcas Universais" if st.session_state.lang == "pt" else "Universal Marks"),
        min_value=0, value=0, step=1, key="hg_inv_marks", on_change=_hg_save,
    )
    st.caption("🍪 " + (
        "Inventário e lotes são salvos no seu browser."
        if st.session_state.lang == "pt" else
        "Inventory and batches are saved in your browser."
    ))
    st.divider()
    st.page_link("app.py", label="← Home")
    st.warning(
        "⚠️ **Versão Beta**\nAlgumas funcionalidades podem estar incompletas."
        if st.session_state.lang == "pt" else
        "⚠️ **Beta Version**\nSome features may be incomplete."
    )

lang = st.session_state.lang
def t(pt, en): return pt if lang == "pt" else en

# ── Session state ──────────────────────────────────────────────────────────────
if "hg_plan" not in st.session_state:
    st.session_state["hg_plan"] = []
if "calc_hg_set" not in st.session_state:
    st.session_state["calc_hg_set"] = GEAR_SETS[0]
if "calc_hg_piece" not in st.session_state:
    st.session_state["calc_hg_piece"] = GEAR_PIECES_PT[0]

# ── Header ─────────────────────────────────────────────────────────────────────
inject_global_css()
st.title("⚔️ " + t("Equipamentos do Herói", "Hero Gear"))
st.caption(t(
    "Calcula Enhancement Runes, Rubies, Gold Bars e Pedras para nivelar e promover equipamentos.",
    "Calculates Enhancement Runes, Rubies, Gold Bars and Stones to level and promote gear.",
))

tab_calc, tab_batch, tab_ref = st.tabs([
    "🧮 " + t("Calculadora", "Calculator"),
    "📋 " + t("Planejador de Lote", "Batch Planner"),
    "📖 " + t("Referência", "Reference"),
])

# ── Shared helpers ─────────────────────────────────────────────────────────────
def _show_promo_star(step: int):
    show_star_image(promo_star_idx(step), _BASE, st)

def _promo_sel(label: str, key: str, default: int = 0, disabled: bool = False) -> int:
    return st.selectbox(
        label,
        range(MAX_PROMOTION + 1),
        format_func=lambda s: promo_label(s, lang),
        index=default,
        key=key,
        disabled=disabled,
    )

def _inv_compare(needed: dict, label: str):
    """Show inventory vs needed table if inventory has any values set."""
    _inv = {
        "enh_rune":   inv_rune,
        "ruby":       inv_ruby,
        "gold_bars":  inv_gold,
        "leg_stones": inv_leg,
        "myth_stones":inv_myth,
        "marks":      inv_marks,
    }
    _labels = {
        "enh_rune":    t("Runa de Aprimoramento", "Enhancement Rune"),
        "ruby":        "Ruby",
        "gold_bars":   t("Barra de Ouro", "Gold Bar"),
        "leg_stones":  t("Pedra Lendária", "Legendary Stone"),
        "myth_stones": t("Pedra Mítica", "Mythic Stone"),
        "marks":       t("Marca Universal", "Universal Mark"),
    }
    if not any(v > 0 for v in _inv.values()):
        return
    _rows = []
    for _k, _lbl in _labels.items():
        _need = needed.get(_k, 0)
        if _need == 0:
            continue
        _have = _inv[_k]
        _diff = _have - _need
        _rows.append({
            t("Recurso", "Resource"): _lbl,
            t("Necessário", "Needed"): f"{_need:,}",
            t("Tem", "Have"): f"{_have:,}",
            t("Saldo", "Balance"): ("✅ +" if _diff >= 0 else "❌ ") + f"{abs(_diff):,}",
        })
    if _rows:
        st.markdown(f"**📦 {label}**")
        st.dataframe(pd.DataFrame(_rows), use_container_width=True, hide_index=True)

set_names = GEAR_SET_NAMES_PT if lang == "pt" else GEAR_SET_NAMES_EN
pieces_disp = GEAR_PIECES_PT if lang == "pt" else GEAR_PIECES_EN

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — CALCULADORA
# ══════════════════════════════════════════════════════════════════════════════
with tab_calc:
    st.subheader("⚔️ " + t("Selecionar Set e Peça", "Select Set and Piece"))

    # Set selector
    _sc = st.columns(3)
    for _i, _s in enumerate(GEAR_SETS):
        with _sc[_i]:
            _is_sel = st.session_state["calc_hg_set"] == _s
            if st.button(set_names[_s], key=f"hg_set_{_s}",
                         use_container_width=True,
                         type="primary" if _is_sel else "secondary"):
                st.session_state["calc_hg_set"] = _s
                st.rerun()

    # Piece selector
    _pc = st.columns(4)
    for _i, (_pt, _en, _ic) in enumerate(zip(GEAR_PIECES_PT, GEAR_PIECES_EN, GEAR_PIECE_ICONS)):
        with _pc[_i]:
            _is_sel = st.session_state["calc_hg_piece"] == _pt
            _pname  = _pt if lang == "pt" else _en
            if st.button(f"{_ic} {_pname}", key=f"hg_piece_{_pt}",
                         use_container_width=True,
                         type="primary" if _is_sel else "secondary"):
                st.session_state["calc_hg_piece"] = _pt
                st.rerun()

    sel_set   = st.session_state["calc_hg_set"]
    sel_piece = st.session_state["calc_hg_piece"]
    _pi       = GEAR_PIECES_PT.index(sel_piece)
    piece_disp = GEAR_PIECES_EN[_pi] if lang == "en" else sel_piece
    _sc2 = GEAR_SET_COLORS[sel_set]

    st.markdown(
        f'<div class="th-banner" style="border-left:5px solid {_sc2}; background:{_sc2}18;">'
        f'<b>{set_names[sel_set]}</b>'
        f'<span style="color:#555; font-size:0.9em;"> · {GEAR_PIECE_ICONS[_pi]} {piece_disp}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Destination for batch ─────────────────────────────────────────────────
    _q_col1, _q_col2 = st.columns([3, 1])
    with _q_col2:
        st.caption(t("Será adicionado ao lote ao clicar em ➕", "Will be added to batch on ➕"))

    st.markdown("---")

    # ── Current / Target ──────────────────────────────────────────────────────
    col_cur, col_tgt = st.columns(2, gap="large")

    with col_cur:
        st.subheader("📍 " + t("Estado Atual", "Current State"))
        cur_lv = st.number_input(
            t("Nível atual (0–40)", "Current level (0–40)"),
            0, MAX_GEAR_LEVEL, 0, key="hg_cur_lv",
        )
        st.progress(cur_lv / MAX_GEAR_LEVEL, text=f"LVL {cur_lv} / {MAX_GEAR_LEVEL}")

        st.markdown(f"**★ {t('Promoção atual', 'Current promotion')}**")
        if cur_lv < MAX_GEAR_LEVEL:
            st.caption(t("⚠️ Promoção disponível apenas no LVL 40.",
                         "⚠️ Promotion available only at LVL 40."))
            cur_promo = 0
        else:
            cur_promo = _promo_sel(t("Promoção atual", "Current promotion"), "hg_cur_promo")
            _show_promo_star(cur_promo)

    with col_tgt:
        st.subheader("🎯 " + t("Estado Alvo", "Target State"))
        tgt_lv = st.number_input(
            t("Nível alvo (0–40)", "Target level (0–40)"),
            0, MAX_GEAR_LEVEL, MAX_GEAR_LEVEL, key="hg_tgt_lv",
        )
        st.progress(tgt_lv / MAX_GEAR_LEVEL, text=f"LVL {tgt_lv} / {MAX_GEAR_LEVEL}")

        st.markdown(f"**★ {t('Promoção alvo', 'Target promotion')}**")
        if tgt_lv < MAX_GEAR_LEVEL:
            st.caption(t("⚠️ Promoção disponível apenas no LVL 40.",
                         "⚠️ Promotion available only at LVL 40."))
            tgt_promo = 0
        else:
            tgt_promo = _promo_sel(t("Promoção alvo", "Target promotion"), "hg_tgt_promo",
                                   default=MAX_PROMOTION)
            _show_promo_star(tgt_promo)

    needs_mark = st.checkbox(
        "🔖 " + t("Precisa de Marca Universal?", "Needs Universal Mark?"),
        key="hg_needs_mark",
    )
    _FAC_OPTS_PT = ["Liga", "Horda", "Natureza"]
    _FAC_OPTS_EN = ["League", "Horde", "Nature"]
    mark_faction = None
    if needs_mark:
        _fac_disp = _FAC_OPTS_PT if lang == "pt" else _FAC_OPTS_EN
        _fc1, _fc2, _fc3 = st.columns(3)
        for _fcol, _fk, _fn in zip([_fc1, _fc2, _fc3], _FAC_OPTS_PT, _fac_disp):
            with _fcol:
                _fic_path = os.path.join(_BASE, FACTION_ICON_DIR, FACTION_ICONS[_fk])
                _fsel = st.session_state.get("hg_mark_faction") == _fk
                _fi1, _fi2 = st.columns([1, 3])
                with _fi1:
                    st.image(_fic_path, width=28)
                with _fi2:
                    if st.button(_fn, key=f"hg_mfac_{_fk}",
                                 use_container_width=True,
                                 type="primary" if _fsel else "secondary"):
                        st.session_state["hg_mark_faction"] = _fk
                        st.rerun()
        if "hg_mark_faction" not in st.session_state:
            st.session_state["hg_mark_faction"] = _FAC_OPTS_PT[0]
        mark_faction = st.session_state["hg_mark_faction"]

    # ── Validation ────────────────────────────────────────────────────────────
    _errs = []
    if tgt_lv < cur_lv:
        _errs.append(t("⚠️ Nível alvo deve ser ≥ nível atual.",
                        "⚠️ Target level must be ≥ current level."))
    if tgt_promo < cur_promo:
        _errs.append(t("⚠️ Promoção alvo deve ser ≥ promoção atual.",
                        "⚠️ Target promotion must be ≥ current promotion."))
    for _e in _errs:
        st.error(_e)

    if not _errs:
        res = calc_gear_piece(cur_lv, tgt_lv, cur_promo, tgt_promo, needs_mark)
        _nothing = (res["enh_rune"] == 0 and res["ruby"] == 0 and res["gold_bars"] == 0
                    and res["leg_stones"] == 0 and res["myth_stones"] == 0 and res["marks"] == 0)

        if _nothing:
            st.info(t("Estado alvo igual ao atual. Nada a calcular.",
                      "Target matches current. Nothing to calculate."))
        else:
            st.markdown("---")
            results_header(f"📊 {t('Recursos Necessários', 'Resources Needed')}")

            _mc = st.columns(3)
            _ci = [0]

            def _metric(label: str, val: int, rkey: str = ""):
                if val <= 0:
                    return
                with _mc[_ci[0] % 3]:
                    if rkey:
                        _a, _b = st.columns([1, 5])
                        with _a:
                            show_resource_image(rkey, _BASE, st, height=28)
                        with _b:
                            st.metric(label, f"{val:,}")
                    else:
                        st.metric(label, f"{val:,}")
                _ci[0] += 1

            _metric(t("Runa de Aprimoramento", "Enhancement Rune"), res["enh_rune"], "enh_rune")
            _metric("Ruby", res["ruby"], "ruby")
            _metric(t("Barra de Ouro", "Gold Bar"), res["gold_bars"], "gold_bar")
            _metric(t("Pedra Lendária", "Legendary Stone"), res["leg_stones"], "leg_stone")
            _metric(t("Pedra Mítica", "Mythic Stone"), res["myth_stones"], "myth_stone")
            if needs_mark:
                _metric(t("Marca Universal", "Universal Mark"), 1)

            # Breakdown (leveling vs promotion)
            _has_lv = res["lv_enh_rune"] > 0
            _has_pr = res["pr_enh_rune"] > 0
            if _has_lv and _has_pr:
                with st.expander(t("🔍 Detalhamento (Nivelamento vs Promoção)",
                                   "🔍 Breakdown (Leveling vs Promotion)")):
                    _brows = []
                    if _has_lv:
                        _brows.append({
                            t("Categoria", "Category"):          t("Nivelamento", "Leveling"),
                            t("Runa Aprim.", "Enh. Rune"):       f"{res['lv_enh_rune']:,}",
                            "Ruby":                               f"{res['lv_ruby']:,}",
                            t("Barra de Ouro", "Gold Bar"):      "—",
                            t("Pedras", "Stones"):                "—",
                        })
                    if _has_pr:
                        _stones_str = ""
                        if res["leg_stones"] > 0:
                            _stones_str += f"{res['leg_stones']} {t('Lend.','Leg.')}"
                        if res["myth_stones"] > 0:
                            _stones_str += f"{' + ' if _stones_str else ''}{res['myth_stones']} {t('Míti.','Myth.')}"
                        _brows.append({
                            t("Categoria", "Category"):          t("Promoção", "Promotion"),
                            t("Runa Aprim.", "Enh. Rune"):       f"{res['pr_enh_rune']:,}",
                            "Ruby":                               f"{res['pr_ruby']:,}" if res['pr_ruby'] > 0 else "—",
                            t("Barra de Ouro", "Gold Bar"):      f"{res['gold_bars']:,}",
                            t("Pedras", "Stones"):                _stones_str or "—",
                        })
                    st.dataframe(pd.DataFrame(_brows), use_container_width=True, hide_index=True)

            st.markdown("---")
            _inv_compare(res, t("Inventário vs Necessário", "Inventory vs Needed"))

            st.markdown("---")
            if st.button(f"➕ {t('Adicionar ao Lote', 'Add to Batch')}", key="hg_add_batch",
                         type="primary"):
                _entry = {
                    "set":        sel_set,
                    "piece_pt":   sel_piece,
                    "piece_en":   GEAR_PIECES_EN[_pi],
                    "icon":       GEAR_PIECE_ICONS[_pi],
                    "from_lv":    cur_lv,
                    "to_lv":      tgt_lv,
                    "from_promo": cur_promo,
                    "to_promo":   tgt_promo,
                    "needs_mark":   needs_mark,
                    "mark_faction": mark_faction,
                    "res":          dict(res),
                }
                # Replace if same set+piece already in plan
                st.session_state["hg_plan"] = [
                    e for e in st.session_state["hg_plan"]
                    if not (e["set"] == sel_set and e["piece_pt"] == sel_piece)
                ]
                st.session_state["hg_plan"].append(_entry)
                _hg_save()
                st.success(t(
                    f"✅ {set_names[sel_set]} · {GEAR_PIECE_ICONS[_pi]} {piece_disp} adicionado ao lote!",
                    f"✅ {set_names[sel_set]} · {GEAR_PIECE_ICONS[_pi]} {piece_disp} added to batch!",
                ))

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — PLANEJADOR DE LOTE
# ══════════════════════════════════════════════════════════════════════════════
with tab_batch:
    plan = st.session_state["hg_plan"]

    if not plan:
        st.info(t(
            "Nenhuma peça no lote. Adicione pela aba Calculadora.",
            "No pieces in batch. Add them via the Calculator tab.",
        ))
    else:
        _rows = []
        grand: dict = {"enh_rune": 0, "ruby": 0, "gold_bars": 0,
                       "leg_stones": 0, "myth_stones": 0, "marks": 0}

        for e in plan:
            r = e["res"]
            _pname = e["piece_pt"] if lang == "pt" else e["piece_en"]
            _promo_from = promo_label(e["from_promo"], lang)
            _promo_to   = promo_label(e["to_promo"],   lang)
            _rows.append({
                t("Set", "Set"):           set_names[e["set"]],
                t("Peça", "Piece"):        f"{e['icon']} {_pname}",
                t("Marca?", "Mark?"):      (
                    f"✅ {e.get('mark_faction', '')}"
                    if e["needs_mark"] else "—"
                ),
                "LVL":                     f"{e['from_lv']}→{e['to_lv']}",
                "★ " + t("Promo", "Promo"): f"{_promo_from} → {_promo_to}",
                "🔷 " + t("Runa", "Rune"): f"{r['enh_rune']:,}",
                "🔴 Ruby":                 f"{r['ruby']:,}",
                "🟡 Gold":                 f"{r['gold_bars']:,}" if r["gold_bars"] > 0 else "—",
                "🟠 " + t("Lend.", "Leg."): f"{r['leg_stones']}" if r["leg_stones"] > 0 else "—",
                "🔴 " + t("Míti.", "Myth."): f"{r['myth_stones']}" if r["myth_stones"] > 0 else "—",
            })
            for _k in grand:
                grand[_k] += r.get(_k, 0)

        st.dataframe(pd.DataFrame(_rows), use_container_width=True, hide_index=True)

        # Remove entry
        _del_opts = [
            f"{set_names[e['set']]} · {e['icon']} {e['piece_pt'] if lang=='pt' else e['piece_en']}"
            for e in plan
        ]
        _del_sel = st.selectbox(t("Remover peça", "Remove piece"), ["—"] + _del_opts,
                                key="hg_del_sel")
        if _del_sel != "—":
            _del_idx = _del_opts.index(_del_sel)
            if st.button(f"🗑️ {t('Remover', 'Remove')} {_del_sel}", key="hg_del_btn"):
                st.session_state["hg_plan"].pop(_del_idx)
                _hg_save()
                st.rerun()

        st.divider()
        st.subheader("📊 " + t("Total do Lote", "Batch Total"))

        _tc = st.columns(3)
        _ti = [0]

        def _grand_metric(label: str, val: int, rkey: str = ""):
            if val <= 0:
                return
            with _tc[_ti[0] % 3]:
                if rkey:
                    _a, _b = st.columns([1, 5])
                    with _a:
                        show_resource_image(rkey, _BASE, st, height=28)
                    with _b:
                        st.metric(label, f"{val:,}")
                else:
                    st.metric(label, f"{val:,}")
            _ti[0] += 1

        _grand_metric(t("Runa de Aprimoramento", "Enhancement Rune"), grand["enh_rune"], "enh_rune")
        _grand_metric("Ruby", grand["ruby"], "ruby")
        _grand_metric(t("Barra de Ouro", "Gold Bar"), grand["gold_bars"], "gold_bar")
        _grand_metric(t("Pedra Lendária", "Legendary Stone"), grand["leg_stones"], "leg_stone")
        _grand_metric(t("Pedra Mítica", "Mythic Stone"), grand["myth_stones"], "myth_stone")
        _grand_metric(t("Marcas Universais", "Universal Marks"), grand["marks"])

        st.divider()
        _inv_compare(grand, t("Inventário vs Total do Lote", "Inventory vs Batch Total"))

        st.divider()
        if st.button("🗑️ " + t("Limpar lote", "Clear batch"), key="hg_clear"):
            st.session_state["hg_plan"] = []
            _hg_save()
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — REFERÊNCIA
# ══════════════════════════════════════════════════════════════════════════════
with tab_ref:
    _how1, _how2 = st.tabs([
        "📖 " + t("Como usar", "How to use"),
        "📊 " + t("Tabelas de referência", "Reference tables"),
    ])

    with _how1:
        st.markdown(t(
            """
### Hero Gear — Como usar

**Inventário** (barra lateral)
Informe seu estoque de cada recurso:
- **Runa de Aprimoramento**: usada tanto em nivelamento quanto em promoção
- **Ruby**: usada em nivelamento
- **Gold Bar**: usada em promoção (exceto passo 5/5 de cada tier)
- **Pedra Lendária**: usada no 5º passo dos tiers 1–4 de promoção
- **Pedra Mítica**: usada no 5º passo do tier 5 de promoção
- **Marca de Set**: necessária para criar a primeira peça de um conjunto

**Aba Calculadora**
1. Selecione o conjunto (Knight / Blood / Titan) e a peça (Arma / Bota / Capacete / Armadura)
2. Configure o **nível atual** (0–40) e o **nível alvo**
3. Configure a **promoção atual** (0–25 passos) e a **promoção alvo**
4. Marque "Precisa de Marca?" se for a primeira peça do conjunto
5. Clique em **"Calcular"** para ver os recursos necessários

**Aba Planejador de Lote**
1. Adicione múltiplas peças com seus objetivos de nível e promoção
2. O plano mostra o custo total e compara com seu inventário
3. Use **"Enviar para Eventos"** para registrar os pontos

**Sistema de Promoção**
Promoção = 5 tiers × 5 passos = 25 passos no total.
Passos 1–4 de cada tier: Runa + Gold Bar + Ruby.
Passo 5/5 de cada tier: Runa + Gold Bar + Pedra (sem Ruby).
""",
            """
### Hero Gear — How to use

**Inventory** (sidebar)
Enter your stock of each resource:
- **Enhancement Rune**: used for both leveling and promotion
- **Ruby**: used for leveling
- **Gold Bar**: used for promotion (except step 5/5 of each tier)
- **Legendary Stone**: used at step 5/5 of promotion tiers 1–4
- **Mythic Stone**: used at step 5/5 of promotion tier 5
- **Set Mark**: required to craft the first piece of a set

**Calculator tab**
1. Select the set (Knight / Blood / Titan) and piece (Weapon / Boot / Helmet / Armor)
2. Set **current level** (0–40) and **target level**
3. Set **current promotion** (0–25 steps) and **target promotion**
4. Check "Needs Mark?" if it's the first piece of a set
5. Click **"Calculate"** to see required resources

**Batch Planner tab**
1. Add multiple pieces with their level and promotion targets
2. The plan shows total cost and compares against your inventory
3. Use **"Send to Events"** to register the points

**Promotion system**
Promotion = 5 tiers × 5 steps = 25 total steps.
Steps 1–4 of each tier: Rune + Gold Bar + Ruby.
Step 5/5 of each tier: Rune + Gold Bar + Stone (no Ruby).
""",
        ))

    with _how2:
        _rt1, _rt2 = st.tabs([
            "📈 " + t("Nivelamento (LVL 0–40)", "Leveling (LVL 0–40)"),
            "★ " + t("Promoção (passos 1–25)", "Promotion (steps 1–25)"),
        ])

        with _rt1:
            st.caption(t(
                f"Total para LVL 0→40: {GEAR_LV_CUMUL_RUNE[40]:,} runas · {GEAR_LV_CUMUL_RUBY[40]:,} rubies",
                f"Total for LVL 0→40: {GEAR_LV_CUMUL_RUNE[40]:,} runes · {GEAR_LV_CUMUL_RUBY[40]:,} rubies",
            ))
            _ldf = [{
                "LVL": _lv,
                t("Runa/nível", "Rune/lvl"):   GEAR_LV_RUNE[_lv],
                t("Ruby/nível", "Ruby/lvl"):   GEAR_LV_RUBY[_lv],
                t("Runa Acum.", "Rune Cum."):  GEAR_LV_CUMUL_RUNE[_lv],
                t("Ruby Acum.", "Ruby Cum."):  GEAR_LV_CUMUL_RUBY[_lv],
            } for _lv in range(1, MAX_GEAR_LEVEL + 1)]
            st.dataframe(pd.DataFrame(_ldf).set_index("LVL"), use_container_width=True, height=450)

        with _rt2:
            st.caption(t(
                f"Total: {PROMO_CUMUL_RUNE[25]:,} runas · {PROMO_CUMUL_GOLD[25]:,} gold bars · "
                f"{PROMO_CUMUL_RUBY[25]:,} rubies · {PROMO_CUMUL_LEG[25]} ped. lend. · "
                f"{PROMO_CUMUL_MYTH[25]} ped. míti.",
                f"Total: {PROMO_CUMUL_RUNE[25]:,} runes · {PROMO_CUMUL_GOLD[25]:,} gold bars · "
                f"{PROMO_CUMUL_RUBY[25]:,} rubies · {PROMO_CUMUL_LEG[25]} leg. stones · "
                f"{PROMO_CUMUL_MYTH[25]} myth. stones",
            ))
            _prows = []
            for _s in range(1, MAX_PROMOTION + 1):
                _r, _g, _rb, _l, _m = PROMO_STEP_COSTS[_s - 1]
                _stones = ""
                if _l > 0:
                    _stones = f"{_l} {t('Lend.', 'Leg.')}"
                if _m > 0:
                    _stones = f"{_m} {t('Míti.', 'Myth.')}"
                _prows.append({
                    t("Passo", "Step"):                  _s,
                    "★":                                  promo_label(_s, lang),
                    t("Runa", "Rune"):                   _r,
                    t("Gold Bar", "Gold Bar"):            _g,
                    "Ruby":                               f"{_rb:,}" if _rb > 0 else "—",
                    t("Pedras", "Stones"):                _stones or "—",
                    t("Runa Acum.", "Rune Cum."):         PROMO_CUMUL_RUNE[_s],
                    t("Gold Bar Acum.", "Gold Bar Cum."): PROMO_CUMUL_GOLD[_s],
                    t("Ruby Acum.", "Ruby Cum."):         f"{PROMO_CUMUL_RUBY[_s]:,}" if PROMO_CUMUL_RUBY[_s] > 0 else "—",
                })
            st.dataframe(
                pd.DataFrame(_prows).set_index(t("Passo", "Step")),
                use_container_width=True, height=450,
            )
