"""
ui_utils.py — Shared visual utilities for Top Heroes Tools.
"""

import streamlit as st

# ── Palette ───────────────────────────────────────────────────────────────────
FACTION_COLORS = {
    "Liga":     "#4A90D9",
    "Horda":    "#CC3333",
    "Natureza": "#33A04A",
}
TIER_COLORS = {
    "Mythic":     "#CC3333",
    "Legendary":  "#C8A400",
    "Epic":       "#8B44CC",
    "Rare":       "#3498DB",
    "Common":     "#7F8C8D",
}
RARITY_COLORS = {
    "Lendária":  "#C8A400",
    "Épica":     "#8B44CC",
    "Rara":      "#3498DB",
    "Legendary": "#C8A400",
    "Epic":      "#8B44CC",
    "Rare":      "#3498DB",
}

_GLOBAL_CSS = """
<style>
/* ── Metric cards ─────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #f7f8fa;
    border-radius: 10px;
    padding: 12px 16px !important;
    border: 1px solid #e4e6ea;
}
[data-testid="stMetricValue"] {
    font-size: 1.3em !important;
    font-weight: 700 !important;
}

/* ── Expander ─────────────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid #e4e6ea;
    border-radius: 10px;
    overflow: hidden;
}
[data-testid="stExpander"] > details > summary {
    font-weight: 600;
    padding: 8px 14px;
}

/* ── Dataframe ────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #e4e6ea;
}

/* ── Buttons ──────────────────────────────────────────────── */
[data-testid="stButton"] > button {
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.15s;
}
[data-testid="stButton"] > button[kind="primary"] {
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
}

/* ── Tabs ─────────────────────────────────────────────────── */
[data-testid="stTabs"] [role="tablist"] {
    gap: 4px;
}

/* ── Section header class ─────────────────────────────────── */
.th-section {
    border-radius: 0 8px 8px 0;
    padding: 6px 16px;
    margin: 14px 0 8px 0;
    font-weight: 700;
    font-size: 1.0em;
    color: white;
}

/* ── Tier / faction badge ─────────────────────────────────── */
.th-badge {
    display: inline-block;
    border-radius: 6px;
    padding: 2px 10px;
    font-weight: 700;
    font-size: 0.82em;
    color: white;
    margin-right: 6px;
}

/* ── Info banner ──────────────────────────────────────────── */
.th-banner {
    border-radius: 0 10px 10px 0;
    padding: 8px 16px;
    margin: 8px 0 12px 0;
}

/* ── Milestone pills ──────────────────────────────────────── */
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
    font-size: 0.82em; display: inline-block;
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
"""


def inject_global_css():
    """Inject global CSS — call once per page, after set_page_config."""
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)


def section_header(label: str, color: str = "#5C3D1E", icon: str = ""):
    """Colored full-width section header bar."""
    st.markdown(
        f'<div class="th-section" style="background:{color};">'
        f'{"" if not icon else icon + " "}{label}</div>',
        unsafe_allow_html=True,
    )


def faction_banner(label: str, faction: str, extra: str = ""):
    """Faction-colored left-border banner."""
    c = FACTION_COLORS.get(faction, "#888")
    st.markdown(
        f'<div class="th-banner" style="border-left:5px solid {c}; background:{c}18;">'
        f'<b>{label}</b>'
        f'{(" — " + extra) if extra else ""}'
        f'</div>',
        unsafe_allow_html=True,
    )


def tier_badge(tier: str, label: str = "") -> str:
    """Return HTML for a colored tier badge."""
    c = TIER_COLORS.get(tier, "#888")
    txt = label or tier
    return f'<span class="th-badge" style="background:{c};">{txt}</span>'


def rarity_badge(rarity: str, label: str = "") -> str:
    """Return HTML for a colored rarity badge."""
    c = RARITY_COLORS.get(rarity, "#888")
    txt = label or rarity
    return f'<span class="th-badge" style="background:{c};">{txt}</span>'


def results_header(label: str, faction: str = ""):
    """Faction-colored results section header."""
    c = FACTION_COLORS.get(faction, "#5C3D1E")
    st.markdown(
        f'<div style="border-left:5px solid {c}; padding:5px 14px; '
        f'border-radius:0 8px 8px 0; background:{c}14; '
        f'font-weight:700; margin:12px 0 8px;">{label}</div>',
        unsafe_allow_html=True,
    )
