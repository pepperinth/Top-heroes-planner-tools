"""
app.py — Top Heroes Tools: home page and global layout.
Run with:  streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Top Heroes Tools",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global language selector (persists across pages via session_state) ─────────
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

# ── Home ───────────────────────────────────────────────────────────────────────
st.title("🏆 Top Heroes" + (" — Ferramentas" if lang == "pt" else " — Tools"))
st.markdown(
    "Escolha uma ferramenta abaixo ou na barra lateral." if lang == "pt"
    else "Choose a tool below or from the sidebar."
)
st.divider()

col1, col2 = st.columns(2, gap="large")

with col1:
    with st.container(border=True):
        st.subheader("⚜️ " + ("Otimizador de Relíquias" if lang == "pt" else "Relic Optimizer"))
        st.markdown(
            "Calcula a rota ideal de **Miracle Hammer** para maximizar os níveis das relíquias com os fragmentos disponíveis."
            if lang == "pt" else
            "Calculates the optimal **Miracle Hammer** route to maximise relic levels with available shards."
        )
        st.page_link("pages/1_Reliquias.py",
                     label="Abrir →" if lang == "pt" else "Open →")

with col2:
    with st.container(border=True):
        st.subheader("🏗️ " + ("Planejador DE & Pó" if lang == "pt" else "DE & Dust Planner"))
        st.markdown(
            "Planeja gastos de **Dragon Essence** e **Dragon Dust** nas construções Brilliance e pesquisas, com cadeia de pré-requisitos do Castelo."
            if lang == "pt" else
            "Plans **Dragon Essence** and **Dragon Dust** spending on Brilliance buildings and research, with Castle prerequisite chain."
        )
        st.page_link("pages/2_DE_Dust.py",
                     label="Abrir →" if lang == "pt" else "Open →")

st.divider()
st.subheader("🙏 " + ("Agradecimentos" if lang == "pt" else "Acknowledgements"))
st.markdown(
    """
Todas as informações foram retiradas do **Discord oficial do Top Heroes**.

**Top Heroes Table** — Hyena

**Dragon Essence Brilliance Building Cost**
Planilha criada por **Mixtape** & **Barad**.
Dados fornecidos por: Mixtape, RegVed, PG Brotha, Cookie, Shootz, Maaarcy, Nomlette, Convex, Huddy, Mystiic.
"""
    if lang == "pt" else
    """
All information was sourced from the **official Top Heroes Discord**.

**Top Heroes Table** — Hyena

**Dragon Essence Brilliance Building Cost**
Spreadsheet created by **Mixtape** & **Barad**.
Data provided by: Mixtape, RegVed, PG Brotha, Cookie, Shootz, Maaarcy, Nomlette, Convex, Huddy, Mystiic.
"""
)
