"""
app.py — Top Heroes Tools: home page and global layout.
Run with:  streamlit run app.py
"""

import streamlit as st
from events_tracker import render_events_tracker

st.set_page_config(
    page_title="Top Heroes Tools",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global language selector ───────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "pt"

with st.sidebar:
    st.markdown("### 🌐 Idioma / Language")
    lang_pick = st.radio(
        "", ["🇧🇷 Português", "🇬🇧 English"],
        index=0 if st.session_state.lang == "pt" else 1,
        horizontal=True, label_visibility="collapsed",
    )
    st.session_state.lang = "pt" if "Português" in lang_pick else "en"
    st.divider()
    st.markdown("**Top Heroes Tools**")
    st.caption("s108+")
    st.divider()
    st.warning(
        "⚠️ **Versão Beta**\nAlgumas funcionalidades podem estar incompletas ou mudar."
        if st.session_state.lang == "pt" else
        "⚠️ **Beta Version**\nSome features may be incomplete or subject to change."
    )
    st.divider()
    if st.button(
        "🗑️ Limpar tudo" if st.session_state.lang == "pt" else "🗑️ Clear all",
        use_container_width=True,
        help=("Zera todos os dados inseridos e reinicia a página."
              if st.session_state.lang == "pt" else
              "Resets all entered data and restarts the page."),
    ):
        _lang = st.session_state.lang
        st.session_state.clear()
        st.session_state.lang = _lang
        st.rerun()

lang = st.session_state.lang
def t(pt, en): return pt if lang == "pt" else en

# ── Title ──────────────────────────────────────────────────────────────────────
st.title("🏆 Top Heroes" + t(" — Ferramentas", " — Tools"))

# ── Main tabs ──────────────────────────────────────────────────────────────────
tab_tools, tab_events = st.tabs([
    "🔧 " + t("Ferramentas", "Tools"),
    "📅 " + t("Eventos Regulares", "Rush Events"),
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Ferramentas / Tools
# ══════════════════════════════════════════════════════════════════════════════
with tab_tools:
    st.markdown(
        "Escolha uma ferramenta abaixo ou na barra lateral." if lang == "pt"
        else "Choose a tool below or from the sidebar."
    )

    col1, col2, col3 = st.columns(3, gap="large")
    col4, col5, col6 = st.columns(3, gap="large")
    col7, col8, col9 = st.columns(3, gap="large")

    with col1:
        with st.container(border=True):
            st.subheader("⚜️ " + t("Otimizador de Relíquias", "Relic Optimizer"))
            st.markdown(
                "Calcula a rota ideal de **Miracle Hammer** para maximizar os níveis das relíquias com os fragmentos disponíveis."
                if lang == "pt" else
                "Calculates the optimal **Miracle Hammer** route to maximise relic levels with available shards."
            )
            st.page_link("pages/1_Reliquias.py",
                         label="Abrir →" if lang == "pt" else "Open →")

    with col2:
        with st.container(border=True):
            st.subheader("🏗️ " + t("Planejador DE & Pó", "DE & Dust Planner"))
            st.markdown(
                "Planeja gastos de **Dragon Essence** e **Dragon Dust** nas construções Brilliance e pesquisas, com cadeia de pré-requisitos do Castelo."
                if lang == "pt" else
                "Plans **Dragon Essence** and **Dragon Dust** spending on Brilliance buildings and research, with Castle prerequisite chain."
            )
            st.page_link("pages/2_DE_Dust.py",
                         label="Abrir →" if lang == "pt" else "Open →")

    with col3:
        with st.container(border=True):
            st.subheader("🐾 " + t("Calculadora de Pets", "Pet Calculator"))
            st.markdown(
                "Calcula **comida, essência e cópias** necessárias para evoluir e promover seus pets até Epic, Legendary e Mythic."
                if lang == "pt" else
                "Calculates **food, essence and copies** needed to level up and promote pets to Epic, Legendary, and Mythic."
            )
            st.page_link("pages/3_Pets.py",
                         label="Abrir →" if lang == "pt" else "Open →")

    with col4:
        with st.container(border=True):
            st.subheader("🧢 " + t("Skins de Tropas", "Troop Skins"))
            st.markdown(
                "Calcula **medalhas e tokens** necessários para subir o nível e as Honor Levels das skins de tropas."
                if lang == "pt" else
                "Calculates **medals and tokens** needed to level up troop skins and unlock Honor Levels."
            )
            st.page_link("pages/4_Troop_Skins.py",
                         label="Abrir →" if lang == "pt" else "Open →")

    with col5:
        with st.container(border=True):
            st.subheader("👤 " + t("Calculadora de Heróis", "Hero Calculator"))
            st.markdown(
                "Calcula **fragmentos, livros de habilidade, soul stones, UW, espírito heroico e atributos** para evoluir seus heróis. Planejador de filas Q1–Q5."
                if lang == "pt" else
                "Calculates **shards, skill books, soul stones, UW, heroic spirit and traits** to upgrade your heroes. Q1–Q5 queue planner."
            )
            st.page_link("pages/5_Herois.py",
                         label="Abrir →" if lang == "pt" else "Open →")

    with col6:
        with st.container(border=True):
            st.subheader("🦕 " + t("Behemoth", "Behemoth"))
            st.markdown(
                "Calcula **Magicite, Núcleos Mágicos e Selos** necessários para evoluir os níveis e estrelas do Behemoth."
                if lang == "pt" else
                "Calculates **Magicite, Magic Cores and Seals** needed to upgrade Behemoth levels and stars."
            )
            st.page_link("pages/6_Behemoth.py",
                         label="Abrir →" if lang == "pt" else "Open →")

    with col7:
        with st.container(border=True):
            st.subheader("⚙️ " + t("Lord Gear & Sacred Codex", "Lord Gear & Sacred Codex"))
            st.markdown(
                "Calcula **Metal Refinado, Fio Mágico, Oricalco e Sangue de Dragão** para evoluir peças do Lord Gear e o Sacred Codex."
                if lang == "pt" else
                "Calculates **Refined Metal, Magic Thread, Orichalcum and Dragon Blood** to upgrade Lord Gear pieces and the Sacred Codex."
            )
            st.page_link("pages/7_LordGear.py",
                         label="Abrir →" if lang == "pt" else "Open →")

    st.divider()
    st.caption(
        "🛈 Esta ferramenta não tem filiação com a River Game HK Limited."
        if lang == "pt" else
        "🛈 This tool has no affiliation with River Game HK Limited."
    )

    st.subheader("🙏 " + t("Agradecimentos", "Acknowledgements"))
    st.markdown(
        """
Todas as informações foram retiradas do **Discord oficial do Top Heroes**.

**Kami** — pela ajuda desde o início

**Maaarcy** — pela ideia de integrar as calculadoras com os eventos regulares

**Top Heroes Table** — Hyena & **Mazdie**

**Dragon Essence Brilliance Building Cost**
Planilha criada por **Mixtape** & **Barad**.
Mixtape, RegVed, PG Brotha, Cookie, Shootz, Maaarcy, Nomlette, Convex, Huddy, Mystiic — pelo excelente trabalho feito na moderação e coleta de dados.
"""
        if lang == "pt" else
        """
All information was sourced from the **official Top Heroes Discord**.

**Kami** — for the help since the beginning

**Maaarcy** — for the idea of integrating the calculators with the regular events

**Top Heroes Table** — Hyena & **Mazdie**

**Dragon Essence Brilliance Building Cost**
Spreadsheet created by **Mixtape** & **Barad**.
Mixtape, RegVed, PG Brotha, Cookie, Shootz, Maaarcy, Nomlette, Convex, Huddy, Mystiic — for the excellent work in moderation and data collection.
"""
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Eventos Regulares / Rush Events
# ══════════════════════════════════════════════════════════════════════════════
with tab_events:
    render_events_tracker()
