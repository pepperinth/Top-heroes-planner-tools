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
    STAR_OPTIONS, PREFERRED_INTER, RELIC_NAME_PT,
    star_leg_to_idx, idx_to_star_leg,
    compute_route, shards_needed,
)
from events_data import EVENTS, get_milestone_status
from ui_utils import inject_global_css, section_header, results_header
import persistence

st.set_page_config(page_title="Relic Optimizer", page_icon="⚜️", layout="wide")

# ── Persistence ────────────────────────────────────────────────────────────────
_cm = persistence.new_manager("relics")

if "rel_initialized" not in st.session_state:
    _saved = persistence.load(_cm, "th_relics")
    if _saved and "inv_table" in _saved:
        st.session_state["inv_table"] = _saved["inv_table"]
    st.session_state["rel_initialized"] = True


def _relics_save():
    persistence.save(_cm, "th_relics", {
        "inv_table": st.session_state.get("inv_table", {}),
    })


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
    st.caption("🍪 " + (
        "Inventário salvo no seu browser."
        if st.session_state.lang == "pt" else
        "Inventory saved in your browser."
    ))
    st.divider()
    st.page_link("app.py", label="← Home")

lang = st.session_state.lang
def t(pt, en): return pt if lang == "pt" else en

_BASE      = os.path.dirname(os.path.dirname(__file__))
_TIER_BASE = {"Y": 0, "R": 25, "P": 50, "B": 75}
_RELIC_TO_EN = {v: k for k, v in RELIC_NAME_PT.items()}

def _rn(relic: str) -> str:
    return RELIC_NAME_PT.get(relic, relic) if lang == "pt" else relic

def _rn_en(display: str) -> str:
    return _RELIC_TO_EN.get(display, display)

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
inject_global_css()
st.title("⚜️ " + t("Otimizador de Relíquias", "Relic Optimizer"))
st.caption(t("Calcula a rota de Martelo Milagroso para maximizar os níveis das relíquias.",
             "Calculates the Miracle Hammer route to maximise relic levels."))

LEG_OPTIONS = ["1/5", "2/5", "3/5", "4/5", "5/5"]

tab_main, tab_help = st.tabs([
    "🔍 " + t("Otimizador", "Optimizer"),
    "📖 " + t("Instruções & Referência", "Instructions & Reference"),
])

with tab_main:

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
                tgt_leg  = st.selectbox(t("Perna alvo", "Target leg"), LEG_OPTIONS, index=0)
                _show_relic_star(tgt_star, tgt_leg)
            with c3:
                hammers  = st.number_input(t("Martelos Milagrosos", "Miracle Hammers"), min_value=1, max_value=30, value=1)
                univ     = st.number_input(t("Fragmentos universais", "Universal shards"), min_value=0, value=0, step=10)
            with c4:
                _univ_disp = [_rn(r) for r in UNIVERSAL_RELICS]
                inter1_d = st.selectbox(t("Relay 1 (obrigatório)", "Relay 1 (mandatory)"), _univ_disp, index=0)
                inter2_d = st.selectbox(t("Relay 2 (obrigatório)", "Relay 2 (mandatory)"), ["—"] + _univ_disp, index=0)
                inter1     = _rn_en(inter1_d)
                inter2_val = _rn_en(inter2_d) if inter2_d != "—" else ""

            set_relics = SETS[target_set]
            st.markdown(t("**Prioridade dentro do conjunto:**", "**Priority within set:**"))
            _set_disp = [_rn(r) for r in set_relics]
            pcols = st.columns(len(set_relics))
            priority = []
            for i, col in enumerate(pcols):
                with col:
                    picked_d = st.selectbox(f"#{i+1}", _set_disp, index=i, key=f"prio_{i}")
                    priority.append(_rn_en(picked_d))

            st.divider()
            st.markdown(t("**Primeira relay por alvo** *(opcional — a semente trocará com ela primeiro)*",
                          "**First relay per target** *(optional — the seed swaps into it first)*"))
            _fr_opts  = ["—"] + [_rn(r) for r in UNIVERSAL_RELICS]
            _fr_cols  = st.columns(len(set_relics))
            first_relays_ui: dict = {}
            for i, (col, tgt) in enumerate(zip(_fr_cols, set_relics)):
                with col:
                    fr_d = st.selectbox(_rn(tgt), _fr_opts, index=0, key=f"fr_{i}")
                    if fr_d != "—":
                        first_relays_ui[tgt] = _rn_en(fr_d)

        else:  # single relic mode
            s1, s2, s3, s4 = st.columns(4)
            with s1:
                _all_disp = [_rn(r) for r in ALL_RELICS]
                single_relic_d = st.selectbox(
                    t("Relíquia alvo", "Target relic"),
                    _all_disp,
                    key="single_relic_sel",
                )
                single_relic = _rn_en(single_relic_d)
                relic_kind = t("Universal", "Universal") if single_relic in UNIVERSAL_RELICS else t("Set", "Set")
                st.caption(relic_kind)
            with s2:
                tgt_star = st.selectbox(t("Estrela alvo", "Target star"), STAR_OPTIONS[1:], index=0, key="sr_tgt_star")
                tgt_leg  = st.selectbox(t("Perna alvo", "Target leg"), LEG_OPTIONS, index=0, key="sr_tgt_leg")
                _show_relic_star(tgt_star, tgt_leg)
            with s3:
                hammers = st.number_input(t("Martelos Milagrosos", "Miracle Hammers"), min_value=1, max_value=30, value=1, key="sr_hammers")
                univ    = st.number_input(t("Fragmentos universais", "Universal shards"), min_value=0, value=0, step=10, key="sr_univ")
            with s4:
                _univ_disp_sr = [_rn(r) for r in UNIVERSAL_RELICS]
                inter1_sr = st.selectbox(t("Relay 1 (obrigatório)", "Relay 1 (mandatory)"), _univ_disp_sr, index=0, key="sr_inter1")
                inter2_sr = st.selectbox(t("Relay 2 (obrigatório)", "Relay 2 (mandatory)"), ["—"] + _univ_disp_sr, index=0, key="sr_inter2")
                inter1     = _rn_en(inter1_sr)
                inter2_val = _rn_en(inter2_sr) if inter2_sr != "—" else ""
            target_set      = ""
            priority        = []
            first_relays_ui = {}

    # ── Inventory table ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader(t("📦 Inventário de Relíquias", "📦 Relic Inventory"))
    st.caption(t("Preencha os dados das relíquias que possui. Relíquias universais com 0 fragmentos serão ignoradas como relay.",
                 "Fill in your relic data. Universal relics with 0 shards will be ignored as relays."))

    inv_rows = []
    for relic in ALL_RELICS:
        kind = t("Universal", "Universal") if relic in UNIVERSAL_RELICS else t("Set", "Set")
        inv_rows.append({
            t("Relíquia", "Relic"):          _rn(relic),
            t("Tipo", "Type"):               kind,
            t("Estrela", "Star"):            "0★",
            t("Perna", "Leg"):                 "—",
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
            t("Perna", "Leg"):      st.column_config.SelectboxColumn(options=["—"] + LEG_OPTIONS),
            t("Frag. específicos", "Spec. shards"): st.column_config.NumberColumn(min_value=0, step=1),
            t("Usar?", "Use?"):   st.column_config.CheckboxColumn(),
        },
        key="inv_table",
        on_change=_relics_save,
    )

    # ── Run ────────────────────────────────────────────────────────────────────────
    st.markdown("---")
    if st.button(f"🔍 {t('Calcular rota', 'Calculate route')}", type="primary", use_container_width=True):
        # Build inv dict from edited table
        relics_dict = {}
        for _, row in edited.iterrows():
            name    = _rn_en(row[t("Relíquia", "Relic")])
            star    = row[t("Estrela", "Star")]
            leg_raw = row[t("Perna", "Leg")]
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
                "first_relays":  first_relays_ui,
            },
        }

        with st.spinner(t("Calculando rota ótima…", "Calculating optimal route…")):
            route = compute_route(inv)

        if not route["targets"]:
            st.info(t("Todas as relíquias alvo já atingiram a meta.", "All target relics already reached the goal."))
        else:
            # ── Results ────────────────────────────────────────────────────────────
            results_header(t("✅ Resultado", "✅ Result"))

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
                    t("Relíquia", "Relic"):    _rn(tgt),
                    t("Antes", "Before"):      f"{os_} {ol}",
                    t("Depois", "After"):      f"{fs} {fl}",
                    t("Meta", "Goal"):         "✅" if reached else f"❌ (-{missing:,} frags)",
                })

            st.dataframe(pd.DataFrame(res_rows), use_container_width=True, hide_index=True)

            # Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric(t("Martelos usados", "Hammers used"),
                      f"{route['hammers_used']} / {hammers}")
            m2.metric(t("Fragmentos universais usados", "Universal shards used"),
                      f"{route['universal_used']:,} / {univ:,}")
            m3.metric(t("Saldo universal", "Universal balance"),
                      f"{univ - route['universal_used']:,}")

            # Assignment
            if route.get("assignment"):
                st.markdown(t("**Atribuição dos relays obrigatórios:**",
                              "**Mandatory relay assignment:**"))
                for tname, mlist in sorted(route["assignment"].items()):
                    for mname in mlist:
                        st.markdown(f"- **{_rn(mname)}** → {_rn(tname)}")

            if route.get("suboptimal_note"):
                st.warning(route["suboptimal_note"])

            opt = route.get("optimal_result")
            if opt:
                with st.expander(t("🏆 Resultado ótimo (sem restrições do usuário)",
                                   "🏆 Optimal result (no user constraints)")):
                    # Per-target summary for optimal
                    opt_rows = []
                    for tgt in opt["targets"]:
                        orig  = relics_dict.get(tgt, {}).get("star_idx", 0)
                        final = opt["final_levels"].get(tgt, orig)
                        fs, fl_s = idx_to_star_leg(final)
                        os_, ol  = idx_to_star_leg(orig)
                        reached  = final >= target_level
                        missing  = shards_needed(final, target_level) if not reached else 0
                        opt_rows.append({
                            t("Relíquia", "Relic"):  _rn(tgt),
                            t("Antes", "Before"):    f"{os_} {ol}",
                            t("Depois", "After"):    f"{fs} {fl_s}",
                            t("Meta", "Goal"):       "✅" if reached else f"❌ (-{missing:,})",
                        })
                    st.dataframe(pd.DataFrame(opt_rows), use_container_width=True, hide_index=True)

                    oc1, oc2, oc3 = st.columns(3)
                    oc1.metric(t("Martelos usados", "Hammers used"),
                               f"{opt['hammers_used']} / {hammers}")
                    oc2.metric(t("Fragmentos universais usados", "Universal shards used"),
                               f"{opt['universal_used']:,} / {univ:,}")
                    oc3.metric(t("Saldo universal", "Universal balance"),
                               f"{univ - opt['universal_used']:,}")

                    if opt.get("assignment"):
                        st.markdown(t("**Atribuição dos relays:**", "**Relay assignment:**"))
                        for tname, mlist in sorted(opt["assignment"].items()):
                            for mname in mlist:
                                st.markdown(f"- **{_rn(mname)}** → {_rn(tname)}")

                    with st.expander(t("📋 Passo a passo ótimo", "📋 Optimal step by step")):
                        opt_step_rows = []
                        opt_step_num  = 0
                        for step in opt["steps"]:
                            if step["type"] == "swap":
                                a_s, a_l = idx_to_star_leg(step["a_from"])
                                b_s, b_l = idx_to_star_leg(step["b_to"])
                                opt_step_rows.append({
                                    "#":                         "🔨",
                                    t("Ação", "Action"):          t("Swap", "Swap"),
                                    t("Relíquia A", "Relic A"):   f"{_rn(step['relic_a'])} ({a_s} {a_l})",
                                    t("Relíquia B", "Relic B"):   f"{_rn(step['relic_b'])} ({b_s} {b_l})",
                                    t("Frag. esp.", "Sp. shards"): "—",
                                    t("Frag. univ.", "Univ. shards"): "—",
                                })
                            else:
                                opt_step_num += 1
                                f_s, f_l = idx_to_star_leg(step["from"])
                                t_s, t_l = idx_to_star_leg(step["to"])
                                opt_step_rows.append({
                                    "#":                         opt_step_num,
                                    t("Ação", "Action"):          f"{t('Desenvolver','Develop')} → {t_s} {t_l}",
                                    t("Relíquia A", "Relic A"):   _rn(step["relic"]),
                                    t("Relíquia B", "Relic B"):   f"{f_s} {f_l} → {t_s} {t_l}",
                                    t("Frag. esp.", "Sp. shards"): step["sp_used"] or "—",
                                    t("Frag. univ.", "Univ. shards"): step["u_used"] or "—",
                                })
                        st.dataframe(pd.DataFrame(opt_step_rows), use_container_width=True, hide_index=True)

            # ── Impacto nos Eventos Regulares ─────────────────────────────────────
            st.markdown("---")
            st.markdown("**📅 " + t("Impacto nos Eventos Regulares", "Regular Event Impact") + "**")

            ev_rr     = next(e for e in EVENTS if e["sheet"] == "Relic_Race")
            ev_rrname = ev_rr.get("name_pt", ev_rr["name"]) if lang == "pt" else ev_rr["name"]

            # All relics in the optimizer are Legendary → all shards are Legendary relic shards (×120)
            # Use the actual sp_used + u_used from each develop step (not leg-transition counting).
            _leg_sh = sum(
                _step["sp_used"] + _step["u_used"]
                for _step in route["steps"]
                if _step["type"] == "develop"
            )
            _pts_leg = _leg_sh * 120
            _pts_rr  = _pts_leg

            _rc1, _rc2 = st.columns(2)
            _rc1.metric(t("Frags. Lendários gastos (×120)", "Legendary Shards spent (×120)"),
                        f"{_leg_sh:,}")
            _rc2.metric(f"📊 {ev_rrname}", f"{_pts_rr:,.0f} pts")

            _ms_rr = "  ".join(
                f"✅ {s['value']:,}" if s["reached"] else f"⬜ {s['value']:,}"
                for s in get_milestone_status(ev_rr["milestones"], _pts_rr)
            )
            st.caption(f"Milestones: {_ms_rr}")

            if st.button("📅 " + t("Enviar para Eventos", "Send to Events"), key="send_relic_evt"):
                st.session_state["_src_relic_opt_Relic_Race"]   = int(_pts_rr)
                st.session_state["_calc_contrib_Relic_Race_5"]  = int(_pts_leg)
                st.session_state["_calc_sent_Relic_Race"]       = True
                st.success(t(
                    f"✅ {_pts_rr:,.0f} pts enviados para **{ev_rrname}**! Acesse Eventos Regulares.",
                    f"✅ {_pts_rr:,.0f} pts sent to **{ev_rrname}**! Go to Regular Events.",
                ))

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
                            t("Ação", "Action"):     t("Martelo Milagroso (SWAP)", "Miracle Hammer SWAP"),
                            t("Relíquia A", "Relic A"): f"{_rn(step['relic_a'])} ({a_s} {a_l})",
                            t("Relíquia B", "Relic B"): f"{_rn(step['relic_b'])} ({b_s} {b_l})",
                            t("Frag. esp.", "Sp. shards"): "—",
                            t("Frag. univ.", "Univ. shards"): "—",
                        })
                    else:
                        step_num += 1
                        f_s, f_l = idx_to_star_leg(step["from"])
                        t_s, t_l = idx_to_star_leg(step["to"])
                        step_rows.append({
                            "#":                    step_num,
                            t("Ação", "Action"):     f"{t('Desenvolver','Develop')} → {t_s} {t_l}",
                            t("Relíquia A", "Relic A"): _rn(step["relic"]),
                            t("Relíquia B", "Relic B"): f"{f_s} {f_l} → {t_s} {t_l}",
                            t("Frag. esp.", "Sp. shards"): step["sp_used"] or "—",
                            t("Frag. univ.", "Univ. shards"): step["u_used"] or "—",
                        })
                st.dataframe(pd.DataFrame(step_rows), use_container_width=True, hide_index=True)

with tab_help:
    _hi1, _hi2 = st.tabs([
        "📖 " + t("Como usar", "How to use"),
        "📊 " + t("Referência de dados", "Data reference"),
    ])

    with _hi1:
        st.markdown(t(
            """
### Otimizador de Relíquias — Como usar

**1. Preencha o Inventário de Relíquias**
Na tabela, indique para cada relíquia:
- **Estrela**: nível de estrela atual (ex.: `Y★3`)
- **Perna**: progresso dentro da estrela (ex.: `2/5`)
- **Frag. específicos**: quantidade de fragmentos exclusivos dessa relíquia que você tem em estoque
- **Usar?**: marque as relíquias que devem entrar na otimização

**2. Configure os parâmetros (⚙️ Configuração)**
- **Modo**: *Set completo* — otimiza todas as relíquias de um conjunto; *Relíquia única* — custo para uma relíquia
- **Martelos Milagrosos**: quantidade disponível (cada martelo desenvolve uma relíquia 1 nível)
- **Fragmentos universais**: estoque de fragmentos que podem ser usados em qualquer relíquia
- **Relay 1 / Relay 2**: relíquias universais obrigatórias que servem de "ponte" para redistribuir fragmentos entre as relíquias do set

**3. Execute**
Clique em **🔍 Calcular rota** para ver a sequência ótima de upgrades.

**4. Interprete o resultado**
- A tabela de resultados mostra o estado antes → depois de cada relíquia
- As métricas mostram martelos e fragmentos usados e o saldo restante
- O resultado **ótimo** (sem restrições) é exibido em expander para comparação
""",
            """
### Relic Optimizer — How to use

**1. Fill the Relic Inventory**
For each relic in the table, set:
- **Star**: current star level (e.g. `Y★3`)
- **Leg**: progress within the star (e.g. `2/5`)
- **Spec. shards**: relic-specific shards you currently hold
- **Use?**: check the relics to include in the optimization

**2. Set parameters (⚙️ Configuration)**
- **Mode**: *Full set* — optimises all relics in a set; *Single relic* — cost for one relic
- **Miracle Hammers**: quantity available (each hammer advances a relic 1 level)
- **Universal shards**: shards that can be used on any relic
- **Relay 1 / Relay 2**: mandatory universal relics acting as "bridges" to redistribute shards

**3. Run**
Click **🔍 Calculate route** to see the optimal upgrade sequence.

**4. Read the result**
- The results table shows each relic's before → after state
- Metrics show hammers and shards used plus remaining balance
- The **optimal** result (without constraints) is shown in an expander for comparison
""",
        ))

    with _hi2:
        _rd1, _rd2 = st.columns(2)
        with _rd1:
            st.subheader(t("⭐ Sistema de Estrelas", "⭐ Star System"))
            st.markdown(t(
                """
| Tier | Prefixo | Índices |
|------|---------|---------|
| Amarelo | Y★ | 1 – 25 |
| Vermelho | R★ | 26 – 50 |
| Platinado | P★ | 51 – 75 |
| Preto | B★ | 76 – 100 |

Cada estrela tem **5 pernas**. A perna 5/5 fecha a estrela.
Fragmentos **específicos** valem apenas para aquela relíquia.
Fragmentos **universais** valem para qualquer relíquia.
""",
                """
| Tier | Prefix | Indices |
|------|--------|---------|
| Yellow | Y★ | 1 – 25 |
| Red | R★ | 26 – 50 |
| Platinum | P★ | 51 – 75 |
| Black | B★ | 76 – 100 |

Each star has **5 legs**. Leg 5/5 completes the star.
**Specific** shards are usable only on that relic.
**Universal** shards work on any relic.
""",
            ))
            st.subheader(t("🔁 Relíquias Universais (Relay)", "🔁 Universal Relics (Relay)"))
            for _ur in UNIVERSAL_RELICS:
                st.markdown(f"- {_rn(_ur)}")
        with _rd2:
            st.subheader(t("📦 Conjuntos", "📦 Sets"))
            _set_labels = {
                "League":  t("Liga",     "League"),
                "Horde":   t("Horda",    "Horde"),
                "Nature":  t("Natureza", "Nature"),
            }
            for _sk, _srelics in SETS.items():
                st.markdown(f"**{_set_labels[_sk]}**")
                for _sr in _srelics:
                    st.markdown(f"  - {_rn(_sr)}")

