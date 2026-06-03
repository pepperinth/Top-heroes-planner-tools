"""
events_tracker.py
=================
Streamlit UI module for the GameEvents Tracker.
Call render_events_tracker() from app.py or any page.
"""

import streamlit as st
from events_data import (
    EVENTS,
    calc_task_points,
    get_milestone_status,
)


# ══════════════════════════════════════════════════════════════════════════════
# STYLING
# ══════════════════════════════════════════════════════════════════════════════

def _inject_css():
    st.markdown("""
    <style>
    .ms-reached {
        background: #217346; color: white;
        border-radius: 6px; padding: 2px 10px;
        font-weight: bold; font-size: 0.85em;
    }
    .ms-pending {
        background: #f0f0f0; color: #cc0000;
        border-radius: 6px; padding: 2px 10px;
        font-size: 0.85em;
    }
    .pts-pill {
        background: #D46B08; color: white;
        border-radius: 12px; padding: 1px 10px;
        font-weight: bold; font-size: 0.9em;
        display: inline-block;
    }
    .calc-pill {
        background: #4A7C59; color: white;
        border-radius: 12px; padding: 1px 8px;
        font-size: 0.82em;
        display: inline-block;
    }
    .section-header {
        background: #5C3D1E; color: white;
        border-radius: 6px; padding: 6px 14px;
        font-weight: bold; margin-bottom: 4px;
    }
    .grand-total {
        background: #FF8C00; color: white;
        border-radius: 8px; padding: 10px 18px;
        font-size: 1.2em; font-weight: bold;
        text-align: center; margin: 8px 0;
    }
    .sim-total {
        background: #FFD700; color: #3B2A1A;
        border-radius: 8px; padding: 8px 18px;
        font-size: 1.1em; font-weight: bold;
        text-align: center; margin: 6px 0;
    }
    </style>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MILESTONE DISPLAY
# ══════════════════════════════════════════════════════════════════════════════

def _render_milestones(milestones: list, grand_total: float, t):
    statuses = get_milestone_status(milestones, grand_total)

    cols = st.columns([2, 2, 3])
    cols[0].markdown(f"**{t('Milestone', 'Milestone')}**")
    cols[1].markdown(f"**{t('Pts necessários', 'Pts needed')}**")
    cols[2].markdown(f"**{t('Status', 'Status')}**")

    for s in statuses:
        c0, c1, c2 = st.columns([2, 2, 3])
        c0.markdown(f"`{s['value']:,}`")
        if s["reached"]:
            c1.markdown("—")
            c2.markdown(
                f'<span class="ms-reached">✓ {t("Alcançado!", "Reached!")}</span>',
                unsafe_allow_html=True,
            )
        else:
            c1.markdown(f"`{s['needed']:,.0f}`")
            c2.markdown(
                f'<span class="ms-pending">{t("Faltam", "Need")} {s["needed"]:,.0f} pts</span>',
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# SINGLE EVENT TAB
# ══════════════════════════════════════════════════════════════════════════════

def _render_event_tab(ev: dict, t, lang: str = "pt"):
    # One-shot delivery from calculators: move pending pts into the widget key
    _delivery = f"_pts_to_send_{ev['sheet']}"
    if _delivery in st.session_state:
        st.session_state[f"cur_{ev['sheet']}"] = st.session_state[_delivery]
        del st.session_state[_delivery]

    current_pts = st.number_input(
        t("Pontos atuais que você já tem:", "Current points you already have:"),
        min_value=0, value=0, step=100,
        key=f"cur_{ev['sheet']}",
        help=t(
            "Insira os pontos que você já acumulou neste evento.",
            "Enter the points you already have accumulated for this event.",
        ),
    )

    info = ev.get("info_note_pt" if lang == "pt" else "info_note") or ev.get("info_note")
    if info:
        st.info(info)

    st.markdown("---")
    st.markdown(f"#### {t('Tarefas — insira as quantidades abaixo', 'Tasks — enter raw quantities below')}")

    _has_calc = st.session_state.get(f"_calc_sent_{ev['sheet']}", False)
    if _has_calc:
        st.info(t(
            "🔗 Pontos atuais pré-preenchidos pelas calculadoras. "
            "Use as tarefas para gastos adicionais não cobertos pelas ferramentas.",
            "🔗 Current points pre-filled by the calculators. "
            "Use the tasks for extra spending not covered by the tools.",
        ))

    simulated_total = 0.0

    for i, task in enumerate(ev["tasks"]):
        col_desc, col_pts, col_input, col_earned, col_calc = st.columns([4, 1, 2, 2, 2])

        with col_desc:
            desc = task.get("description_pt", task["description"]) if lang == "pt" else task["description"]
            st.markdown(f"**{desc}**")

        with col_pts:
            st.markdown(
                f'<span class="pts-pill">{task["pts_label"]}</span>',
                unsafe_allow_html=True,
            )

        with col_input:
            if task["is_speedup"]:
                d = st.number_input(t("Dias", "Days"), min_value=0, value=0, step=1,
                                    key=f"{ev['sheet']}_{i}_days", label_visibility="collapsed")
                h = st.number_input(t("Horas", "Hours"), min_value=0, max_value=23, value=0, step=1,
                                    key=f"{ev['sheet']}_{i}_hours", label_visibility="collapsed")
                m = st.number_input(t("Min", "Min"), min_value=0, max_value=59, value=0, step=1,
                                    key=f"{ev['sheet']}_{i}_min", label_visibility="collapsed")
                pts = calc_task_points(task, days=d, hours=h, minutes=m)
                st.caption(t("Dias / Horas / Min", "Days / Hours / Min"))
            else:
                qty = st.number_input(
                    t("Qtd", "Qty"), min_value=0, value=0, step=1,
                    key=f"{ev['sheet']}_{i}_qty",
                    label_visibility="collapsed",
                )
                pts = calc_task_points(task, quantity=qty)

        with col_earned:
            if pts > 0:
                st.success(f"**{pts:,.0f} pts**")
            else:
                st.markdown("—")

        with col_calc:
            _contrib = st.session_state.get(f"_calc_contrib_{ev['sheet']}_{i}", 0)
            if _contrib > 0:
                st.markdown(
                    f'<span class="calc-pill">🔗 {_contrib:,.0f}</span>',
                    unsafe_allow_html=True,
                )

        simulated_total += pts

    st.markdown("---")

    grand_total = current_pts + simulated_total

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            f'<div class="sim-total">{t("Simulado", "Simulated")}: {simulated_total:,.0f} pts</div>',
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            f'<div class="grand-total">{t("Total", "Grand Total")}: {grand_total:,.0f} pts</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown(f"#### {t('Milestones do Evento', 'Event Milestones')}")
    _render_milestones(ev["milestones"], grand_total, t)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def render_events_tracker():
    _inject_css()

    lang = st.session_state.get("lang", "pt")
    def t(pt, en): return pt if lang == "pt" else en

    st.title("📅 " + t("Eventos Regulares", "Rush Events"))
    st.markdown(t(
        "Acompanhe seus pontos, planeje tarefas e confira o progresso nos milestones de cada evento.",
        "Track your points, plan tasks and check milestone progress for each active event.",
    ))

    tab_labels = [ev.get("name_pt", ev["name"]) if lang == "pt" else ev["name"] for ev in EVENTS]
    tabs = st.tabs(tab_labels)

    for tab, ev in zip(tabs, EVENTS):
        with tab:
            ev_name = ev.get("name_pt", ev["name"]) if lang == "pt" else ev["name"]
            st.markdown(
                f'<div class="section-header">{ev_name}</div>',
                unsafe_allow_html=True,
            )
            _render_event_tab(ev, t, lang)


# ══════════════════════════════════════════════════════════════════════════════
# STANDALONE RUN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    st.set_page_config(page_title="Game Events Tracker", page_icon="📅", layout="wide")
    render_events_tracker()
