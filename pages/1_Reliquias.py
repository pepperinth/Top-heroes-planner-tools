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
    STAR_OPTIONS, PREFERRED_INTER, RELIC_NAME_PT, RELIC_IMAGES,
    EPIC_RELICS, RARE_RELICS, STAR_OPTIONS_RARE, RARE_MAX_LEVEL,
    star_leg_to_idx, idx_to_star_leg,
    compute_route, shards_needed, epic_shards_needed, rare_shards_needed,
)
from events_data import EVENTS, get_milestone_status
from ui_utils import inject_global_css, section_header, results_header
import persistence

st.set_page_config(page_title="Relíquias", page_icon="⚜️", layout="wide")

# ── Test preset ────────────────────────────────────────────────────────────────
# Inventário atual: Asas P★4 1/5 (17sp), Perseguição usada. 3 martelos, 464u.
# Estratégia ótima: 1h Amuleto (Asas→Amuleto direto) + 2h Coração boomerang
# via Bandeira de Guerra → Amuleto P★5 5/5, Coração P★5 1/5.
_PRESET_RELICS = {
    "Duke's Signet Ring": ("Y★5", "5/5", 0,   True),
    "Eternal Wings":      ("P★4", "1/5", 17,  True),
    "Frost Diadem":       ("Y★4", "3/5", 69,  True),
    "Royalty":            ("Y★5", "3/5", 76,  True),
    "War Flag":           ("Y★5", "5/5", 113, True),
    "Scale of Injustice": ("R★2", "3/5", 0,   True),
    "Mighty Gold":        ("0★",  "1/5", 0,   True),
    "Persecution":        ("0★",  "1/5", 0,   False),
    "Thunder Judgment":   ("P★5", "5/5", 0,   True),
    "Dragonheart":        ("P★1", "2/5", 0,   True),
    "Dragonbone Amulet":  ("0★",  "1/5", 117, True),
}

def _load_preset_callback():
    _lang = st.session_state.get("lang", "pt")
    _pt   = _lang == "pt"
    for r in ALL_RELICS:
        star, leg, spec, use = _PRESET_RELICS.get(r, ("0★", "1/5", 0, True))
        st.session_state[f"istar_{r}"] = star
        st.session_state[f"ileg_{r}"]  = leg
        st.session_state[f"ispec_{r}"] = spec
        st.session_state[f"iu_{r}"]    = use
    _set_map = {"League": "Liga", "Horde": "Horda", "Nature": "Natureza"}
    st.session_state["cfg_target_set"] = _set_map["Horde"] if _pt else "Horde"
    st.session_state["cfg_tgt_star"]   = "P★5"
    st.session_state["cfg_tgt_leg"]    = "5/5"
    st.session_state["cfg_hammers"]    = 3
    st.session_state["cfg_univ"]       = 464
    _rn_cb = lambda r: RELIC_NAME_PT.get(r, r) if _pt else r
    st.session_state["cfg_inter1"] = _rn_cb("Eternal Wings")
    st.session_state["cfg_inter2"] = ""
    _prio_en = ["Dragonbone Amulet", "Dragonheart"]
    for i, r in enumerate(_prio_en):
        st.session_state[f"prio_{i}"] = _rn_cb(r)
    if len(_prio_en) < 3:
        st.session_state["prio_2"] = ""
    st.session_state["relic_mode"] = "Set completo" if _pt else "Full set"

# ── Persistence ────────────────────────────────────────────────────────────────
_cm = persistence.new_manager("relics")

_LEG_OPTIONS_ALL = ["1/5", "2/5", "3/5", "4/5", "5/5"]

def _to_star_leg(idx: int):
    if idx <= 0:
        return "0★", "1/5"
    if idx > 75:
        return f"B★{idx - 75}", "1/5"
    off = idx - 1
    return f"{'YRP'[off // 25]}★{off % 25 // 5 + 1}", f"{off % 25 % 5 + 1}/5"

if "rel_initialized" not in st.session_state:
    _saved = persistence.load(_cm, "th_relics")
    if _saved:
        if "inv_v3" in _saved:
            for _r in ALL_RELICS:
                _rd = _saved["inv_v3"].get(_r, {})
                _s, _l = _to_star_leg(int(_rd.get("star_idx", 0) or 0))
                st.session_state[f"istar_{_r}"] = _s
                st.session_state[f"ileg_{_r}"]  = _l
                st.session_state[f"ispec_{_r}"] = int(_rd.get("spec", 0) or 0)
                st.session_state[f"iu_{_r}"]    = bool(_rd.get("use",  True))
        elif "inv_v2" in _saved:
            for _r in ALL_RELICS:
                _rd = _saved["inv_v2"].get(_r, {})
                _s = _rd.get("star", "0★") if _rd.get("star", "0★") in STAR_OPTIONS else "0★"
                _l = _rd.get("leg",  "1/5") if _rd.get("leg", "—") in _LEG_OPTIONS_ALL else "1/5"
                st.session_state[f"istar_{_r}"] = _s
                st.session_state[f"ileg_{_r}"]  = _l
                st.session_state[f"ispec_{_r}"] = int(_rd.get("spec", 0) or 0)
                st.session_state[f"iu_{_r}"]    = bool(_rd.get("use",  True))
        elif "inv_table" in _saved:
            _edited_rows = _saved["inv_table"].get("edited_rows", {})
            from relic_optimizer import star_leg_to_idx as _stl
            for _i, _r in enumerate(ALL_RELICS):
                _rd   = _edited_rows.get(str(_i), {})
                _star = _rd.get("Star") or _rd.get("Estrela", "0★")
                _leg  = _rd.get("Leg")  or _rd.get("Perna",  "1/5")
                if _leg == "—": _leg = "1/5"
                _spec = _rd.get("Spec. shards") or _rd.get("Frag. específicos", 0)
                _use  = _rd.get("Use?") if "Use?" in _rd else _rd.get("Usar?", True)
                _s, _l = _to_star_leg(_stl(_star if _star in STAR_OPTIONS else "0★", _leg))
                st.session_state[f"istar_{_r}"] = _s
                st.session_state[f"ileg_{_r}"]  = _l
                st.session_state[f"ispec_{_r}"] = int(_spec) if _spec else 0
                st.session_state[f"iu_{_r}"]    = bool(_use) if _use is not None else True
    st.session_state["rel_initialized"] = True

if "rel_epic_initialized" not in st.session_state:
    _saved_e = persistence.load(_cm, "th_epics")
    if _saved_e and "inv_epic_v1" in _saved_e:
        st.session_state["epic_univ_shards"] = int(_saved_e["inv_epic_v1"].get("_univ", 0) or 0)
        for _r in EPIC_RELICS:
            _rd = _saved_e["inv_epic_v1"].get(_r, {})
            st.session_state[f"espec_{_r}"] = int(_rd.get("spec", 0) or 0)
    st.session_state["rel_epic_initialized"] = True

if "rel_rare_initialized" not in st.session_state:
    _saved_r = persistence.load(_cm, "th_rares")
    if _saved_r and "inv_rare_v1" in _saved_r:
        st.session_state["rare_univ_shards"] = int(_saved_r["inv_rare_v1"].get("_univ", 0) or 0)
        for _r in RARE_RELICS:
            _rd = _saved_r["inv_rare_v1"].get(_r, {})
            st.session_state[f"rspec_{_r}"] = int(_rd.get("spec", 0) or 0)
    st.session_state["rel_rare_initialized"] = True

if "epic_plan" not in st.session_state:
    st.session_state["epic_plan"] = []
if "rare_plan" not in st.session_state:
    st.session_state["rare_plan"] = []
if "epic_univ_shards" not in st.session_state:
    st.session_state["epic_univ_shards"] = 0
if "rare_univ_shards" not in st.session_state:
    st.session_state["rare_univ_shards"] = 0
for _k, _v in [("cfg_hammers", 1), ("cfg_univ", 0)]:
    if _k not in st.session_state:
        st.session_state[_k] = _v


def _inv_save_all():
    _inv_v3 = {}
    for _r in ALL_RELICS:
        _star = st.session_state.get(f"istar_{_r}", "0★") or "0★"
        _leg  = st.session_state.get(f"ileg_{_r}",  "1/5") or "1/5"
        _inv_v3[_r] = {
            "star_idx": _relic_star_idx(_star, _leg),
            "spec":     int(st.session_state.get(f"ispec_{_r}", 0) or 0),
            "use":      bool(st.session_state.get(f"iu_{_r}", True)),
        }
    st.session_state["inv_v3"] = _inv_v3
    persistence.save(_cm, "th_relics", {"inv_v3": _inv_v3})


def _epic_save_all():
    _inv = {"_univ": int(st.session_state.get("epic_univ_shards", 0) or 0)}
    for _r in EPIC_RELICS:
        _inv[_r] = {"spec": int(st.session_state.get(f"espec_{_r}", 0) or 0)}
    persistence.save(_cm, "th_epics", {"inv_epic_v1": _inv})


def _rare_save_all():
    _inv = {"_univ": int(st.session_state.get("rare_univ_shards", 0) or 0)}
    for _r in RARE_RELICS:
        _inv[_r] = {"spec": int(st.session_state.get(f"rspec_{_r}", 0) or 0)}
    persistence.save(_cm, "th_rares", {"inv_rare_v1": _inv})


# ── Language ───────────────────────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "en"

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
    _btn_lbl = ("Carregar preset de teste"
                if st.session_state.get("lang", "pt") == "pt"
                else "Load test preset")
    st.button(
        "🧪 " + _btn_lbl,
        key="btn_preset", on_click=_load_preset_callback,
        use_container_width=True,
    )
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

_RELIC_IMG_DIR = os.path.join(_BASE, "relic_imgs")

@st.cache_data
def _load_portrait(relic_en: str):
    fn = RELIC_IMAGES.get(relic_en)
    if not fn:
        return None
    p = os.path.join(_RELIC_IMG_DIR, fn)
    if not os.path.exists(p):
        return None
    from PIL import Image
    return Image.open(p).resize((44, 44), Image.LANCZOS)

@st.cache_data
def _star_img_for_idx(idx: int, base_dir: str):
    """Return (PIL image, display width) for a star index, cached."""
    from PIL import Image as _PIL
    path = os.path.join(base_dir, "behemoth_imgs", STAR_IMAGES[max(0, min(idx, len(STAR_IMAGES) - 1))])
    img  = _PIL.open(path)
    h    = 40
    w    = max(1, int(img.width * h / img.height))
    return img.resize((w, h), _PIL.LANCZOS), w

_STAR_TIER_OPTS = (
    ["0★"] +
    [f"Y★{n}" for n in range(1, 6)] +
    [f"R★{n}" for n in range(1, 6)] +
    [f"P★{n}" for n in range(1, 6)] +
    [f"B★{n}" for n in range(1, 6)]
)

_STAR_TIER_OPTS_RARE = (
    ["0★"] +
    [f"Y★{n}" for n in range(1, 6)] +
    [f"R★{n}" for n in range(1, 6)] +
    [f"P★{n}" for n in range(1, 6)] +
    ["B★1", "B★2", "B★3"]
)

# ── Header ─────────────────────────────────────────────────────────────────────
inject_global_css()
st.title("⚜️ " + t("Relíquias", "Relics"))
st.caption(t("Gerencie seu inventário e calcule rotas de upgrade para todas as relíquias.",
             "Manage your inventory and calculate upgrade routes for all relics."))

LEG_OPTIONS = ["1/5", "2/5", "3/5", "4/5", "5/5"]

_star_fmt = {
    "0★": t("— Sem relíquia", "— No relic"),
    **{f"Y★{n}": f"{t('Amarelo','Yellow')} ★{n}" for n in range(1, 6)},
    **{f"R★{n}": f"{t('Vermelho','Red')} ★{n}" for n in range(1, 6)},
    **{f"P★{n}": f"{t('Platinado','Platinum')} ★{n}" for n in range(1, 6)},
    **{f"B★{n}": f"{t('Preto','Black')} ★{n}" for n in range(1, 6)},
}

tab_leg, tab_epic, tab_rare, tab_help = st.tabs([
    "⚜️ " + t("Lendárias", "Legendary"),
    "🔮 " + t("Épicas", "Epic"),
    "💎 " + t("Raras", "Rare"),
    "📖 " + t("Instruções & Referência", "Instructions & Reference"),
])

with tab_leg:

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
                _set_disp = st.selectbox(t("Conjunto alvo", "Target set"), _set_opts, index=0, key="cfg_target_set")
                target_set = {"Liga": "League", "Horda": "Horde", "Natureza": "Nature", "League": "League", "Horde": "Horde", "Nature": "Nature"}.get(_set_disp, _set_disp)
                _set_img_cols = st.columns(3)
                for _si, _sr in enumerate(SETS[target_set]):
                    _p = _load_portrait(_sr)
                    if _p:
                        with _set_img_cols[_si]: st.image(_p, width=28)
            with c2:
                tgt_star = st.selectbox(t("Estrela alvo", "Target star"), STAR_OPTIONS[1:], index=0,
                                        format_func=lambda x: _star_fmt.get(x, x), key="cfg_tgt_star")
                tgt_leg  = st.selectbox(t("Perna alvo", "Target leg"), LEG_OPTIONS, index=0, key="cfg_tgt_leg")
                _show_relic_star(tgt_star, tgt_leg)
            with c3:
                hammers  = st.number_input(t("Martelos Milagrosos", "Miracle Hammers"), min_value=1, max_value=30, key="cfg_hammers")
                univ     = st.number_input(t("Fragmentos universais", "Universal shards"), min_value=0, step=10, key="cfg_univ")
            with c4:
                _univ_disp = [_rn(r) for r in UNIVERSAL_RELICS]
                inter1_d = st.selectbox(t("Relay 1 (obrigatório)", "Relay 1 (mandatory)"), _univ_disp, index=0, key="cfg_inter1")
                inter2_d = st.selectbox(t("Relay 2 (obrigatório)", "Relay 2 (mandatory)"), ["—"] + _univ_disp, index=0, key="cfg_inter2")
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
                _portrait_cfg = _load_portrait(single_relic)
                if _portrait_cfg:
                    st.image(_portrait_cfg, width=28)
            with s2:
                tgt_star = st.selectbox(t("Estrela alvo", "Target star"), STAR_OPTIONS[1:], index=0, key="sr_tgt_star",
                                        format_func=lambda x: _star_fmt.get(x, x))
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

    # ── Inventory (card layout with portraits) ─────────────────────────────────
    st.markdown("---")
    st.subheader(t("📦 Inventário de Relíquias", "📦 Relic Inventory"))
    st.caption(t(
        "Preencha os dados das relíquias. Universais com 0 frags. específicos são ignoradas como relay.",
        "Fill in your relic data. Universal relics with 0 specific shards are skipped as relays.",
    ))

    @st.fragment
    def _inventory_section():
        _INV_GROUPS = [
            (t("🔮 Universais", "🔮 Universals"), UNIVERSAL_RELICS),
            (t("⚔️ Set: Liga",    "⚔️ Set: League"), SETS["League"]),
            (t("🐉 Set: Horda",   "🐉 Set: Horde"),  SETS["Horde"]),
            (t("🌿 Set: Natureza", "🌿 Set: Nature"), SETS["Nature"]),
        ]
        _LEG_OPTS = ["1/5", "2/5", "3/5", "4/5", "5/5"]

        _hc1, _hc2 = st.columns([4, 7])
        _hc1.caption(t("Relíquia", "Relic"))
        _hc2.caption(t("Nível  ·  Frags. específicos  ·  Usar?", "Level  ·  Spec. shards  ·  Use?"))

        for _grp_name, _grp_relics in _INV_GROUPS:
            st.markdown(f"**{_grp_name}**")
            for _relic in _grp_relics:
                _portrait = _load_portrait(_relic)
                _c1, _c2 = st.columns([4, 7])
                with _c1:
                    _cp, _cn = st.columns([1, 3])
                    with _cp:
                        if _portrait is not None:
                            st.image(_portrait, width=44)
                        else:
                            st.markdown("⚜️")
                    with _cn:
                        st.markdown(f"**{_rn(_relic)}**")
                        _rtype = t("Universal", "Universal") if _relic in UNIVERSAL_RELICS else t("Set", "Set")
                        st.caption(_rtype)
                with _c2:
                    _cur_star = st.session_state.get(f"istar_{_relic}", "0★") or "0★"
                    _cur_leg  = st.session_state.get(f"ileg_{_relic}",  "1/5") or "1/5"
                    _cur_idx  = _relic_star_idx(_cur_star, _cur_leg)
                    _si_img, _si_w = _star_img_for_idx(_cur_idx, _BASE)
                    _cs, _cl = st.columns([5, 3])
                    with _cs:
                        st.selectbox(
                            "Star", _STAR_TIER_OPTS,
                            format_func=lambda x: _star_fmt.get(x, x),
                            key=f"istar_{_relic}",
                            on_change=_inv_save_all,
                            label_visibility="collapsed",
                        )
                    with _cl:
                        _leg_disabled = _cur_star == "0★" or _cur_star.startswith("B")
                        st.selectbox(
                            "Leg", _LEG_OPTS,
                            key=f"ileg_{_relic}",
                            on_change=_inv_save_all,
                            label_visibility="collapsed",
                            disabled=_leg_disabled,
                        )
                    _ci, _cf, _cu = st.columns([2, 4, 2])
                    with _ci:
                        st.image(_si_img, width=_si_w)
                    with _cf:
                        st.number_input(
                            t("Frags. específicos", "Spec. shards"), min_value=0,
                            key=f"ispec_{_relic}",
                            on_change=_inv_save_all,
                        )
                    with _cu:
                        st.checkbox(
                            t("Usar?", "Use?"),
                            key=f"iu_{_relic}",
                            on_change=_inv_save_all,
                        )
            st.divider()

    _inventory_section()

    # ── Run ────────────────────────────────────────────────────────────────────────
    st.markdown("---")
    if st.button(f"🔍 {t('Calcular rota', 'Calculate route')}", type="primary", use_container_width=True):
        # Build inv dict from per-relic session state
        relics_dict = {}
        for _rr in ALL_RELICS:
            _star    = st.session_state.get(f"istar_{_rr}", "0★") or "0★"
            _leg     = st.session_state.get(f"ileg_{_rr}",  "1/5") or "1/5"
            _spec_v  = int(st.session_state.get(f"ispec_{_rr}", 0) or 0)
            _can_use = bool(st.session_state.get(f"iu_{_rr}", True))
            relics_dict[_rr] = {
                "star_idx":        _relic_star_idx(_star, _leg),
                "specific_shards": _spec_v,
                "can_use":         _can_use,
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
                _opt_is_sub = opt.get("_is_sub", False)
                if _opt_is_sub:
                    _exp_label = t("🏆 Resultado ótimo (sem relays obrigatórios, mesma priorização)",
                                   "🏆 Optimal result (no mandatory relays, same priority)")
                else:
                    _exp_label = t("📊 Referência sem relays obrigatórios (mesma priorização)",
                                   "📊 Reference: no mandatory relays, same priority")
                with st.expander(_exp_label):
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

with tab_epic:
    st.caption(t(
        "Registre seus fragmentos épicos e calcule o custo de upgrades.",
        "Record your epic shards and calculate upgrade costs.",
    ))

    @st.fragment
    def _epic_inventory_section():
        _uh, _ui = st.columns([5, 6])
        with _uh:
            st.markdown(f"**{t('Frags. universais épicos', 'Epic universal shards')}**")
            st.caption(t("Usáveis em qualquer relíquia épica", "Usable on any epic relic"))
        with _ui:
            st.number_input(
                "univ_e", min_value=0,
                key="epic_univ_shards",
                on_change=_epic_save_all,
                label_visibility="collapsed",
            )
        st.divider()
        _hc1, _hc2 = st.columns([4, 7])
        _hc1.caption(t("Relíquia", "Relic"))
        _hc2.caption(t("Frags. específicos", "Spec. shards"))
        for _relic in EPIC_RELICS:
            _portrait = _load_portrait(_relic)
            _c1, _c2 = st.columns([4, 7])
            with _c1:
                _cp, _cn = st.columns([1, 3])
                with _cp:
                    if _portrait is not None:
                        st.image(_portrait, width=44)
                    else:
                        st.markdown("🔮")
                with _cn:
                    st.markdown(f"**{_rn(_relic)}**")
            with _c2:
                st.number_input(
                    "spec", min_value=0,
                    key=f"espec_{_relic}",
                    on_change=_epic_save_all,
                    label_visibility="collapsed",
                )
        st.divider()

    st.subheader(t("📦 Inventário — Épicas", "📦 Inventory — Epic"))
    _epic_inventory_section()

    st.markdown("---")
    st.subheader(t("🧮 Calculadora Individual", "🧮 Individual Calculator"))
    _ec1, _ec2, _ec3 = st.columns(3)
    with _ec1:
        _ecalc_disp = [_rn(r) for r in EPIC_RELICS]
        _ecalc_d    = st.selectbox(t("Relíquia", "Relic"), _ecalc_disp, key="ecalc_relic")
        _ecalc_r    = EPIC_RELICS[_ecalc_disp.index(_ecalc_d)]
        _ep = _load_portrait(_ecalc_r)
        if _ep:
            st.image(_ep, width=44)
    with _ec2:
        _ec_star = st.selectbox(
            t("Nível atual", "Current level"), _STAR_TIER_OPTS,
            format_func=lambda x: _star_fmt.get(x, x),
            key="ecalc_cur_star",
        )
        _ec_leg = st.selectbox(
            t("Perna atual", "Current leg"), LEG_OPTIONS,
            key="ecalc_cur_leg", disabled=(_ec_star == "0★"),
        )
        _ec_cur = star_leg_to_idx(_ec_star, _ec_leg)
        _ec_tgt_star = st.selectbox(
            t("Estrela alvo", "Target star"), _STAR_TIER_OPTS[1:], key="ecalc_tgt_star",
            format_func=lambda x: _star_fmt.get(x, x),
        )
        _ec_tgt_leg = st.selectbox(t("Perna alvo", "Target leg"), LEG_OPTIONS, key="ecalc_tgt_leg")
    with _ec3:
        _ec_tgt     = star_leg_to_idx(_ec_tgt_star, _ec_tgt_leg)
        _ec_spec    = int(st.session_state.get(f"espec_{_ecalc_r}", 0) or 0)
        _ec_univ_av = int(st.session_state.get("epic_univ_shards", 0) or 0)
        _ec_needed  = epic_shards_needed(_ec_cur, _ec_tgt)
        _ec_sp_used = min(_ec_spec, _ec_needed)
        _ec_univ    = max(0, _ec_needed - _ec_sp_used)
        st.metric(t("Frags. necessários", "Shards needed"), f"{_ec_needed:,}")
        st.metric(t("Esp. usados / disponíveis", "Spec. used / available"), f"{_ec_sp_used:,} / {_ec_spec:,}")
        st.metric(t("Univ. necessários / disponíveis", "Univ. needed / available"), f"{_ec_univ:,} / {_ec_univ_av:,}")
        st.markdown("")
        if st.button(t("➕ Adicionar ao Lote", "➕ Add to Batch"), key="ecalc_add",
                     type="primary", use_container_width=True):
            _entry = {
                "relic": _ecalc_r,
                "from_s": _ec_star, "from_l": _ec_leg,
                "to_s": _ec_tgt_star, "to_l": _ec_tgt_leg,
                "shards": _ec_needed, "spec_used": _ec_sp_used, "univ_used": _ec_univ,
            }
            _eplan = [e for e in st.session_state["epic_plan"] if e["relic"] != _ecalc_r]
            _eplan.append(_entry)
            st.session_state["epic_plan"] = _eplan
            st.success(t(f"✅ {_rn(_ecalc_r)} adicionada ao lote!", f"✅ {_rn(_ecalc_r)} added to batch!"))

    st.markdown("---")
    st.subheader(t("📊 Projeção de Evento — Épicas", "📊 Event Projection — Epic"))
    st.caption(t(
        "Fragmentos épicos valem ×25 pts na Corrida de Relíquias.",
        "Epic shards are worth ×25 pts in the Relic Race event.",
    ))

    with st.expander(t("⚡ Adicionar todas ao Lote", "⚡ Add all to Batch"), expanded=False):
        _ea0, _ea1, _ea2 = st.columns(3)
        with _ea0:
            _all_e_from_star = st.selectbox(
                t("De (atual)", "From (current)"),
                _STAR_TIER_OPTS,
                format_func=lambda x: _star_fmt.get(x, x),
                key="epic_all_from_star",
            )
            _all_e_from_leg = st.selectbox(
                t("Perna atual", "Current leg"), LEG_OPTIONS,
                key="epic_all_from_leg", disabled=(_all_e_from_star == "0★"),
            )
        with _ea1:
            _all_e_star = st.selectbox(
                t("Estrela alvo", "Target star"),
                _STAR_TIER_OPTS[1:],
                format_func=lambda x: _star_fmt.get(x, x),
                key="epic_all_tgt_star",
            )
        with _ea2:
            _all_e_leg = st.selectbox(
                t("Perna alvo", "Target leg"),
                LEG_OPTIONS, key="epic_all_tgt_leg",
            )
        if st.button(t("➕ Adicionar todas ao Lote", "➕ Add all to Batch"), key="epic_add_all", type="primary"):
            _new_ep = list(st.session_state["epic_plan"])
            _ci_all = star_leg_to_idx(_all_e_from_star, _all_e_from_leg)
            _ti_all = star_leg_to_idx(_all_e_star, _all_e_leg)
            for _r in EPIC_RELICS:
                _sh = epic_shards_needed(_ci_all, _ti_all)
                _sp = int(st.session_state.get(f"espec_{_r}", 0) or 0)
                _su = min(_sp, _sh)
                _uu = max(0, _sh - _su)
                _new_ep = [e for e in _new_ep if e["relic"] != _r]
                _new_ep.append({
                    "relic": _r,
                    "from_s": _all_e_from_star, "from_l": _all_e_from_leg,
                    "to_s": _all_e_star, "to_l": _all_e_leg,
                    "shards": _sh, "spec_used": _su, "univ_used": _uu,
                })
            st.session_state["epic_plan"] = _new_ep
            st.success(t("✅ Todas as épicas adicionadas!", "✅ All epic relics added!"))

    _ev_rr = next(e for e in EVENTS if e["sheet"] == "Relic_Race")
    _ev_rr_name = _ev_rr.get("name_pt", _ev_rr["name"]) if lang == "pt" else _ev_rr["name"]
    _eplan = st.session_state["epic_plan"]
    if not _eplan:
        st.info(t(
            "Lote vazio. Use a Calculadora acima ou '⚡ Adicionar todas'.",
            "Batch is empty. Use the Calculator above or '⚡ Add all'.",
        ))
    else:
        _ep_rows = []
        _ep_total = 0
        for _e in _eplan:
            _fr_lbl = _star_fmt.get(_e["from_s"], _e["from_s"]) + (f" {_e['from_l']}" if _e["from_s"] != "0★" else "")
            _to_lbl = _star_fmt.get(_e["to_s"], _e["to_s"]) + f" {_e['to_l']}"
            _ep_rows.append({
                t("Relíquia", "Relic"): _rn(_e["relic"]),
                t("De", "From"):        _fr_lbl,
                t("Para", "To"):        _to_lbl,
                t("Frags.", "Shards"):  _e["shards"],
                t("Esp. usados", "Spec. used"): _e["spec_used"],
            })
            _ep_total += _e["shards"]
        st.dataframe(pd.DataFrame(_ep_rows), use_container_width=True, hide_index=True)

        _del_opts_e = [_rn(e["relic"]) for e in _eplan]
        _del_sel_e = st.selectbox(t("Remover do lote", "Remove from batch"), ["—"] + _del_opts_e, key="epic_del_sel")
        if _del_sel_e != "—":
            if st.button(f"🗑️ {t('Remover', 'Remove')} {_del_sel_e}", key="epic_del_btn"):
                st.session_state["epic_plan"].pop(_del_opts_e.index(_del_sel_e))
                st.rerun()

        st.divider()
        _ep_pts = _ep_total * 25
        _mc1, _mc2 = st.columns(2)
        _mc1.metric(t("Total frags. épicos", "Total epic shards"), f"{_ep_total:,}")
        _mc2.metric(t("Pontos no evento (×25)", "Event pts (×25)"), f"{_ep_pts:,}")
        _ms_str = "  ".join(
            f"✅ {s['value']:,}" if s["reached"] else f"⬜ {s['value']:,}"
            for s in get_milestone_status(_ev_rr["milestones"], _ep_pts)
        )
        st.caption(f"**{_ev_rr_name}** — {_ms_str}")
        st.divider()
        if st.button("🗑️ " + t("Limpar lote épico", "Clear epic batch"), key="epic_clear"):
            st.session_state["epic_plan"] = []
            st.rerun()

with tab_rare:
    st.caption(t(
        "Registre seus fragmentos raros e calcule o custo de upgrades.",
        "Record your rare shards and calculate upgrade costs.",
    ))

    @st.fragment
    def _rare_inventory_section():
        _uh, _ui = st.columns([5, 6])
        with _uh:
            st.markdown(f"**{t('Frags. universais raros', 'Rare universal shards')}**")
            st.caption(t("Usáveis em qualquer relíquia rara", "Usable on any rare relic"))
        with _ui:
            st.number_input(
                "univ_r", min_value=0,
                key="rare_univ_shards",
                on_change=_rare_save_all,
                label_visibility="collapsed",
            )
        st.divider()
        _hc1, _hc2 = st.columns([4, 7])
        _hc1.caption(t("Relíquia", "Relic"))
        _hc2.caption(t("Frags. específicos", "Spec. shards"))
        for _relic in RARE_RELICS:
            _portrait = _load_portrait(_relic)
            _c1, _c2 = st.columns([4, 7])
            with _c1:
                _cp, _cn = st.columns([1, 3])
                with _cp:
                    if _portrait is not None:
                        st.image(_portrait, width=44)
                    else:
                        st.markdown("💎")
                with _cn:
                    st.markdown(f"**{_rn(_relic)}**")
            with _c2:
                st.number_input(
                    "spec", min_value=0,
                    key=f"rspec_{_relic}",
                    on_change=_rare_save_all,
                    label_visibility="collapsed",
                )
        st.divider()

    st.subheader(t("📦 Inventário — Raras", "📦 Inventory — Rare"))
    _rare_inventory_section()

    st.markdown("---")
    st.subheader(t("🧮 Calculadora Individual", "🧮 Individual Calculator"))
    _rc1, _rc2, _rc3 = st.columns(3)
    with _rc1:
        _rcalc_disp = [_rn(r) for r in RARE_RELICS]
        _rcalc_d    = st.selectbox(t("Relíquia", "Relic"), _rcalc_disp, key="rcalc_relic")
        _rcalc_r    = RARE_RELICS[_rcalc_disp.index(_rcalc_d)]
        _rp = _load_portrait(_rcalc_r)
        if _rp:
            st.image(_rp, width=44)
    with _rc2:
        _rc_star = st.selectbox(
            t("Nível atual", "Current level"), _STAR_TIER_OPTS_RARE,
            format_func=lambda x: _star_fmt.get(x, x),
            key="rcalc_cur_star",
        )
        _rc_leg = st.selectbox(
            t("Perna atual", "Current leg"), LEG_OPTIONS,
            key="rcalc_cur_leg", disabled=(_rc_star == "0★"),
        )
        _rc_cur = star_leg_to_idx(_rc_star, _rc_leg)
        _rc_tgt_star = st.selectbox(
            t("Estrela alvo", "Target star"), _STAR_TIER_OPTS_RARE[1:], key="rcalc_tgt_star",
            format_func=lambda x: _star_fmt.get(x, x),
        )
        _rc_tgt_leg = st.selectbox(t("Perna alvo", "Target leg"), LEG_OPTIONS, key="rcalc_tgt_leg")
    with _rc3:
        _rc_tgt     = star_leg_to_idx(_rc_tgt_star, _rc_tgt_leg)
        _rc_spec    = int(st.session_state.get(f"rspec_{_rcalc_r}", 0) or 0)
        _rc_univ_av = int(st.session_state.get("rare_univ_shards", 0) or 0)
        _rc_needed  = rare_shards_needed(_rc_cur, _rc_tgt)
        _rc_sp_used = min(_rc_spec, _rc_needed)
        _rc_univ    = max(0, _rc_needed - _rc_sp_used)
        st.metric(t("Frags. necessários", "Shards needed"), f"{_rc_needed:,}")
        st.metric(t("Esp. usados / disponíveis", "Spec. used / available"), f"{_rc_sp_used:,} / {_rc_spec:,}")
        st.metric(t("Univ. necessários / disponíveis", "Univ. needed / available"), f"{_rc_univ:,} / {_rc_univ_av:,}")
        st.markdown("")
        if st.button(t("➕ Adicionar ao Lote", "➕ Add to Batch"), key="rcalc_add",
                     type="primary", use_container_width=True):
            _rentry = {
                "relic": _rcalc_r,
                "from_s": _rc_star, "from_l": _rc_leg,
                "to_s": _rc_tgt_star, "to_l": _rc_tgt_leg,
                "shards": _rc_needed, "spec_used": _rc_sp_used, "univ_used": _rc_univ,
            }
            _rplan = [e for e in st.session_state["rare_plan"] if e["relic"] != _rcalc_r]
            _rplan.append(_rentry)
            st.session_state["rare_plan"] = _rplan
            st.success(t(f"✅ {_rn(_rcalc_r)} adicionada ao lote!", f"✅ {_rn(_rcalc_r)} added to batch!"))

    st.markdown("---")
    st.subheader(t("📊 Projeção de Evento — Raras", "📊 Event Projection — Rare"))
    st.caption(t(
        "Fragmentos raros valem ×5 pts na Corrida de Relíquias.",
        "Rare shards are worth ×5 pts in the Relic Race event.",
    ))

    with st.expander(t("⚡ Adicionar todas ao Lote", "⚡ Add all to Batch"), expanded=False):
        _ra0, _ra1, _ra2 = st.columns(3)
        with _ra0:
            _all_r_from_star = st.selectbox(
                t("De (atual)", "From (current)"),
                _STAR_TIER_OPTS_RARE,
                format_func=lambda x: _star_fmt.get(x, x),
                key="rare_all_from_star",
            )
            _all_r_from_leg = st.selectbox(
                t("Perna atual", "Current leg"), LEG_OPTIONS,
                key="rare_all_from_leg", disabled=(_all_r_from_star == "0★"),
            )
        with _ra1:
            _all_r_star = st.selectbox(
                t("Estrela alvo", "Target star"),
                _STAR_TIER_OPTS_RARE[1:],
                format_func=lambda x: _star_fmt.get(x, x),
                key="rare_all_tgt_star",
            )
        with _ra2:
            _all_r_leg = st.selectbox(
                t("Perna alvo", "Target leg"),
                LEG_OPTIONS, key="rare_all_tgt_leg",
            )
        if st.button(t("➕ Adicionar todas ao Lote", "➕ Add all to Batch"), key="rare_add_all", type="primary"):
            _new_rp = list(st.session_state["rare_plan"])
            _ci_all_r = star_leg_to_idx(_all_r_from_star, _all_r_from_leg)
            _ti_all_r = star_leg_to_idx(_all_r_star, _all_r_leg)
            for _r in RARE_RELICS:
                _sh = rare_shards_needed(_ci_all_r, _ti_all_r)
                _sp = int(st.session_state.get(f"rspec_{_r}", 0) or 0)
                _su = min(_sp, _sh)
                _uu = max(0, _sh - _su)
                _new_rp = [e for e in _new_rp if e["relic"] != _r]
                _new_rp.append({
                    "relic": _r,
                    "from_s": _all_r_from_star, "from_l": _all_r_from_leg,
                    "to_s": _all_r_star, "to_l": _all_r_leg,
                    "shards": _sh, "spec_used": _su, "univ_used": _uu,
                })
            st.session_state["rare_plan"] = _new_rp
            st.success(t("✅ Todas as raras adicionadas!", "✅ All rare relics added!"))

    _ev_rr2 = next(e for e in EVENTS if e["sheet"] == "Relic_Race")
    _ev_rr2_name = _ev_rr2.get("name_pt", _ev_rr2["name"]) if lang == "pt" else _ev_rr2["name"]
    _rplan = st.session_state["rare_plan"]
    if not _rplan:
        st.info(t(
            "Lote vazio. Use a Calculadora acima ou '⚡ Adicionar todas'.",
            "Batch is empty. Use the Calculator above or '⚡ Add all'.",
        ))
    else:
        _rp_rows = []
        _rp_total = 0
        for _e in _rplan:
            _fr_lbl = _star_fmt.get(_e["from_s"], _e["from_s"]) + (f" {_e['from_l']}" if _e["from_s"] != "0★" else "")
            _to_lbl = _star_fmt.get(_e["to_s"], _e["to_s"]) + f" {_e['to_l']}"
            _rp_rows.append({
                t("Relíquia", "Relic"): _rn(_e["relic"]),
                t("De", "From"):        _fr_lbl,
                t("Para", "To"):        _to_lbl,
                t("Frags.", "Shards"):  _e["shards"],
                t("Esp. usados", "Spec. used"): _e["spec_used"],
            })
            _rp_total += _e["shards"]
        st.dataframe(pd.DataFrame(_rp_rows), use_container_width=True, hide_index=True)

        _del_opts_r = [_rn(e["relic"]) for e in _rplan]
        _del_sel_r = st.selectbox(t("Remover do lote", "Remove from batch"), ["—"] + _del_opts_r, key="rare_del_sel")
        if _del_sel_r != "—":
            if st.button(f"🗑️ {t('Remover', 'Remove')} {_del_sel_r}", key="rare_del_btn"):
                st.session_state["rare_plan"].pop(_del_opts_r.index(_del_sel_r))
                st.rerun()

        st.divider()
        _rp_pts = _rp_total * 5
        _mc1, _mc2 = st.columns(2)
        _mc1.metric(t("Total frags. raros", "Total rare shards"), f"{_rp_total:,}")
        _mc2.metric(t("Pontos no evento (×5)", "Event pts (×5)"), f"{_rp_pts:,}")
        _ms_str = "  ".join(
            f"✅ {s['value']:,}" if s["reached"] else f"⬜ {s['value']:,}"
            for s in get_milestone_status(_ev_rr2["milestones"], _rp_pts)
        )
        st.caption(f"**{_ev_rr2_name}** — {_ms_str}")
        st.divider()
        if st.button("🗑️ " + t("Limpar lote raro", "Clear rare batch"), key="rare_clear"):
            st.session_state["rare_plan"] = []
            st.rerun()

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
- **Martelos Milagrosos**: quantidade disponível (cada martelo troca o nível de estrela entre duas relíquias)
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
- **Miracle Hammers**: quantity available (each hammer swaps the star level between two relics)
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

