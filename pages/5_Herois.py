"""
pages/5_Herois.py — Hero Calculator page.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd

from hero_engine import (
    HEROES, MYTHIC_HEROES, LEGENDARY_HEROES, ALL_HERO_NAMES,
    FACTION_HEROES, HEROIC_SPIRIT_HEROES,
    LEGENDARY_CUMUL, MYTHIC_CUMUL, LEGENDARY_LEG_COSTS, MYTHIC_LEG_COSTS, MAX_LEGS,
    SKILL_BOOK_COSTS, SKILL_BOOK_CUMUL, MAX_SKILL_LEVEL,
    AWAKENING_STEPS, AWK_STEP_LABELS, MAX_AWK_STEP,
    HS_COST_PER_LEVEL, HS_CUMUL, MAX_HS_LEVEL,
    UW_SHARDS_PER_LEVEL, UW_CUMUL, MAX_UW_LEVEL,
    TRAIT_TYPE_NAMES_PT, TRAIT_TYPE_NAMES_EN,
    TRAIT_DIAMOND_COSTS, TRAIT_FRAGS_PER_LEVEL, MAX_TRAIT_LEVEL,
    shards_for_legs, books_for_one_skill, total_books_per_skill,
    awk_cost, hs_shards, uw_shards, trait_cost, total_trait_cost,
    calc_hero,
)
from behemoth_engine import FACTION_ICONS, FACTION_ICON_DIR, show_star_image
from events_data import EVENTS, get_milestone_status

_BASE = os.path.dirname(os.path.dirname(__file__))

st.set_page_config(page_title="Heróis", page_icon="👤", layout="wide")

# ── Language ───────────────────────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "pt"

with st.sidebar:
    st.markdown("### 🌐 Idioma / Language")
    lang_pick = st.radio(
        "", ["🇧🇷 Português", "🇬🇧 English"],
        index=0 if st.session_state.lang == "pt" else 1,
        horizontal=True, label_visibility="collapsed", key="lang_hero",
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

# ── Visual constants ───────────────────────────────────────────────────────────
_FAC_COLOR  = {"Liga": "#4A90D9", "Horda": "#CC3333", "Natureza": "#33A04A"}
_TIER_COLOR = {"Mythic": "#CC3333", "Legendary": "#C8A400"}

def _inject_css():
    st.markdown("""
    <style>
    .hero-info-banner {
        border-radius: 0 8px 8px 0;
        padding: 8px 14px;
        margin: 6px 0 10px 0;
    }
    .tier-badge {
        display: inline-block;
        border-radius: 5px;
        padding: 2px 10px;
        font-weight: bold;
        font-size: 0.85em;
        color: white;
        margin-right: 8px;
    }
    .queue-header {
        border-radius: 0 6px 6px 0;
        padding: 5px 12px;
        margin-bottom: 4px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# ── Constants & helpers ────────────────────────────────────────────────────────
_FAC_PT = {"Liga": "Liga",     "Horda": "Horda",  "Natureza": "Natureza"}
_FAC_EN = {"Liga": "League",   "Horda": "Horde",  "Natureza": "Nature"}
_FACTIONS = ["Liga", "Horda", "Natureza"]

def _fn(f: str) -> str:
    return _FAC_PT[f] if lang == "pt" else _FAC_EN[f]

def _faction_icon(faction: str, width: int = 32):
    path = os.path.join(_BASE, FACTION_ICON_DIR, FACTION_ICONS[faction])
    st.image(path, width=width)

def _tier_emoji(tier: str) -> str:
    return "🔴" if tier == "Mythic" else "🟡"

def _tier_label(tier: str) -> str:
    return t("Mítico", "Mythic") if tier == "Mythic" else t("Lendário", "Legendary")

_COLOR_PT = ["Amarela", "Vermelha", "Platinada"]
_COLOR_EN = ["Yellow",  "Red",      "Platinum"]

def _leg_label(li: int) -> str:
    if li == 0:
        return t("0★ — Sem estrelas", "0★ — No stars")
    colors = _COLOR_PT if lang == "pt" else _COLOR_EN
    color  = colors[(li - 1) // 25]
    star   = (li - 1) % 25 // 5 + 1
    leg    = (li - 1) % 5 + 1
    return f"⭐{star} {color} · {leg}/5"

def _leg_sel(label: str, key: str, default: int = 0) -> int:
    idx = st.selectbox(label, range(MAX_LEGS + 1),
                       format_func=_leg_label, index=default, key=key)
    return idx

def _awk_sel(label: str, key: str, default: int = 0) -> int:
    return st.selectbox(label, range(MAX_AWK_STEP + 1),
                        format_func=lambda i: AWK_STEP_LABELS[i],
                        index=default, key=key)

def _show_leg_progress(leg_idx: int):
    """Progress bar showing leg completion."""
    pct = leg_idx / MAX_LEGS
    if leg_idx > 0:
        colors = _COLOR_PT if lang == "pt" else _COLOR_EN
        sn = (leg_idx - 1) // 5 + 1
        co = colors[(leg_idx - 1) // 25]
        ln = (leg_idx - 1) % 5 + 1
        txt = f"⭐{sn} {co} · {ln}/5  ({leg_idx}/{MAX_LEGS} {t('pernas','legs')})"
    else:
        txt = t(f"Sem estrelas (0/{MAX_LEGS})", f"No stars (0/{MAX_LEGS})")
    st.progress(pct, text=txt)

# ── Queue plan state ───────────────────────────────────────────────────────────
_Q_KEYS  = ["Q1", "Q2", "Q3", "Q4", "Q5"]
_Q_TYPES = {"Q1": t("Regular","Regular"), "Q2": t("Regular","Regular"),
            "Q3": t("Regular","Regular"), "Q4": t("Regular","Regular"),
            "Q5": t("Privilégio","Privilege")}

if "hero_plan_v2" not in st.session_state:
    st.session_state["hero_plan_v2"] = {
        k: {"faction": "Liga", "heroes": []} for k in _Q_KEYS
    }

# ── Header ─────────────────────────────────────────────────────────────────────
_inject_css()
st.title("👤 " + t("Calculadora de Heróis", "Hero Calculator"))
st.caption(t(
    "Calcula fragmentos, livros de habilidade, soul stones, UW, espírito heroico e atributos.",
    "Calculates shards, skill books, soul stones, UW, heroic spirit and traits.",
))

tab_calc, tab_plan, tab_ref = st.tabs([
    "🧮 " + t("Calculadora", "Calculator"),
    "📋 " + t("Planejador de Filas", "Queue Planner"),
    "📖 " + t("Referência", "Reference"),
])

# ══════════════════════════════════════════════════════════════════════════════
# ABA 1 — CALCULADORA INDIVIDUAL
# ══════════════════════════════════════════════════════════════════════════════
with tab_calc:

    # ── 1. Faction → Hero selection ───────────────────────────────────────────
    st.subheader("👤 " + t("Selecione o Herói", "Select Hero"))

    fac_opts = [_fn(f) for f in _FACTIONS]
    fac_disp = st.radio(t("Facção", "Faction"), fac_opts,
                        horizontal=True, key="calc_fac_filter")
    sel_fac  = _FACTIONS[fac_opts.index(fac_disp)]

    tier_opts = [t("Todos","All"), t("Mítico","Mythic"), t("Lendário","Legendary")]
    tier_filt = st.radio(t("Tier", "Tier"), tier_opts, horizontal=True, key="calc_tier_filter")

    _pool = FACTION_HEROES[sel_fac]
    if tier_filt == t("Mítico","Mythic"):
        _pool = [h for h in _pool if HEROES[h]["tier"] == "Mythic"]
    elif tier_filt == t("Lendário","Legendary"):
        _pool = [h for h in _pool if HEROES[h]["tier"] == "Legendary"]

    # Ensure selected hero is in current pool
    if st.session_state.get("calc_hero_sel") not in _pool:
        st.session_state["calc_hero_sel"] = _pool[0]

    # Hero grid
    _fac_color = _FAC_COLOR[sel_fac]
    _hi1, _hi2 = st.columns([1, 11])
    with _hi1:
        _faction_icon(sel_fac, width=36)
    with _hi2:
        _ncols = 4
        for _row_start in range(0, len(_pool), _ncols):
            _row_heroes = _pool[_row_start:_row_start + _ncols]
            _row_cols   = st.columns(len(_row_heroes))
            for _h, _hc in zip(_row_heroes, _row_cols):
                with _hc:
                    _selected = st.session_state.get("calc_hero_sel") == _h
                    if st.button(
                        f"{_tier_emoji(HEROES[_h]['tier'])} {_h}",
                        key=f"hero_btn_{_h}",
                        use_container_width=True,
                        type="primary" if _selected else "secondary",
                    ):
                        st.session_state["calc_hero_sel"] = _h
                        st.rerun()

    sel_hero = st.session_state["calc_hero_sel"]
    hdata    = HEROES[sel_hero]
    tier     = hdata["tier"]
    faction  = hdata["faction"]
    n_sk     = hdata["skills"]
    t_names  = TRAIT_TYPE_NAMES_PT if lang == "pt" else TRAIT_TYPE_NAMES_EN

    # Hero info banner with faction color
    _flags = []
    if hdata["has_hs"]:      _flags.append(t("✨ Espírito Heroico","✨ Heroic Spirit"))
    if hdata["has_uw"]:      _flags.append(t("⚔️ UW","⚔️ UW"))
    if tier == "Legendary":  _flags.append(t("💎 Despertar","💎 Awakening"))
    _flags.append(f"{n_sk} skills")
    _fc = _FAC_COLOR[faction]
    _tc = _TIER_COLOR[tier]
    st.markdown(
        f'<div class="hero-info-banner" style="border-left:5px solid {_fc}; background:{_fc}11;">'
        f'<span class="tier-badge" style="background:{_tc};">'
        f'{_tier_emoji(tier)} {_tier_label(tier)}</span>'
        f'<span style="color:#555; font-size:0.88em;">'
        f'{" · ".join(_flags)} · <b>{t("Atributo 3","Trait 3")}:</b> {hdata["trait3"]}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── 2. Current / Target ───────────────────────────────────────────────────
    col_cur, col_tgt = st.columns(2, gap="large")

    with col_cur:
        st.subheader("📍 " + t("Estado Atual", "Current State"))

        # Stars
        st.markdown(f"**⭐ {t('Estrelas','Stars')}**")
        cur_leg = _leg_sel(t("Perna atual","Current leg"), "calc_cur_leg", 0)
        show_star_image(cur_leg, _BASE, st)
        _show_leg_progress(cur_leg)

        # Skills
        st.markdown(f"**📚 {t('Skills (por habilidade)','Skills (per ability)')}**")
        cur_skills = []
        for si in range(n_sk):
            cur_skills.append(st.number_input(
                f"Skill {si+1} — {t('Atual','Current')}",
                min_value=1, max_value=15, value=1, key=f"calc_cur_sk_{si}",
            ))

        # Awakening
        if tier == "Legendary":
            with st.expander(f"💎 {t('Despertar','Awakening')}", expanded=True):
                cur_awk = _awk_sel(t("Estágio atual","Current stage"), "calc_cur_awk", 0)
        else:
            cur_awk = 0

        # Heroic Spirit
        if hdata["has_hs"]:
            with st.expander(f"✨ {t('Espírito Heroico','Heroic Spirit')}", expanded=True):
                cur_hs = st.number_input(t("Nível atual (0-100)","Current level (0-100)"),
                                         0, MAX_HS_LEVEL, 0, key="calc_cur_hs")
        else:
            cur_hs = 0

        # UW
        if hdata["has_uw"]:
            with st.expander(f"⚔️ {t('Equip. Exclusivo (UW)','Exclusive Weapon (UW)')}", expanded=True):
                cur_uw = st.number_input(t("Nível atual UW (0-20)","Current UW level (0-20)"),
                                         0, MAX_UW_LEVEL, 0, key="calc_cur_uw")
        else:
            cur_uw = 0

        # Traits
        with st.expander(f"🧬 {t('Atributos','Traits')}", expanded=False):
            cur_traits = [
                st.number_input(f"{t_names[ti]} — {t('Atual','Current')}",
                                0, MAX_TRAIT_LEVEL, 0, key=f"calc_cur_tr_{ti}")
                for ti in range(4)
            ]

    with col_tgt:
        st.subheader("🎯 " + t("Estado Alvo", "Target State"))

        # Stars
        st.markdown(f"**⭐ {t('Estrelas','Stars')}**")
        tgt_leg = _leg_sel(t("Perna alvo","Target leg"), "calc_tgt_leg", MAX_LEGS)
        show_star_image(tgt_leg, _BASE, st)
        _show_leg_progress(tgt_leg)

        # Skills
        st.markdown(f"**📚 {t('Skills (por habilidade)','Skills (per ability)')}**")
        tgt_skills = []
        for si in range(n_sk):
            tgt_skills.append(st.number_input(
                f"Skill {si+1} — {t('Alvo','Target')}",
                min_value=1, max_value=15, value=15, key=f"calc_tgt_sk_{si}",
            ))

        # Awakening
        if tier == "Legendary":
            with st.expander(f"💎 {t('Despertar','Awakening')}", expanded=True):
                tgt_awk = _awk_sel(t("Estágio alvo","Target stage"), "calc_tgt_awk", MAX_AWK_STEP)
        else:
            tgt_awk = 0

        # Heroic Spirit
        if hdata["has_hs"]:
            with st.expander(f"✨ {t('Espírito Heroico','Heroic Spirit')}", expanded=True):
                tgt_hs = st.number_input(t("Nível alvo (0-100)","Target level (0-100)"),
                                         0, MAX_HS_LEVEL, MAX_HS_LEVEL, key="calc_tgt_hs")
        else:
            tgt_hs = 0

        # UW
        if hdata["has_uw"]:
            with st.expander(f"⚔️ {t('Equip. Exclusivo (UW)','Exclusive Weapon (UW)')}", expanded=True):
                tgt_uw = st.number_input(t("Nível alvo UW (0-20)","Target UW level (0-20)"),
                                         0, MAX_UW_LEVEL, MAX_UW_LEVEL, key="calc_tgt_uw")
        else:
            tgt_uw = 0

        # Traits
        with st.expander(f"🧬 {t('Atributos','Traits')}", expanded=False):
            tgt_traits = [
                st.number_input(f"{t_names[ti]} — {t('Alvo','Target')}",
                                0, MAX_TRAIT_LEVEL, MAX_TRAIT_LEVEL, key=f"calc_tgt_tr_{ti}")
                for ti in range(4)
            ]

    # ── Validation ────────────────────────────────────────────────────────────
    errors = []
    if tgt_leg < cur_leg:
        errors.append(t("⚠️ Perna alvo deve ser ≥ perna atual.", "⚠️ Target leg must be ≥ current leg."))
    for si in range(n_sk):
        if tgt_skills[si] < cur_skills[si]:
            errors.append(t(f"⚠️ Skill {si+1}: alvo deve ser ≥ atual.",
                            f"⚠️ Skill {si+1}: target must be ≥ current."))
    if tier == "Legendary" and tgt_awk < cur_awk:
        errors.append(t("⚠️ Despertar: alvo deve ser ≥ atual.", "⚠️ Awakening: target must be ≥ current."))
    for ti in range(4):
        if tgt_traits[ti] < cur_traits[ti]:
            errors.append(t(f"⚠️ Atributo {t_names[ti]}: alvo deve ser ≥ atual.",
                            f"⚠️ Trait {t_names[ti]}: target must be ≥ current."))
    for e in errors:
        st.error(e)

    if not errors:
        res = calc_hero(
            sel_hero,
            from_leg=cur_leg,    to_leg=tgt_leg,
            from_skills=cur_skills, to_skills=tgt_skills,
            from_awk=cur_awk,    to_awk=tgt_awk,
            from_hs=cur_hs,      to_hs=tgt_hs,
            from_uw=cur_uw,      to_uw=tgt_uw,
            from_traits=cur_traits, to_traits=tgt_traits,
        )

        nothing = all(v == 0 for k, v in res.items()
                      if k not in ("hero", "tier", "faction"))
        if nothing:
            st.info(t("Estado alvo igual ao atual. Nada a calcular.",
                      "Target matches current state. Nothing to calculate."))
        else:
            st.markdown("---")
            # Faction-colored results header
            st.markdown(
                f'<div style="border-left:5px solid {_fc}; padding:4px 12px; '
                f'border-radius:0 6px 6px 0; background:{_fc}11; margin-bottom:8px;">'
                f'<b>📊 {t("Recursos Necessários","Resources Needed")}</b></div>',
                unsafe_allow_html=True,
            )

            _mc = st.columns(4)
            _ci = [0]
            def _m(label: str, value: int, icon: str = ""):
                if value > 0:
                    with _mc[_ci[0] % 4]:
                        st.metric(f"{icon} {label}", f"{value:,}")
                _ci[0] += 1

            _shard_lbl = (t("Frags. Míticos","Mythic Shards")
                          if tier == "Mythic" else t("Frags. Lendários","Legendary Shards"))
            _m(_shard_lbl,                                     res["star_shards"],    "⭐")
            _m(t("Livros de Habilidade","Skill Books"),         res["skill_books"],    "📚")
            if tier == "Legendary":
                _m(t("Frags. (Despertar)","Shards (Awakening)"), res["awk_shards"],   "💎")
                _m(f"Soul Stones ({_fn(faction)})",               res["awk_ss"],       "💠")
            if hdata["has_hs"]:
                _m(t("Frags. Esp. Heroico","Heroic Spirit Shards"), res["hs_shards"], "✨")
            if hdata["has_uw"]:
                _m(t("Frags. UW","UW Shards"),                   res["uw_shards"],    "⚔️")
            if res["trait_diamonds"] > 0:
                _m(t("Diamantes (Atributos)","Diamonds (Traits)"), res["trait_diamonds"], "💎")
            if res["trait_shards"] > 0:
                _m(t("Frags. de Atributo","Trait Shards"),         res["trait_shards"],   "🧬")

            # Skill breakdown
            if any(tgt_skills[i] > cur_skills[i] for i in range(n_sk)):
                with st.expander(t("📚 Detalhamento de Skills","📚 Skill Breakdown")):
                    sk_rows = []
                    for si in range(n_sk):
                        bk = books_for_one_skill(cur_skills[si], tgt_skills[si])
                        if bk > 0:
                            sk_rows.append({
                                t("Skill","Skill"):          f"Skill {si+1}",
                                t("De → Para","From → To"):  f"Lv{cur_skills[si]} → Lv{tgt_skills[si]}",
                                t("📚 Livros","📚 Books"):    bk,
                            })
                    st.dataframe(pd.DataFrame(sk_rows), use_container_width=True, hide_index=True)

            # Trait breakdown
            if any(tgt_traits[i] > cur_traits[i] for i in range(4)):
                with st.expander(t("🧬 Detalhamento de Atributos","🧬 Trait Breakdown")):
                    tr_rows = []
                    for ti in range(4):
                        if tgt_traits[ti] > cur_traits[ti]:
                            dia, frags = trait_cost(ti, cur_traits[ti], tgt_traits[ti])
                            tr_rows.append({
                                t("Tipo","Type"):               t_names[ti],
                                t("De → Para","From → To"):     f"{cur_traits[ti]} → {tgt_traits[ti]}",
                                t("💎 Diamantes","💎 Diamonds"): dia if dia else "—",
                                t("🧬 Fragmentos","🧬 Shards"):  frags if frags else "—",
                            })
                    st.dataframe(pd.DataFrame(tr_rows), use_container_width=True, hide_index=True)

            # ── Event Impact ──────────────────────────────────────────────────
            st.markdown("---")
            st.markdown("**📅 " + t("Impacto nos Eventos Regulares","Regular Event Impact") + "**")

            ev_hd     = next(e for e in EVENTS if e["sheet"] == "Hero_Development")
            ev_hdname = ev_hd.get("name_pt", ev_hd["name"]) if lang == "pt" else ev_hd["name"]

            pts_shards = (res["star_shards"] + res["awk_shards"]) * 100
            pts_books  = res["skill_books"] * 0.1
            pts_ss     = res["awk_ss"] * 1500
            pts_uw     = res["uw_shards"] * 100
            pts_hd     = pts_shards + pts_books + pts_ss + pts_uw

            _ec = st.columns(4)
            _ec[0].metric(f"⭐ {_shard_lbl}", f"{pts_shards:,.0f} pts")
            _ec[1].metric(f"📚 {t('Livros','Books')}", f"{pts_books:,.0f} pts")
            if pts_ss > 0:
                _ec[2].metric("💠 Soul Stones", f"{pts_ss:,.0f} pts")
            if pts_uw > 0:
                _ec[3].metric("⚔️ UW", f"{pts_uw:,.0f} pts")
            st.metric(f"📊 {ev_hdname}", f"{pts_hd:,.0f} pts")

            _ms_hd = "  ".join(
                f"✅ {s['value']:,}" if s["reached"] else f"⬜ {s['value']:,}"
                for s in get_milestone_status(ev_hd["milestones"], pts_hd)
            )
            st.caption(f"Milestones: {_ms_hd}")

            if st.button("📅 " + t("Enviar para Eventos","Send to Events"), key="send_hero_calc_evt"):
                st.session_state["_src_hero_Hero_Development"] = int(pts_hd)
                task_shard = 10 if tier == "Mythic" else 0
                st.session_state[f"_calc_contrib_Hero_Development_{task_shard}"] = int(pts_shards)
                st.session_state["_calc_contrib_Hero_Development_4"]  = int(pts_ss)
                st.session_state["_calc_contrib_Hero_Development_5"]  = int(pts_books)
                st.session_state["_calc_contrib_Hero_Development_2"]  = int(pts_uw)
                st.session_state["_calc_sent_Hero_Development"] = True
                st.success(t(f"✅ {pts_hd:,.0f} pts enviados para **{ev_hdname}**!",
                             f"✅ {pts_hd:,.0f} pts sent to **{ev_hdname}**!"))

            # ── Adicionar à fila ───────────────────────────────────────────────
            st.markdown("---")
            st.markdown("**📋 " + t("Adicionar ao Planejador de Filas","Add to Queue Planner") + "**")

            _qa1, _qa2 = st.columns([2, 1])
            with _qa1:
                _q_dest = st.selectbox(t("Destino","Destination"),
                                       _Q_KEYS, key="calc_q_dest")
            with _qa2:
                _q_type_info = _Q_TYPES.get(_q_dest, "Regular")
                st.caption(f"{_q_type_info} — {_fn(faction)}")

            if st.button("➕ " + t("Adicionar à fila","Add to queue"), key="calc_add_to_q"):
                plan = st.session_state["hero_plan_v2"]
                plan[_q_dest]["faction"] = faction
                plan[_q_dest]["heroes"] = [
                    e for e in plan[_q_dest]["heroes"] if e["name"] != sel_hero
                ]
                plan[_q_dest]["heroes"].append({
                    "name":       sel_hero,
                    "tier":       tier,
                    "faction":    faction,
                    "cur_leg":    cur_leg,
                    "tgt_leg":    tgt_leg,
                    "cur_skills": list(cur_skills),
                    "tgt_skills": list(tgt_skills),
                    "cur_awk":    cur_awk,
                    "tgt_awk":    tgt_awk,
                    "cur_hs":     cur_hs,
                    "tgt_hs":     tgt_hs,
                    "cur_uw":     cur_uw,
                    "tgt_uw":     tgt_uw,
                    "cur_traits": list(cur_traits),
                    "tgt_traits": list(tgt_traits),
                    "res":        dict(res),
                })
                st.success(t(f"✅ {sel_hero} adicionado a {_q_dest}!",
                             f"✅ {sel_hero} added to {_q_dest}!"))

# ══════════════════════════════════════════════════════════════════════════════
# ABA 2 — PLANEJADOR DE FILAS
# ══════════════════════════════════════════════════════════════════════════════
with tab_plan:
    st.caption(t(
        "Q1-Q4 são filas regulares, Q5 é privilégio. "
        "Adicione heróis pela aba Calculadora.",
        "Q1-Q4 are regular queues, Q5 is privilege. "
        "Add heroes via the Calculator tab.",
    ))

    plan = st.session_state["hero_plan_v2"]

    grand: dict = {
        "star_my": 0, "star_le": 0, "skill_books": 0,
        "awk_sh": 0, "ss_liga": 0, "ss_horda": 0, "ss_nat": 0,
        "hs_sh": 0, "uw_sh": 0, "trait_dia": 0, "trait_sh": 0,
    }

    for qk in _Q_KEYS:
        q = plan[qk]

        # Resolve current faction without one-frame lag
        _q_fac_opts = [_fn(f) for f in _FACTIONS]
        _widget_sel = st.session_state.get(f"q_fac_{qk}")
        if _widget_sel is not None and _widget_sel in _q_fac_opts:
            qfac = _FACTIONS[_q_fac_opts.index(_widget_sel)]
            plan[qk]["faction"] = qfac
        else:
            qfac = q["faction"]

        hlist = q["heroes"]

        # Faction-colored queue header
        _qfc = _FAC_COLOR[qfac]
        _qh1, _qh2 = st.columns([1, 9])
        with _qh1:
            _faction_icon(qfac, width=28)
        with _qh2:
            st.markdown(
                f'<div class="queue-header" style="border-left:4px solid {_qfc}; '
                f'background:{_qfc}11;">'
                f'{qk} — {_Q_TYPES[qk]}</div>',
                unsafe_allow_html=True,
            )
            _q_fac_sel = st.selectbox(
                t("Facção","Faction"),
                _q_fac_opts,
                index=_FACTIONS.index(qfac),
                key=f"q_fac_{qk}",
                label_visibility="collapsed",
            )
            plan[qk]["faction"] = _FACTIONS[_q_fac_opts.index(_q_fac_sel)]

        if not hlist:
            st.caption(t(f"  {qk}: vazia — adicione heróis pela aba Calculadora.",
                         f"  {qk}: empty — add heroes via Calculator tab."))
        else:
            _q_rows = []
            for entry in hlist:
                r = entry["res"]
                _q_rows.append({
                    t("Herói","Hero"):        f"{_tier_emoji(entry['tier'])} {entry['name']}",
                    t("Perna","Leg"):         f"{entry['cur_leg']}→{entry['tgt_leg']}",
                    t("⭐ Frags","⭐ Shards"): r["star_shards"],
                    t("📚 Livros","📚 Books"): r["skill_books"],
                    "💎 Awk":                 r["awk_shards"],
                    "💠 SS":                  r["awk_ss"],
                    "✨ HS":                  r["hs_shards"],
                    "⚔️ UW":                  r["uw_shards"],
                })
                tier_h = entry["tier"]
                fac_h  = entry["faction"]
                if tier_h == "Mythic":
                    grand["star_my"] += r["star_shards"]
                else:
                    grand["star_le"] += r["star_shards"] + r["awk_shards"]
                grand["skill_books"] += r["skill_books"]
                grand["hs_sh"]       += r["hs_shards"]
                grand["uw_sh"]       += r["uw_shards"]
                grand["trait_dia"]   += r["trait_diamonds"]
                grand["trait_sh"]    += r["trait_shards"]
                if fac_h == "Liga":    grand["ss_liga"]  += r["awk_ss"]
                elif fac_h == "Horda": grand["ss_horda"] += r["awk_ss"]
                else:                  grand["ss_nat"]   += r["awk_ss"]

            df_q = pd.DataFrame(_q_rows)
            st.dataframe(df_q, use_container_width=True, hide_index=True)

            _del_h = st.selectbox(t("Remover herói","Remove hero"),
                                  ["—"] + [e["name"] for e in hlist],
                                  key=f"q_del_{qk}")
            if _del_h != "—":
                if st.button(f"🗑️ {t('Remover','Remove')} {_del_h}", key=f"q_del_btn_{qk}"):
                    plan[qk]["heroes"] = [e for e in hlist if e["name"] != _del_h]
                    st.rerun()

        st.divider()

    # Grand total
    st.subheader("📊 " + t("Total Geral", "Grand Total"))
    _gt = st.columns(4)
    if grand["star_my"] > 0:
        _gt[0].metric(t("⭐ Frags. Míticos","⭐ Mythic Shards"), f"{grand['star_my']:,}")
    if grand["star_le"] > 0:
        _gt[1].metric(t("⭐ Frags. Lendários","⭐ Legendary Shards"), f"{grand['star_le']:,}")
    if grand["skill_books"] > 0:
        _gt[2].metric(t("📚 Livros","📚 Books"), f"{grand['skill_books']:,}")
    if grand["hs_sh"] > 0:
        _gt[3].metric(t("✨ Esp. Heroico","✨ Heroic Spirit"), f"{grand['hs_sh']:,}")

    _gt2 = st.columns(4)
    for _fac, _key, _ci in [("Liga","ss_liga",0),("Horda","ss_horda",1),("Natureza","ss_nat",2)]:
        if grand[_key] > 0:
            _gt2[_ci].metric(f"💠 SS {_fn(_fac)}", f"{grand[_key]:,}")
    if grand["uw_sh"] > 0:
        _gt2[3].metric(t("⚔️ UW Shards","⚔️ UW Shards"), f"{grand['uw_sh']:,}")

    st.divider()
    if st.button("🗑️ " + t("Limpar todo o plano","Clear entire plan"), key="q_clear_all"):
        st.session_state["hero_plan_v2"] = {k: {"faction": "Liga", "heroes": []}
                                             for k in _Q_KEYS}
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# ABA 3 — REFERÊNCIA
# ══════════════════════════════════════════════════════════════════════════════
with tab_ref:
    _r1, _r2 = st.tabs([
        "⭐ " + t("Estrelas", "Stars"),
        "📚 " + t("Skills / UW / HS", "Skills / UW / HS"),
    ])

    with _r1:
        _rc1, _rc2 = st.columns(2)
        with _rc1:
            st.subheader(t("⭐ Lendário — custo por perna","⭐ Legendary — cost per leg"))
            st.caption(t("Total: 500 fragmentos","Total: 500 shards"))
            _leg_col = t("Perna","Leg")
            _ld = [{_leg_col: i, t("Custo","Cost"): LEGENDARY_LEG_COSTS[i-1],
                    t("Acum.","Cum."): LEGENDARY_CUMUL[i]}
                   for i in range(1, MAX_LEGS + 1)]
            st.dataframe(pd.DataFrame(_ld).set_index(_leg_col),
                         use_container_width=True, height=400)
        with _rc2:
            st.subheader(t("⭐ Mítico — custo por perna","⭐ Mythic — cost per leg"))
            st.caption(t("Total: 1000 fragmentos","Total: 1000 shards"))
            _leg_col2 = t("Perna","Leg")
            _md = [{_leg_col2: i, t("Custo","Cost"): MYTHIC_LEG_COSTS[i-1],
                    t("Acum.","Cum."): MYTHIC_CUMUL[i]}
                   for i in range(1, MAX_LEGS + 1)]
            st.dataframe(pd.DataFrame(_md).set_index(_leg_col2),
                         use_container_width=True, height=400)

    with _r2:
        _sr1, _sr2, _sr3 = st.columns(3)
        with _sr1:
            st.subheader(t("📚 Livros de Skill","📚 Skill Books"))
            _skd = [{"LVL": i+1, t("Custo","Cost"): SKILL_BOOK_COSTS[i],
                     t("Acum.","Cum."): SKILL_BOOK_CUMUL[i]}
                    for i in range(len(SKILL_BOOK_COSTS))]
            st.dataframe(pd.DataFrame(_skd).set_index("LVL"),
                         use_container_width=True, height=400)
        with _sr2:
            st.subheader(t("⚔️ UW — custo por nível","⚔️ UW — cost per level"))
            st.caption(t(f"Total: {UW_CUMUL[20]:,} fragmentos",
                         f"Total: {UW_CUMUL[20]:,} shards"))
            _uwd = [{"LVL": i+1, t("Custo","Cost"): UW_SHARDS_PER_LEVEL[i],
                     t("Acum.","Cum."): UW_CUMUL[i+1]}
                    for i in range(MAX_UW_LEVEL)]
            st.dataframe(pd.DataFrame(_uwd).set_index("LVL"),
                         use_container_width=True, height=400)
        with _sr3:
            st.subheader(t("✨ Espírito Heroico (simples)","✨ Heroic Spirit (simple)"))
            st.caption(t(f"Total: {HS_CUMUL[100]:,} fragmentos",
                         f"Total: {HS_CUMUL[100]:,} shards"))
            _hsd = [{"LVL": lv, t("Custo","Cost"): HS_COST_PER_LEVEL[lv],
                     t("Acum.","Cum."): HS_CUMUL[lv]}
                    for lv in range(1, MAX_HS_LEVEL + 1)]
            st.dataframe(pd.DataFrame(_hsd).set_index("LVL"),
                         use_container_width=True, height=400)
