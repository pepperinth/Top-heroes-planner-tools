"""
pages/1_Reliquias.py — Relic Optimizer page.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from behemoth_engine import STAR_IMAGES, show_star_image
from relic_optimizer import (
    ALL_RELICS, UNIVERSAL_RELICS, ALL_SET_RELICS, SETS,
    STAR_OPTIONS, PREFERRED_INTER,
    star_leg_to_idx, idx_to_star_leg,
    compute_route, shards_needed,
)

st.set_page_config(page_title="Relic Optimizer", page_icon="⚜️", layout="wide")

# ── Language ───────────────────────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "pt"

with st.sidebar:
    st.markdown("### 🌐 Idioma / Language")
    lang_pick = st.radio(
        "", ["🇧🇷 Português", "🇬🇧 English"],
        index=0 if st.session_state.lang == "pt" else 1,
        horizontal=True, label_visibility="collapsed", key="lang_rel",
    )
    st.session_state.lang = "pt" if "Português" in lang_pick else "en"
    st.divider()
    st.page_link("app.py", label="← Home")

lang = st.session_state.lang
def t(pt, en): return pt if lang == "pt" else en

_BASE      = os.path.dirname(os.path.dirname(__file__))
_TIER_BASE = {"Y": 0, "R": 25, "P": 50, "B": 75}

def _relic_star_idx(star_str: str, leg_str: str) -> int:
    """Convert 'Y★3' + '2/5' → STAR_IMAGES index.
    Tiers: Y=Gold(0-25), R=Red(26-50), P=Platinum(51-75), B=Black(76-80 complete only).
    """
    if star_str == "0★":
        return 0
    prefix = star_str[0]
    n      = int(star_str.split("★")[1])
    base   = _TIER_BASE.get(prefix, 0)
    if prefix == "B":
        return base + n
    return base + (n - 1) * 5 + int(leg_str.split("/")[0])

def _show_relic_star(star_str: str, leg_str: str):
    show_star_image(_relic_star_idx(star_str, leg_str), _BASE, st)

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("⚜️ " + t("Otimizador de Relíquias", "Relic Optimizer"))
st.caption(t("Calcula a rota de Miracle Hammer para maximizar os níveis das relíquias.",
             "Calculates the Miracle Hammer route to maximise relic levels."))

LEG_OPTIONS = ["1/5", "2/5", "3/5", "4/5", "5/5"]

# ── Configuration ──────────────────────────────────────────────────────────────
with st.expander(t("⚙️ Configuração", "⚙️ Configuration"), expanded=True):

    mode = st.radio(
        t("Modo", "Mode"),
        [t("Set completo", "Full set"), t("Relíquia única", "Single relic")],
        horizontal=True, key="relic_mode",
    )
    single_mode = mode == t("Relíquia única", "Single relic")

    st.divider()

    if not single_mode:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            _SET_PT = {"League": "Liga", "Horde": "Horda", "Nature": "Natureza"}
            _set_opts = [t(_SET_PT[k], k) for k in SETS.keys()]
            _set_disp = st.selectbox(t("Conjunto alvo", "Target set"), _set_opts, index=0)
            target_set = {"Liga": "League", "Horda": "Horde", "Natureza": "Nature"}.get(_set_disp, _set_disp)
        with c2:
            tgt_star = st.selectbox(t("Estrela alvo", "Target star"), STAR_OPTIONS[1:], index=0)
            tgt_leg  = st.selectbox(t("Leg alvo", "Target leg"), LEG_OPTIONS, index=0)
            _show_relic_star(tgt_star, tgt_leg)
        with c3:
            hammers  = st.number_input(t("Miracle Hammers", "Miracle Hammers"), min_value=1, max_value=30, value=1)
            univ     = st.number_input(t("Fragmentos universais", "Universal shards"), min_value=0, value=0, step=10)
        with c4:
            inter1 = st.selectbox(t("Relay 1 (obrigatório)", "Relay 1 (mandatory)"), UNIVERSAL_RELICS, index=0)
            inter2 = st.selectbox(t("Relay 2 (obrigatório)", "Relay 2 (mandatory)"), ["—"] + UNIVERSAL_RELICS, index=0)
            inter2_val = inter2 if inter2 != "—" else ""

        set_relics = SETS[target_set]
        st.markdown(t("**Prioridade dentro do conjunto:**", "**Priority within set:**"))
        pcols = st.columns(len(set_relics))
        priority = []
        for i, (col, rel) in enumerate(zip(pcols, set_relics)):
            with col:
                picked = st.selectbox(f"#{i+1}", set_relics, index=i, key=f"prio_{i}")
                priority.append(picked)

    else:  # single relic mode
        s1, s2, s3, s4 = st.columns(4)
        with s1:
            single_relic = st.selectbox(
                t("Relíquia alvo", "Target relic"),
                ALL_RELICS,
                key="single_relic_sel",
            )
            relic_kind = t("Universal", "Universal") if single_relic in UNIVERSAL_RELICS else t("Set", "Set")
            st.caption(relic_kind)
        with s2:
            tgt_star = st.selectbox(t("Estrela alvo", "Target star"), STAR_OPTIONS[1:], index=0, key="sr_tgt_star")
            tgt_leg  = st.selectbox(t("Leg alvo", "Target leg"), LEG_OPTIONS, index=0, key="sr_tgt_leg")
            _show_relic_star(tgt_star, tgt_leg)
        with s3:
            hammers = st.number_input(t("Miracle Hammers", "Miracle Hammers"), min_value=1, max_value=30, value=1, key="sr_hammers")
            univ    = st.number_input(t("Fragmentos universais", "Universal shards"), min_value=0, value=0, step=10, key="sr_univ")
        with s4:
            inter1 = st.selectbox(t("Relay 1 (obrigatório)", "Relay 1 (mandatory)"), UNIVERSAL_RELICS, index=0, key="sr_inter1")
            inter2 = st.selectbox(t("Relay 2 (obrigatório)", "Relay 2 (mandatory)"), ["—"] + UNIVERSAL_RELICS, index=0, key="sr_inter2")
            inter2_val = inter2 if inter2 != "—" else ""
        target_set = ""
        priority   = []

# ── Inventory table ────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader(t("📦 Inventário de Relíquias", "📦 Relic Inventory"))
st.caption(t("Preencha os dados das relíquias que possui. Relíquias universais com 0 fragmentos serão ignoradas como relay.",
             "Fill in your relic data. Universal relics with 0 shards will be ignored as relays."))

inv_rows = []
for relic in ALL_RELICS:
    kind = t("Universal", "Universal") if relic in UNIVERSAL_RELICS else t("Set", "Set")
    inv_rows.append({
        t("Relíquia", "Relic"):          relic,
        t("Tipo", "Type"):               kind,
        t("Estrela", "Star"):            "0★",
        t("Leg", "Leg"):                 "—",
        t("Frag. específicos", "Spec. shards"): 0,
        t("Usar?", "Use?"):              True,
    })

df_inv = pd.DataFrame(inv_rows)

edited = st.data_editor(
    df_inv,
    use_container_width=True,
    hide_index=True,
    disabled=[t("Relíquia", "Relic"), t("Tipo", "Type")],
    column_config={
        t("Estrela", "Star"): st.column_config.SelectboxColumn(options=STAR_OPTIONS),
        t("Leg", "Leg"):      st.column_config.SelectboxColumn(options=["—"] + LEG_OPTIONS),
        t("Frag. específicos", "Spec. shards"): st.column_config.NumberColumn(min_value=0, step=1),
        t("Usar?", "Use?"):   st.column_config.CheckboxColumn(),
    },
    key="inv_table",
)

# ── Run ────────────────────────────────────────────────────────────────────────
st.markdown("---")
if st.button(f"🔍 {t('Calcular rota', 'Calculate route')}", type="primary", use_container_width=True):
    # Build inv dict from edited table
    relics_dict = {}
    for _, row in edited.iterrows():
        name    = row[t("Relíquia", "Relic")]
        star    = row[t("Estrela", "Star")]
        leg_raw = row[t("Leg", "Leg")]
        leg     = leg_raw if leg_raw != "—" else "1/5"
        _spec_raw = row[t("Frag. específicos", "Spec. shards")]
        spec    = int(_spec_raw) if _spec_raw == _spec_raw else 0  # NaN guard
        can_use = bool(row[t("Usar?", "Use?")])
        relics_dict[name] = {
            "star_idx":        star_leg_to_idx(star, leg),
            "specific_shards": spec,
            "can_use":         can_use,
        }

    target_level = star_leg_to_idx(tgt_star, tgt_leg)
    priority_active = [p for p in priority
                       if relics_dict.get(p, {}).get("can_use", True)]

    inv = {
        "universal_shards": univ,
        "relics": relics_dict,
        "config": {
            "target_set":    "" if single_mode else target_set,
            "target_relic":  single_relic if single_mode else "",
            "priority":      [] if single_mode else priority_active,
            "inter1":        inter1,
            "inter2":        inter2_val,
            "target_level":  target_level,
            "hammers_avail": hammers,
        },
    }

    with st.spinner(t("Calculando rota ótima…", "Calculating optimal route…")):
        route = compute_route(inv)

    if not route["targets"]:
        st.info(t("Todas as relíquias alvo já atingiram a meta.", "All target relics already reached the goal."))
    else:
        # ── Results ────────────────────────────────────────────────────────────
        st.subheader(t("✅ Resultado", "✅ Result"))

        # Per-target summary
        res_rows = []
        tgt_star_label, tgt_leg_label = idx_to_star_leg(target_level)
        for tgt in route["targets"]:
            orig  = relics_dict.get(tgt, {}).get("star_idx", 0)
            final = route["final_levels"].get(tgt, orig)
            fs, fl = idx_to_star_leg(final)
            os_, ol = idx_to_star_leg(orig)
            reached = final >= target_level
            missing = shards_needed(final, target_level) if not reached else 0
            res_rows.append({
                t("Relíquia", "Relic"):    tgt,
                t("Antes", "Before"):      f"{os_} {ol}",
                t("Depois", "After"):      f"{fs} {fl}",
                t("Meta", "Goal"):         "✅" if reached else f"❌ (-{missing:,} frags)",
            })

        st.dataframe(pd.DataFrame(res_rows), use_container_width=True, hide_index=True)

        # Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric(t("Hammers usados", "Hammers used"),
                  f"{route['hammers_used']} / {hammers}")
        m2.metric(t("Fragmentos universais usados", "Universal shards used"),
                  f"{route['universal_used']:,} / {univ:,}")
        m3.metric(t("Saldo universal", "Universal balance"),
                  f"{univ - route['universal_used']:,}")

        # Assignment
        if route.get("assignment"):
            st.markdown(t("**Atribuição dos relays obrigatórios:**",
                          "**Mandatory relay assignment:**"))
            for t_idx, mname in sorted(route["assignment"].items()):
                if t_idx < len(route["targets"]):
                    st.markdown(f"- **{mname}** → {route['targets'][t_idx]}")

        if route.get("suboptimal_note"):
            st.warning(route["suboptimal_note"])

        # Step-by-step
        with st.expander(t("📋 Passo a passo", "📋 Step by step")):
            step_rows = []
            step_num  = 0
            for step in route["steps"]:
                if step["type"] == "swap":
                    a_s, a_l = idx_to_star_leg(step["a_from"])
                    b_s, b_l = idx_to_star_leg(step["b_to"])
                    step_rows.append({
                        "#":                    "🔨",
                        t("Ação", "Action"):     "Miracle Hammer SWAP",
                        t("Relíquia A", "Relic A"): f"{step['relic_a']} ({a_s} {a_l})",
                        t("Relíquia B", "Relic B"): f"{step['relic_b']} ({b_s} {b_l})",
                        t("Frag. esp.", "Sp. shards"): "—",
                        t("Frag. univ.", "Univ. shards"): "—",
                    })
                else:
                    step_num += 1
                    f_s, f_l = idx_to_star_leg(step["from"])
                    t_s, t_l = idx_to_star_leg(step["to"])
                    step_rows.append({
                        "#":                    step_num,
                        t("Ação", "Action"):     f"Develop → {t_s} {t_l}",
                        t("Relíquia A", "Relic A"): step["relic"],
                        t("Relíquia B", "Relic B"): f"{f_s} {f_l} → {t_s} {t_l}",
                        t("Frag. esp.", "Sp. shards"): step["sp_used"] or "—",
                        t("Frag. univ.", "Univ. shards"): step["u_used"] or "—",
                    })
            st.dataframe(pd.DataFrame(step_rows), use_container_width=True, hide_index=True)
