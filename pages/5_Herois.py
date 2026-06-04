"""
pages/5_Herois.py — Hero Calculator page.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from PIL import Image

from hero_engine import (
    HEROES, MYTHIC_HEROES, LEGENDARY_HEROES, ALL_HERO_NAMES,
    FACTION_HEROES, HEROIC_SPIRIT_HEROES,
    LEGENDARY_CUMUL, MYTHIC_CUMUL, MAX_LEGS,
    SKILL_BOOK_COSTS, SKILL_BOOK_CUMUL, MAX_SKILL_LEVEL,
    AWAKENING_STEPS, MAX_AWK_STEP,
    HS_COST_PER_LEVEL, HS_CUMUL, MAX_HS_LEVEL,
    UW_SHARDS_PER_LEVEL, UW_CUMUL, MAX_UW_LEVEL,
    TRAIT_TYPE_NAMES_PT, TRAIT_TYPE_NAMES_EN,
    TRAIT_DIAMOND_COSTS, TRAIT_FRAGS_PER_LEVEL,
    TRAIT_UNLOCK_PREREQ, MAX_TRAIT_LEVEL,
    leg_to_display, shards_for_legs, books_for_skills, total_books,
    awk_cost, hs_shards, uw_shards, trait_cost, total_trait_cost,
    calc_hero,
)
from behemoth_engine import FACTION_ICONS, FACTION_ICON_DIR
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

# ── Helpers ────────────────────────────────────────────────────────────────────
_FACTION_PT = {"Liga": "Liga", "Horda": "Horda", "Natureza": "Natureza"}
_FACTION_EN = {"Liga": "League", "Horda": "Horde", "Natureza": "Nature"}

def _faction_name(f: str) -> str:
    return _FACTION_PT[f] if lang == "pt" else _FACTION_EN[f]

def _faction_icon(faction: str, width: int = 32):
    path = os.path.join(_BASE, FACTION_ICON_DIR, FACTION_ICONS[faction])
    st.image(path, width=width)

def _tier_label(tier: str) -> str:
    return t("Mítico", "Mythic") if tier == "Mythic" else t("Lendário", "Legendary")

def _tier_emoji(tier: str) -> str:
    return "🔴" if tier == "Mythic" else "🟡"

# Build leg option labels once
_LEG_LABELS: list[str] = [t("0★ — Sem estrelas", "0★ — No stars")]
_COLOR_PT = ["Amarela ⭐", "Vermelha ⭐", "Platinada ⭐"]
_COLOR_EN = ["Yellow ⭐",  "Red ⭐",     "Platinum ⭐"]
for _li in range(1, MAX_LEGS + 1):
    _s_in_color = ((_li - 1) % 25) // 5 + 1
    _leg        = (_li - 1) % 5 + 1
    _color_i    = (_li - 1) // 25
    _colors     = _COLOR_PT if lang == "pt" else _COLOR_EN
    _color      = _colors[_color_i] if _color_i < 3 else f"C{_color_i+1}"
    _LEG_LABELS.append(f"{_color}{_s_in_color} · {_leg}/5")

_AWK_LABELS: list[str] = [t("Não desperto", "Not awakened")] + [
    f"T{_t} L{_l}" for _t, _l, _, _ in AWAKENING_STEPS
]

def _leg_selectbox(label: str, key: str, default: int = 0) -> int:
    sel = st.selectbox(label, _LEG_LABELS, index=default, key=key)
    return _LEG_LABELS.index(sel)

def _awk_selectbox(label: str, key: str, default: int = 0) -> int:
    sel = st.selectbox(label, _AWK_LABELS, index=default, key=key)
    return _AWK_LABELS.index(sel)

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("👤 " + t("Calculadora de Heróis", "Hero Calculator"))
st.caption(t(
    "Calcula fragmentos, livros, soul stones, equipamento exclusivo, espírito heroico e traits.",
    "Calculates shards, books, soul stones, exclusive weapon, heroic spirit and traits.",
))

# ── ABAS ───────────────────────────────────────────────────────────────────────
tab_calc, tab_plan, tab_ref = st.tabs([
    "🧮 " + t("Calculadora", "Calculator"),
    "📋 " + t("Planejador de Filas", "Queue Planner"),
    "📖 " + t("Referência", "Reference"),
])

# ══════════════════════════════════════════════════════════════════════════════
# ABA 1 — CALCULADORA INDIVIDUAL
# ══════════════════════════════════════════════════════════════════════════════
with tab_calc:

    # ── Hero selection ─────────────────────────────────────────────────────────
    st.subheader("👤 " + t("Selecione o Herói", "Select Hero"))

    tier_filter = st.radio(
        t("Filtrar por tier:", "Filter by tier:"),
        [t("Todos", "All"), t("Mítico", "Mythic"), t("Lendário", "Legendary")],
        horizontal=True, key="calc_tier_filter",
    )
    if tier_filter == t("Mítico", "Mythic"):
        _hero_list = MYTHIC_HEROES
    elif tier_filter == t("Lendário", "Legendary"):
        _hero_list = LEGENDARY_HEROES
    else:
        _hero_list = ALL_HERO_NAMES

    sel_hero = st.selectbox(t("Herói", "Hero"), _hero_list, key="calc_hero_sel")
    hdata    = HEROES[sel_hero]
    tier     = hdata["tier"]
    faction  = hdata["faction"]

    hi1, hi2, hi3 = st.columns([1, 2, 3])
    with hi1:
        _faction_icon(faction, width=36)
    with hi2:
        st.markdown(f"**{_tier_emoji(tier)} {_tier_label(tier)}**")
        st.caption(f"**{t('Facção','Faction')}:** {_faction_name(faction)}")
    with hi3:
        flags = []
        if hdata["has_hs"]:
            flags.append(t("✨ Espírito Heroico", "✨ Heroic Spirit"))
        if hdata["has_uw"]:
            flags.append(t("⚔️ UW", "⚔️ UW"))
        if tier == "Legendary":
            flags.append(t("💎 Despertar", "💎 Awakening"))
        st.caption(" · ".join(flags) if flags else "—")
        st.caption(f"**{t('Skills','Skills')}:** {hdata['skills']}  |  "
                   f"**Trait 3:** {hdata['trait3']}")

    st.markdown("---")

    # ── Estado atual / alvo ────────────────────────────────────────────────────
    col_cur, col_tgt = st.columns(2, gap="large")

    with col_cur:
        st.subheader("📍 " + t("Estado Atual", "Current State"))

        st.markdown(f"**⭐ {t('Estrelas', 'Stars')}**")
        cur_leg = _leg_selectbox(t("Leg atual", "Current leg"), "calc_cur_leg", 0)

        st.markdown(f"**📚 {t('Skills', 'Skills')}**")
        cur_skill = st.number_input(
            t("Nível atual de skill (1-15)", "Current skill level (1-15)"),
            min_value=1, max_value=15, value=1, key="calc_cur_skill",
        )

        if tier == "Legendary":
            st.markdown(f"**💎 {t('Despertar', 'Awakening')}**")
            cur_awk = _awk_selectbox(t("Estágio atual", "Current stage"), "calc_cur_awk", 0)
        else:
            cur_awk = 0

        if hdata["has_hs"]:
            st.markdown(f"**✨ {t('Espírito Heroico', 'Heroic Spirit')}**")
            cur_hs = st.number_input(
                t("Nível atual (0-100)", "Current level (0-100)"),
                min_value=0, max_value=MAX_HS_LEVEL, value=0, key="calc_cur_hs",
            )
        else:
            cur_hs = 0

        if hdata["has_uw"]:
            st.markdown(f"**⚔️ {t('Equipamento Exclusivo (UW)', 'Exclusive Weapon (UW)')}**")
            cur_uw = st.number_input(
                t("Nível atual UW (0-20)", "Current UW level (0-20)"),
                min_value=0, max_value=MAX_UW_LEVEL, value=0, key="calc_cur_uw",
            )
        else:
            cur_uw = 0

        st.markdown(f"**🧬 {t('Traits', 'Traits')}**")
        cur_traits = []
        t_names = TRAIT_TYPE_NAMES_PT if lang == "pt" else TRAIT_TYPE_NAMES_EN
        for ti in range(4):
            cur_traits.append(st.number_input(
                f"{t_names[ti]} — {t('Atual', 'Current')}",
                min_value=0, max_value=MAX_TRAIT_LEVEL, value=0,
                key=f"calc_cur_trait_{ti}",
            ))

    with col_tgt:
        st.subheader("🎯 " + t("Estado Alvo", "Target State"))

        st.markdown(f"**⭐ {t('Estrelas', 'Stars')}**")
        tgt_leg = _leg_selectbox(t("Leg alvo", "Target leg"), "calc_tgt_leg", MAX_LEGS)

        st.markdown(f"**📚 {t('Skills', 'Skills')}**")
        tgt_skill = st.number_input(
            t("Nível alvo de skill (1-15)", "Target skill level (1-15)"),
            min_value=1, max_value=15, value=15, key="calc_tgt_skill",
        )

        if tier == "Legendary":
            st.markdown(f"**💎 {t('Despertar', 'Awakening')}**")
            tgt_awk = _awk_selectbox(t("Estágio alvo", "Target stage"), "calc_tgt_awk", MAX_AWK_STEP)
        else:
            tgt_awk = 0

        if hdata["has_hs"]:
            st.markdown(f"**✨ {t('Espírito Heroico', 'Heroic Spirit')}**")
            tgt_hs = st.number_input(
                t("Nível alvo (0-100)", "Target level (0-100)"),
                min_value=0, max_value=MAX_HS_LEVEL, value=MAX_HS_LEVEL, key="calc_tgt_hs",
            )
        else:
            tgt_hs = 0

        if hdata["has_uw"]:
            st.markdown(f"**⚔️ {t('Equipamento Exclusivo (UW)', 'Exclusive Weapon (UW)')}**")
            tgt_uw = st.number_input(
                t("Nível alvo UW (0-20)", "Target UW level (0-20)"),
                min_value=0, max_value=MAX_UW_LEVEL, value=MAX_UW_LEVEL, key="calc_tgt_uw",
            )
        else:
            tgt_uw = 0

        st.markdown(f"**🧬 {t('Traits', 'Traits')}**")
        tgt_traits = []
        for ti in range(4):
            tgt_traits.append(st.number_input(
                f"{t_names[ti]} — {t('Alvo', 'Target')}",
                min_value=0, max_value=MAX_TRAIT_LEVEL, value=MAX_TRAIT_LEVEL,
                key=f"calc_tgt_trait_{ti}",
            ))

    # Validation
    errors = []
    if tgt_leg < cur_leg:
        errors.append(t("⚠️ Leg alvo deve ser ≥ leg atual.", "⚠️ Target leg must be ≥ current leg."))
    if tgt_skill < cur_skill:
        errors.append(t("⚠️ Nível de skill alvo deve ser ≥ atual.", "⚠️ Target skill level must be ≥ current."))
    if tier == "Legendary" and tgt_awk < cur_awk:
        errors.append(t("⚠️ Estágio de despertar alvo deve ser ≥ atual.", "⚠️ Target awakening stage must be ≥ current."))
    for _ti in range(4):
        if tgt_traits[_ti] < cur_traits[_ti]:
            errors.append(t(f"⚠️ Trait {t_names[_ti]}: alvo deve ser ≥ atual.",
                            f"⚠️ Trait {t_names[_ti]}: target must be ≥ current."))
    for e in errors:
        st.error(e)

    # ── Results ────────────────────────────────────────────────────────────────
    if not errors:
        res = calc_hero(
            sel_hero,
            from_leg=cur_leg,    to_leg=tgt_leg,
            from_skill_lv=cur_skill, to_skill_lv=tgt_skill,
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
            st.subheader("📊 " + t("Recursos Necessários", "Resources Needed"))

            _metric_cols = st.columns(3)
            _col_i = 0

            def _metric(label: str, value: int, icon: str = ""):
                nonlocal _col_i
                with _metric_cols[_col_i % 3]:
                    if value > 0:
                        st.metric(f"{icon} {label}", f"{value:,}")
                _col_i += 1

            # Stars
            if res["star_shards"] > 0:
                _shard_label = (t("Fragmentos Míticos", "Mythic Shards")
                                if tier == "Mythic"
                                else t("Fragmentos Lendários", "Legendary Shards"))
                _metric(_shard_label, res["star_shards"], "⭐")

            # Skills
            if res["skill_books"] > 0:
                _metric(t("Livros de Habilidade", "Skill Books"), res["skill_books"], "📚")

            # Awakening
            if res["awk_shards"] > 0:
                _metric(t("Fragmentos (Despertar)", "Shards (Awakening)"), res["awk_shards"], "💎")
            if res["awk_ss"] > 0:
                _fac_name = _faction_name(faction)
                _metric(f"Soul Stones ({_fac_name})", res["awk_ss"], "💠")

            # Heroic Spirit
            if res["hs_shards"] > 0:
                _metric(t("Frags. Espírito Heroico", "Heroic Spirit Shards"), res["hs_shards"], "✨")

            # UW
            if res["uw_shards"] > 0:
                _metric(t("Frags. UW (específicos)", "UW Shards (specific)"), res["uw_shards"], "⚔️")

            # Traits
            if res["trait_diamonds"] > 0:
                _metric(t("Diamantes (Traits)", "Diamonds (Traits)"), res["trait_diamonds"], "💎")
            if res["trait_shards"] > 0:
                _metric(t("Frags. de Trait", "Trait Shards"), res["trait_shards"], "🧬")

            # Trait breakdown
            if any(tgt_traits[i] > cur_traits[i] for i in range(4)):
                with st.expander(t("🧬 Detalhamento de Traits", "🧬 Trait Breakdown")):
                    tr_rows = []
                    for ti in range(4):
                        if tgt_traits[ti] > cur_traits[ti]:
                            dia, frags = trait_cost(ti, cur_traits[ti], tgt_traits[ti])
                            tr_rows.append({
                                t("Tipo", "Type"):                     t_names[ti],
                                t("De → Para", "From → To"):           f"{cur_traits[ti]} → {tgt_traits[ti]}",
                                t("💎 Diamantes", "💎 Diamonds"):       dia if dia else "—",
                                t("🧬 Fragmentos", "🧬 Shards"):        frags if frags else "—",
                            })
                    if tr_rows:
                        st.dataframe(pd.DataFrame(tr_rows), use_container_width=True, hide_index=True)

            # ── Event Impact ──────────────────────────────────────────────────
            st.markdown("---")
            st.markdown("**📅 " + t("Impacto nos Eventos Regulares", "Regular Event Impact") + "**")

            ev_hd     = next(e for e in EVENTS if e["sheet"] == "Hero_Development")
            ev_hdname = ev_hd.get("name_pt", ev_hd["name"]) if lang == "pt" else ev_hd["name"]

            # Pts calculations (per Hero_Development event tasks)
            # task 0: Legendary Shard × 100 | task 10: Mythic Shard × 100
            # task 4: Soul Stone × 1500
            # task 5: Skill Books (10 books = 1 pt) → ×0.1/book
            # task 2: UW Shard (specific) × 100 | task 3: Universal UW × 100
            pts_shards  = res["star_shards"]  * (100 if tier == "Mythic" else 100)
            pts_books   = res["skill_books"]  * 0.1
            pts_ss      = res["awk_ss"]       * 1500
            pts_uw      = res["uw_shards"]    * 100
            pts_awk_sh  = res["awk_shards"]   * (100 if tier == "Mythic" else 100)
            pts_hd      = pts_shards + pts_awk_sh + pts_books + pts_ss + pts_uw

            _ev1, _ev2, _ev3, _ev4 = st.columns(4)
            _shard_lbl = t("Frag. Míticos", "Mythic Shards") if tier == "Mythic" else t("Frag. Lend.", "Leg. Shards")
            _ev1.metric(f"⭐ {_shard_lbl}", f"{pts_shards + pts_awk_sh:,.0f} pts",
                        help=f"{res['star_shards'] + res['awk_shards']:,} × 100")
            _ev2.metric(f"📚 {t('Livros', 'Books')}", f"{pts_books:,.0f} pts",
                        help=f"{res['skill_books']:,} × 0.1")
            if pts_ss > 0:
                _ev3.metric(f"💠 Soul Stones", f"{pts_ss:,.0f} pts",
                            help=f"{res['awk_ss']} × 1500")
            if pts_uw > 0:
                _ev4.metric(f"⚔️ UW", f"{pts_uw:,.0f} pts",
                            help=f"{res['uw_shards']:,} × 100")

            _ev5 = st.columns(1)[0]
            _ev5.metric(f"📊 {ev_hdname}", f"{pts_hd:,.0f} pts")

            _ms_hd = "  ".join(
                f"✅ {s['value']:,}" if s["reached"] else f"⬜ {s['value']:,}"
                for s in get_milestone_status(ev_hd["milestones"], pts_hd)
            )
            st.caption(f"Milestones: {_ms_hd}")

            if st.button("📅 " + t("Enviar para Eventos", "Send to Events"), key="send_hero_calc_evt"):
                st.session_state["_src_hero_Hero_Development"] = int(pts_hd)
                # Contribute to specific task indices
                if tier == "Mythic":
                    st.session_state["_calc_contrib_Hero_Development_10"] = int(pts_shards + pts_awk_sh)
                else:
                    st.session_state["_calc_contrib_Hero_Development_0"]  = int(pts_shards + pts_awk_sh)
                st.session_state["_calc_contrib_Hero_Development_4"]  = int(pts_ss)
                st.session_state["_calc_contrib_Hero_Development_5"]  = int(pts_books)
                st.session_state["_calc_contrib_Hero_Development_2"]  = int(pts_uw)
                st.session_state["_calc_sent_Hero_Development"]        = True
                st.success(t(
                    f"✅ {pts_hd:,.0f} pts enviados para **{ev_hdname}**!",
                    f"✅ {pts_hd:,.0f} pts sent to **{ev_hdname}**!",
                ))

# ══════════════════════════════════════════════════════════════════════════════
# ABA 2 — PLANEJADOR DE FILAS
# ══════════════════════════════════════════════════════════════════════════════
with tab_plan:
    st.caption(t(
        "Monte até 5 filas (4 regulares + 1 privilégio), cada uma com até 6 heróis da mesma facção. "
        "O plano consolida os recursos totais necessários.",
        "Build up to 5 queues (4 regular + 1 privilege), each with up to 6 heroes from the same faction. "
        "The plan consolidates total resources needed.",
    ))

    if "hero_queues" not in st.session_state:
        st.session_state["hero_queues"] = []

    # ── Add queue ──────────────────────────────────────────────────────────────
    st.markdown("**➕ " + t("Adicionar fila", "Add queue") + "**")
    _qc1, _qc2, _qc3 = st.columns(3)
    with _qc1:
        _q_type = st.selectbox(
            t("Tipo de fila", "Queue type"),
            [t("Regular", "Regular"), t("Privilégio", "Privilege")],
            key="q_type",
        )
    with _qc2:
        _q_fac_opts = [_faction_name(f) for f in ["Liga", "Horda", "Natureza"]]
        _q_fac_disp = st.selectbox(t("Facção", "Faction"), _q_fac_opts, key="q_faction")
        _q_fac_en   = {"Liga": "Liga", "League": "Liga",
                       "Horda": "Horda", "Horde": "Horda",
                       "Natureza": "Natureza", "Nature": "Natureza"}.get(_q_fac_disp, _q_fac_disp)
        # Recover internal key
        _q_fac = {_faction_name(f): f for f in ["Liga", "Horda", "Natureza"]}[_q_fac_disp]
    with _qc3:
        _avail = FACTION_HEROES[_q_fac]
        _q_heroes = st.multiselect(
            t("Heróis (até 6)", "Heroes (up to 6)"),
            _avail, max_selections=6, key="q_heroes",
        )

    if st.button("➕ " + t("Adicionar fila ao plano", "Add queue to plan"), key="q_add"):
        if not _q_heroes:
            st.warning(t("Selecione ao menos um herói.", "Select at least one hero."))
        else:
            st.session_state["hero_queues"].append({
                "type":    _q_type,
                "faction": _q_fac,
                "heroes":  list(_q_heroes),
            })
            st.rerun()

    queues = st.session_state["hero_queues"]

    if not queues:
        st.info(t("Nenhuma fila no plano. Adicione acima ↑", "No queues in plan. Add above ↑"))
    else:
        st.divider()
        st.subheader("📋 " + t("Filas planejadas", "Planned queues"))

        # Show queues
        for qi, q in enumerate(queues):
            f_ico_col, f_info_col, f_del_col = st.columns([1, 8, 1])
            with f_ico_col:
                _faction_icon(q["faction"], width=28)
            with f_info_col:
                _heroes_disp = " · ".join(f"**{h}**" for h in q["heroes"])
                _type_lbl = t("Privilégio", "Privilege") if q["type"] in ("Privilégio", "Privilege") else t("Regular", "Regular")
                st.markdown(f"**{_type_lbl} — {_faction_name(q['faction'])}:** {_heroes_disp}")
            with f_del_col:
                if st.button("🗑️", key=f"q_del_{qi}"):
                    queues.pop(qi)
                    st.rerun()

        # Consolidated targets (use max legs / max skill for all heroes in plan)
        st.divider()
        st.markdown("**⚙️ " + t("Configuração global do plano", "Global plan settings") + "**")
        _pc1, _pc2 = st.columns(2)
        with _pc1:
            _plan_tgt_leg = _leg_selectbox(t("Leg alvo (todos)", "Target leg (all)"), "plan_tgt_leg", MAX_LEGS)
            _plan_tgt_skill = st.number_input(
                t("Nível alvo de skill (todos)", "Target skill level (all)"),
                min_value=1, max_value=15, value=15, key="plan_tgt_skill",
            )
        with _pc2:
            _plan_tgt_uw = st.number_input(
                t("Nível alvo UW (todos com UW)", "Target UW level (all with UW)"),
                min_value=0, max_value=MAX_UW_LEVEL, value=MAX_UW_LEVEL, key="plan_tgt_uw",
            )
            _plan_tgt_hs = st.number_input(
                t("Nível alvo Espírito Heroico", "Target Heroic Spirit level"),
                min_value=0, max_value=MAX_HS_LEVEL, value=MAX_HS_LEVEL, key="plan_tgt_hs",
            )

        # Compute totals
        all_plan_heroes = list({h for q in queues for h in q["heroes"]})
        total_plan: dict = {
            "star_shards_mythic": 0, "star_shards_legendary": 0,
            "skill_books": 0, "awk_shards": 0, "awk_ss_liga": 0,
            "awk_ss_horda": 0, "awk_ss_natureza": 0,
            "hs_shards": 0, "uw_shards": 0,
        }

        for h in all_plan_heroes:
            hd = HEROES[h]
            r = calc_hero(
                h,
                to_leg=_plan_tgt_leg,
                to_skill_lv=_plan_tgt_skill,
                to_awk=(MAX_AWK_STEP if hd["tier"] == "Legendary" else 0),
                to_hs=(_plan_tgt_hs if hd["has_hs"] else 0),
                to_uw=(_plan_tgt_uw if hd["has_uw"] else 0),
            )
            if hd["tier"] == "Mythic":
                total_plan["star_shards_mythic"] += r["star_shards"]
            else:
                total_plan["star_shards_legendary"] += r["star_shards"] + r["awk_shards"]
            total_plan["skill_books"] += r["skill_books"]
            if hd["tier"] == "Legendary":
                _ss_key = f"awk_ss_{hd['faction'].lower()}"
                total_plan[_ss_key] = total_plan.get(_ss_key, 0) + r["awk_ss"]
            total_plan["hs_shards"]  += r["hs_shards"]
            total_plan["uw_shards"]  += r["uw_shards"]

        st.divider()
        st.subheader("📊 " + t("Totais do plano", "Plan totals"))

        _tm1, _tm2, _tm3 = st.columns(3)
        if total_plan["star_shards_mythic"] > 0:
            _tm1.metric(t("⭐ Frags. Míticos", "⭐ Mythic Shards"),
                        f"{total_plan['star_shards_mythic']:,}")
        if total_plan["star_shards_legendary"] > 0:
            _tm2.metric(t("⭐ Frags. Lendários", "⭐ Legendary Shards"),
                        f"{total_plan['star_shards_legendary']:,}")
        if total_plan["skill_books"] > 0:
            _tm3.metric(t("📚 Livros de Habilidade", "📚 Skill Books"),
                        f"{total_plan['skill_books']:,}")

        _tm4, _tm5, _tm6 = st.columns(3)
        for _fac, _key in [("Liga", "awk_ss_liga"), ("Horda", "awk_ss_horda"), ("Natureza", "awk_ss_natureza")]:
            _ss_val = total_plan.get(_key, 0)
            if _ss_val > 0:
                _tm4.metric(f"💠 Soul Stones ({_faction_name(_fac)})", f"{_ss_val:,}")

        if total_plan["hs_shards"] > 0:
            _tm5.metric(t("✨ Frags. Espírito Heroico", "✨ Heroic Spirit Shards"),
                        f"{total_plan['hs_shards']:,}")
        if total_plan["uw_shards"] > 0:
            _tm6.metric(t("⚔️ Frags. UW (total)", "⚔️ UW Shards (total)"),
                        f"{total_plan['uw_shards']:,}")

        st.divider()
        if st.button("🗑️ " + t("Limpar plano", "Clear plan"), key="q_clear"):
            st.session_state["hero_queues"] = []
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# ABA 3 — REFERÊNCIA
# ══════════════════════════════════════════════════════════════════════════════
with tab_ref:
    ref1, ref2 = st.tabs([
        "⭐ " + t("Estrelas", "Stars"),
        "📚 " + t("Skills / UW / HS", "Skills / UW / HS"),
    ])

    with ref1:
        _rc1, _rc2 = st.columns(2)
        with _rc1:
            st.subheader(t("⭐ Custo por Leg — Lendário", "⭐ Cost per Leg — Legendary"))
            st.caption(t("Total: 500 fragmentos (75 legs)", "Total: 500 shards (75 legs)"))
            rows_leg = []
            for _li in range(1, MAX_LEGS + 1):
                from hero_engine import LEGENDARY_LEG_COSTS
                rows_leg.append({
                    t("Leg", "Leg"): _li,
                    t("Custo", "Cost"): LEGENDARY_LEG_COSTS[_li - 1],
                    t("Acum.", "Cum."): LEGENDARY_CUMUL[_li],
                })
            st.dataframe(pd.DataFrame(rows_leg).set_index(t("Leg", "Leg")),
                         use_container_width=True, height=400)
        with _rc2:
            st.subheader(t("⭐ Custo por Leg — Mítico", "⭐ Cost per Leg — Mythic"))
            st.caption(t("Total: 1000 fragmentos (75 legs)", "Total: 1000 shards (75 legs)"))
            from hero_engine import MYTHIC_LEG_COSTS
            rows_myt = []
            for _li in range(1, MAX_LEGS + 1):
                rows_myt.append({
                    t("Leg", "Leg"): _li,
                    t("Custo", "Cost"): MYTHIC_LEG_COSTS[_li - 1],
                    t("Acum.", "Cum."): MYTHIC_CUMUL[_li],
                })
            st.dataframe(pd.DataFrame(rows_myt).set_index(t("Leg", "Leg")),
                         use_container_width=True, height=400)

    with ref2:
        _sr1, _sr2, _sr3 = st.columns(3)
        with _sr1:
            st.subheader(t("📚 Livros de Skill", "📚 Skill Books"))
            rows_sk = [{"LVL": i+1, t("Custo", "Cost"): SKILL_BOOK_COSTS[i],
                        t("Acum.", "Cum."): SKILL_BOOK_CUMUL[i]}
                       for i in range(len(SKILL_BOOK_COSTS))]
            st.dataframe(pd.DataFrame(rows_sk).set_index("LVL"),
                         use_container_width=True, height=400)
        with _sr2:
            st.subheader(t("⚔️ Custo UW (por nível)", "⚔️ UW Cost (per level)"))
            st.caption(t(f"Total: {UW_CUMUL[20]:,} fragmentos", f"Total: {UW_CUMUL[20]:,} shards"))
            rows_uw = [{"LVL": i+1, t("Custo", "Cost"): UW_SHARDS_PER_LEVEL[i],
                        t("Acum.", "Cum."): UW_CUMUL[i+1]}
                       for i in range(MAX_UW_LEVEL)]
            st.dataframe(pd.DataFrame(rows_uw).set_index("LVL"),
                         use_container_width=True, height=400)
        with _sr3:
            st.subheader(t("✨ Espírito Heroico (simples)", "✨ Heroic Spirit (simple)"))
            st.caption(t(f"Total: {HS_CUMUL[100]:,} fragmentos", f"Total: {HS_CUMUL[100]:,} shards"))
            rows_hs = [{"LVL": _lv, t("Custo", "Cost"): HS_COST_PER_LEVEL[_lv],
                        t("Acum.", "Cum."): HS_CUMUL[_lv]}
                       for _lv in range(1, MAX_HS_LEVEL + 1)]
            st.dataframe(pd.DataFrame(rows_hs).set_index("LVL"),
                         use_container_width=True, height=400)
