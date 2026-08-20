"""
pages/2_DE_Dust.py — DE & Dust Planner page.
"""

import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from PIL import Image

_BASE    = os.path.dirname(os.path.dirname(__file__))
_IMG_DIR = os.path.join(_BASE, "de_dust_imgs")
_ICON_H  = 22

def _show_de(st_mod=None):
    m = st_mod or st
    img = Image.open(os.path.join(_IMG_DIR, "dragon_essence.png"))
    r = _ICON_H / img.height
    w = max(1, int(img.width * r))
    m.image(img.resize((w, _ICON_H), Image.LANCZOS), width=w)

def _show_dust(st_mod=None):
    m = st_mod or st
    img = Image.open(os.path.join(_IMG_DIR, "dragon_dust.png"))
    r = _ICON_H / img.height
    w = max(1, int(img.width * r))
    m.image(img.resize((w, _ICON_H), Image.LANCZOS), width=w)
from de_dust_engine import (
    BUILDINGS, CASTLE_PREREQS, PREREQ_LABELS, FACTION_LABEL,
    BI_LEVEL_COSTS,
    de_cost, max_b, castle_prereq_chain, compute_castle_total, bi_de_cost,
    bar_labels, de_cost_bar,
    BI_R, BI2_R, FAC_R, AWK_R, S2_R, S3_R, S4_R,
    RESEARCH_TIER_SLICES,
    research_max_levels, research_cost,
)
from ui_utils import inject_global_css
import persistence

st.set_page_config(page_title="DE & Dust Planner", page_icon="🏗️", layout="wide")

# ── Persistence ────────────────────────────────────────────────────────────────
_cm = persistence.new_manager("dedust")

if "de_initialized" not in st.session_state:
    _saved = persistence.load(_cm, "th_dedust")
    if _saved:
        st.session_state["de_avail"]   = int(_saved.get("de_avail", 0))
        st.session_state["dust_avail"] = int(_saved.get("dust_avail", 0))
    st.session_state["de_initialized"] = True


def _dedust_save():
    persistence.save(_cm, "th_dedust", {
        "de_avail":   st.session_state.get("de_avail", 0),
        "dust_avail": st.session_state.get("dust_avail", 0),
    })


# ── Language ───────────────────────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "en"

with st.sidebar:
    st.markdown("### 🌐 Idioma / Language")
    lang_pick = st.radio(
        "", ["🇧🇷 Português", "🇬🇧 English"],
        index=0 if st.session_state.lang == "pt" else 1,
        horizontal=True, label_visibility="collapsed", key="lang_de",
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

B_OPTIONS = ["B0", "B1", "B2", "B3", "B4", "B5", "B6"]

_FACS      = ["league", "horde", "nature"]
_FAC_NAMES = {
    "league": "⚔️ " + t("Liga",     "League"),
    "horde":  "🔥 " + t("Horda",    "Horde"),
    "nature": "🌿 " + t("Natureza", "Nature"),
}
_BRK_DISPLAY = {
    "League": t("Liga",     "League"),
    "Horde":  t("Horda",    "Horde"),
    "Nature": t("Natureza", "Nature"),
}
_DISP_TO_EN = {v: k for k, v in _BRK_DISPLAY.items()}

# ── Header ─────────────────────────────────────────────────────────────────────
inject_global_css()
st.title("🏗️ " + t("Planejador DE & Pó", "DE & Dust Planner"))
st.caption(t(
    "Essência de Dragão (DE) · Pó de Dragão · Brilho (s108+)",
    "Dragon Essence (DE) · Dragon Dust · Brilliance (s108+)",
))

# ── DICAS ─────────────────────────────────────────────────────────────────────

tab_main, tab_help = st.tabs([
    "🏗️ " + t("Planejador", "Planner"),
    "📖 " + t("Instruções & Referência", "Instructions & Reference"),
])

with tab_main:
    with st.expander("💡 " + t("Dicas — Como conseguir 1k+ DE+Pó por ciclo F2P", "Tips — How to get 1k+ DE+Dust per F2P cycle"), expanded=False):
        st.markdown(f"**{t('Como conseguir mais de 1k de DE+Pó a cada duas semanas como F2P','How to get 1k+ DE+Dust every two weeks as F2P')}**")
        st.caption(t(
            "Valores calculados para um ciclo de **14 dias**, considerando a sexta-feira da corrida da guilda como referência.",
            "Values calculated for a **14-day** cycle, using the guild race Friday as reference.",
        ))

        _src_col  = t("Fonte", "Source")
        _freq_col = t("Frequência", "Frequency")
        _de_col   = "DE"
        _du_col   = t("Pó", "Dust")

        # (source_pt, source_en, freq_pt, freq_en, de, dust, note_pt, note_en, is_optional)
        _tips_data = [
            ("Dragão Negro / Yeti (loja)",
             "Black Dragon / Yeti (store)",
             "2× por ciclo (a cada 2 sem.)",
             "2× per cycle (every 2 wks)",
             200, 200,
             "Loja aparece a cada 2 semanas — coincide com as duas sextas do ciclo.",
             "Store appears every 2 weeks — matches both Fridays of the cycle.",
             False),
            ("Loja de Honra da Guilda",
             "Guild Honor Store",
             "Semanal (2×)",
             "Weekly (2×)",
             70, 70,
             "", "", False),
            ("Loja de Troca",
             "Trade Store",
             "Semanal (2×)",
             "Weekly (2×)",
             60, None,
             "", "", False),
            ("Loja da Guilda",
             "Guild Store",
             "Semanal (2×)",
             "Weekly (2×)",
             None, 70,
             "", "", False),
            ("Marcos das Minas",
             "Mines Milestones",
             "Semanal (2×)",
             "Weekly (2×)",
             60, None,
             "", "", False),
            ("Oficina de Essência",
             "Essence Workshop",
             "Diário (mín. 7/dia × 14)",
             "Daily (min. 7/day × 14)",
             98, None,
             "Mínimo de 7 por dia. Valor pode ser maior dependendo da atividade.",
             "Minimum 7 per day. Value may be higher depending on activity.",
             False),
            ("Evento Regular — Equipamento do Lorde",
             "Regular Event — Lord Gear",
             "2× por ciclo (a cada 2 sem.)",
             "2× per cycle (every 2 wks)",
             150, 150,
             "Evento aparece a cada 2 semanas — coincide com as duas sextas do ciclo.",
             "Event appears every 2 weeks — matches both Fridays of the cycle.",
             False),
            ("Recompensas",
             "Bounties",
             "Diário (6/dia × 14)",
             "Daily (6/day × 14)",
             84, None,
             "", "", False),
            (t("Privilégio Permanente (opcional)", "Permanent Privilege (optional)"),
             "Permanent Privilege (optional)",
             "Diário (10/dia × 14)",
             "Daily (10/day × 14)",
             140, None,
             "S3+ · Pago · Opcional",
             "S3+ · Paid · Optional",
             True),  # optional — excluded from F2P total
        ]

        _display_rows = []
        for row in _tips_data:
            src  = row[0] if lang == "pt" else row[1]
            freq = row[2] if lang == "pt" else row[3]
            de_v = str(row[4]) if row[4] is not None else "—"
            du_v = str(row[5]) if row[5] is not None else "—"
            _display_rows.append({_src_col: src, _freq_col: freq, _de_col: de_v, _du_col: du_v})

        st.dataframe(pd.DataFrame(_display_rows), use_container_width=True, hide_index=True)

        # Totals — exclude optional (Privilege)
        _total_de_f2p = sum(r[4] for r in _tips_data if r[4] is not None and not r[8])
        _total_de_all = sum(r[4] for r in _tips_data if r[4] is not None)
        _total_du     = sum(r[5] for r in _tips_data if r[5] is not None)

        _tc1, _tc2, _tc3, _tc4 = st.columns(4)
        _tc1.metric(t("DE F2P", "DE F2P"),             f"{_total_de_f2p}+")
        _tc2.metric(t("DE com Priv.", "DE with Priv."), f"{_total_de_all}+")
        _tc3.metric(t("Pó", "Dust"),                   f"{_total_du}")
        _tc4.metric(t("DE+Pó F2P", "DE+Dust F2P"),     f"{_total_de_f2p + _total_du}+")

        st.markdown("---")
        st.markdown(f"**{t('Observações','Notes')}**")
        for row in _tips_data:
            note = row[6] if lang == "pt" else row[7]
            src  = row[0] if lang == "pt" else row[1]
            if note:
                st.caption(f"**{src}** — {note}")

        st.info(t(
            "ⓘ **Privilégio Permanente** — Disponível a partir da **S3**. Recurso **pago** e opcional — "
            "não contabilizado no total F2P.",
            "ⓘ **Permanent Privilege** — Available from **S3** onwards. **Paid** and optional — "
            "not counted in the F2P total.",
        ))

    # ── INVENTÁRIO ─────────────────────────────────────────────────────────────────
    with st.expander(t("📦 Inventário de Recursos", "📦 Resource Inventory"), expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            _show_de()
            de_avail = st.number_input(
                t("Essência de Dragão disponível", "Dragon Essence available"),
                min_value=0, value=0, step=500, format="%d", key="de_avail",
                on_change=_dedust_save,
            )
        with c2:
            _show_dust()
            dust_avail = st.number_input(
                t("Pó de Dragão disponível", "Dragon Dust available"),
                min_value=0, value=0, step=500, format="%d", key="dust_avail",
                on_change=_dedust_save,
            )
        with c3:
            de_convert = st.number_input(
                t("Converter DE → Pó (1:1)", "Convert DE → Dust (1:1)"),
                min_value=0, max_value=int(de_avail), value=0, step=100, format="%d",
                help=t("DE é convertido em pó na proporção 1:1. Esta conversão é irreversível.",
                       "DE converts to Dust at 1:1. This conversion is irreversible."),
            )

        de_eff   = de_avail - de_convert
        dust_eff = dust_avail + de_convert

        mc1, mc2 = st.columns(2)
        mc1.metric(t("DE efetivo", "Effective DE"),   f"{de_eff:,}")
        mc2.metric(t("Pó efetivo", "Effective Dust"), f"{dust_eff:,}")

    # ── CASTELO — CADEIA DE PRÉ-REQUISITOS ────────────────────────────────────────
    st.divider()
    st.subheader("🏰 " + t("Castelo — Cadeia de Pré-requisitos", "Castle — Prerequisite Chain"))
    st.caption(
        t("Ao definir o nível alvo do Castelo, o custo das construções pré-requisito é calculado automaticamente.",
          "When you set the Castle target level, prerequisite building costs are calculated automatically.")
    )

    _castle_labels = bar_labels("castle")

    cc1, cc2 = st.columns(2)
    with cc1:
        castle_from_sel = st.selectbox(t("Nível atual do Castelo", "Current Castle Level"),
                                       _castle_labels, index=0, key="castle_from_bar")

    castle_from_bar = _castle_labels.index(castle_from_sel)
    castle_from_b   = castle_from_bar // 5

    with cc2:
        _castle_to_opts = _castle_labels[castle_from_bar + 1:]
        if not _castle_to_opts:
            st.info(t("Castelo já está no nível máximo.", "Castle is already at maximum level."))
            castle_to_sel = castle_from_sel
        else:
            castle_to_sel = st.selectbox(t("Nível alvo do Castelo", "Target Castle Level"),
                                         _castle_to_opts, index=len(_castle_to_opts) - 1,
                                         key="castle_to_bar")

    castle_to_bar = _castle_labels.index(castle_to_sel)
    castle_to_b   = castle_to_bar // 5

    # "Any barracks" choice for B5/B6
    _BRK_MAP = {"League": "brk_l", "Horde": "brk_h", "Nature": "brk_n"}
    brk_any_choice = "brk_l"
    if castle_to_b >= 5:
        _pre_chain = castle_prereq_chain(castle_from_b, 0, {}, "brk_l")
        _pre_b     = {p["building_id"]: p["required_b"] for p in _pre_chain if not p["is_regular_level"]}
        _brk_opts_en = sorted(_BRK_MAP.keys(), key=lambda x: (_pre_b.get(_BRK_MAP[x], 0), x))
        _brk_opts    = [_BRK_DISPLAY[k] for k in _brk_opts_en]
        brk_pick_disp = st.selectbox(
            t("Quartel para pré-requisito B5/B6 (escolha)", "Barracks for B5/B6 prerequisite (choose)"),
            _brk_opts, key=f"brk_any_{castle_from_b}_{castle_to_b}",
        )
        brk_any_choice = _BRK_MAP[_DISP_TO_EN[brk_pick_disp]]

    # Collect current B levels for prerequisite buildings
    temp_chain    = castle_prereq_chain(castle_to_b, castle_from_b, {}, brk_any_choice)
    real_prereqs  = [p for p in temp_chain if not p["is_regular_level"]]
    regular_notes = [p for p in temp_chain if p["is_regular_level"]]

    current_prereq_levels = {}
    prereq_bar_indices    = {}
    if real_prereqs:
        # What each prereq building already needed at the current castle level
        _already_chain = castle_prereq_chain(castle_from_b, 0, {}, brk_any_choice)
        _already_b     = {p["building_id"]: p["required_b"]
                          for p in _already_chain if not p["is_regular_level"]}

        st.markdown(t("**Nível atual de cada pré-requisito:**", "**Current level of each prerequisite:**"))
        prereq_cols = st.columns(min(len(real_prereqs), 4))
        for i, p in enumerate(real_prereqs):
            bid     = p["building_id"]
            bname   = p["label_pt"] if lang == "pt" else p["label_en"]
            labels  = bar_labels(bid)
            max_bar = min(len(labels) - 1, castle_to_b * 5)
            opts    = labels[: max_bar + 1]
            already_bar = min(_already_b.get(bid, 0) * 5, len(opts) - 1)
            with prereq_cols[i % 4]:
                sel     = st.selectbox(bname, opts, index=already_bar,
                                       key=f"pre_{castle_from_b}_{castle_to_b}_{bid}")
                bar_idx = opts.index(sel)
                current_prereq_levels[bid] = bar_idx // 5   # B level for engine
                prereq_bar_indices[bid]    = bar_idx         # bar index for precise cost

    for note in regular_notes:
        label = note["label_pt"] if lang == "pt" else note["label_en"]
        st.warning(
            t(f"⚠️ **{label}** deve estar no nível regular indicado antes de subir o Castelo para B1. "
              "Custo de DE para níveis normais não calculado aqui.",
              f"⚠️ **{label}** must be at the indicated regular level before upgrading Castle to B1. "
              "Regular-level DE cost not calculated here.")
        )

    if castle_from_bar < castle_to_bar:
        castle_own_de = de_cost_bar("castle", castle_from_bar, castle_to_bar)

        if castle_from_b < castle_to_b:
            result = compute_castle_total(castle_to_b, castle_from_b, current_prereq_levels, brk_any_choice)
            result["castle_de"] = castle_own_de
            # Refine prereq costs to bar-level precision
            for p in result["prereqs"]:
                bid = p["building_id"]
                if not p["is_regular_level"] and bid in prereq_bar_indices:
                    curr_bar = prereq_bar_indices[bid]
                    req_bar  = p["required_b"] * 5
                    p["de_cost"]        = de_cost_bar(bid, curr_bar, req_bar)
                    p["needs_upgrade"]  = curr_bar < req_bar
                    p["curr_bar_label"] = bar_labels(bid)[curr_bar]
            result["prereq_de"] = sum(p["de_cost"] for p in result["prereqs"] if not p["is_regular_level"])
            result["total_de"]  = result["castle_de"] + result["prereq_de"]
        else:
            # Within same B level — no prerequisites, just bar cost
            result = {"castle_de": castle_own_de, "prereqs": [], "prereq_de": 0, "total_de": castle_own_de}

        rows = [{"#": "🏰",
                 t("Construção", "Building"): f"Castle {castle_from_sel} → {castle_to_sel}",
                 t("Atual", "Current"): castle_from_sel,
                 t("Alvo", "Target"):   castle_to_sel,
                 "DE": f"{result['castle_de']:,}"}]

        for p in result["prereqs"]:
            if p["is_regular_level"]:
                continue
            bname        = p["label_pt"] if lang == "pt" else p["label_en"]
            status       = "✅" if not p["needs_upgrade"] else "🔨"
            curr_display = p.get("curr_bar_label", f"B{p['current_b']}")
            de_val       = (f"{p['de_cost']:,}" if p["de_cost"] > 0
                            else ("✅ " + t("já possui", "already have")))
            rows.append({
                "#":                    status,
                t("Construção", "Building"): bname,
                t("Atual", "Current"):  curr_display,
                t("Alvo", "Target"):    f"B{p['required_b']}",
                "DE":                   de_val,
            })

        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        m1, m2, m3 = st.columns(3)
        m1.metric(t("DE — Castelo",        "DE — Castle"),        f"{result['castle_de']:,}")
        m2.metric(t("DE — Pré-requisitos", "DE — Prerequisites"), f"{result['prereq_de']:,}")
        m3.metric(t("DE Total (Castelo)",  "Total DE (Castle)"),  f"{result['total_de']:,}")

        castle_total_de = result["total_de"]
    else:
        castle_total_de = 0

    # ── OUTRAS CONSTRUÇÕES ─────────────────────────────────────────────────────────
    st.divider()
    st.subheader("🏗️ " + t("Outras Construções", "Other Buildings"))
    st.caption(t(
        "Cada barra é um nível (B0 = nível 40, B1 = nível 45, etc.). "
        "Pré-requisitos do castelo já iniciam no nível exigido — custo aqui = apenas upgrades além do necessário.",
        "Each bar is one level (B0 = lv40, B1 = lv45, etc.). "
        "Castle prerequisites start at their required level — cost here = only upgrades beyond what the castle needs."
    ))

    other_bids = [k for k, v in BUILDINGS.items()
                  if k != "castle" and not v.get("bi_special")]

    faction_groups = {"all": [], "league": [], "horde": [], "nature": []}
    for bid in other_bids:
        faction_groups[BUILDINGS[bid]["faction"]].append(bid)

    other_de_total = 0
    _COLS = 3

    # Prereq buildings needed for this upgrade (already costed in castle section above)
    _req_b_for = {p["building_id"]: p["required_b"] for p in real_prereqs}

    for _bid in prereq_bar_indices:
        _bl      = bar_labels(_bid)
        _max_bar = min(len(_bl) - 1, castle_to_b * 5)
        _opts    = _bl[:_max_bar + 1]
        _req_bar = min(_req_b_for.get(_bid, 0) * 5, len(_opts) - 1)
        # Always lock "from" to the required level (that cost is already in castle prereqs above)
        st.session_state[f"ob_{castle_from_b}_{castle_to_b}_from_{_bid}"] = _opts[_req_bar]
        # Ensure "to" is at least the required level; leave higher values so user can plan extra upgrades
        _to_key = f"ob_{castle_from_b}_{castle_to_b}_to_{_bid}"
        _to_cur = st.session_state.get(_to_key)
        if _to_cur not in _opts or _opts.index(_to_cur) < _req_bar:
            st.session_state[_to_key] = _opts[_req_bar]

    # Already-achieved levels at castle_from_b (default "Current" for non-req buildings)
    _from_chain  = castle_prereq_chain(castle_from_b, 0, {}, brk_any_choice)
    _curr_preq_b = {p["building_id"]: p["required_b"] for p in _from_chain if not p["is_regular_level"]}

    for faction, bids in faction_groups.items():
        if not bids:
            continue
        flabel = FACTION_LABEL[faction]["pt"] if lang == "pt" else FACTION_LABEL[faction]["en"]
        with st.expander(f"**{flabel}**", expanded=(faction == "all")):
            faction_de = 0

            for row_start in range(0, len(bids), _COLS):
                row_bids = bids[row_start : row_start + _COLS]
                row_cols = st.columns(len(row_bids))
                for col, bid in zip(row_cols, row_bids):
                    bdata  = BUILDINGS[bid]
                    bname  = bdata["pt"] if lang == "pt" else bdata["en"]
                    labels = bar_labels(bid)
                    max_bar = min(len(labels) - 1, castle_to_b * 5)
                    opts    = labels[: max_bar + 1]

                    if bid in _req_b_for:
                        # Covered by castle prereqs — from = required level, to defaults to same (no double-count)
                        req_bar      = min(_req_b_for[bid] * 5, len(opts) - 1)
                        from_default = req_bar
                        to_default   = req_bar
                    else:
                        # Not in current plan — pre-fill "from" with already-achieved level, no extra upgrade
                        curr_req_b   = _curr_preq_b.get(bid, 0)
                        from_default = min(curr_req_b * 5, len(opts) - 1)
                        to_default   = from_default

                    with col:
                        with st.container(border=True):
                            st.markdown(f"**{bname}**")
                            fc, tc = st.columns(2)
                            with fc:
                                from_sel = st.selectbox(
                                    t("Atual", "Current"), opts,
                                    **({} if bid in _req_b_for else {"index": from_default}),
                                    key=f"ob_{castle_from_b}_{castle_to_b}_from_{bid}",
                                )
                            with tc:
                                to_sel = st.selectbox(
                                    t("Alvo", "Target"), opts,
                                    **({} if bid in _req_b_for else {"index": to_default}),
                                    key=f"ob_{castle_from_b}_{castle_to_b}_to_{bid}",
                                )
                            from_bar = opts.index(from_sel)
                            to_bar   = opts.index(to_sel)
                            cost     = de_cost_bar(bid, from_bar, to_bar)
                            faction_de += cost
                            if cost > 0:
                                st.caption(f"DE: {cost:,}")

            other_de_total += faction_de
            if faction_de > 0:
                st.metric(t(f"DE — {flabel}", f"DE — {flabel}"), f"{faction_de:,}")

    # ── BRILLIANCE INSTITUTE ───────────────────────────────────────────────────────
    st.divider()
    st.subheader("🔬 " + t("Instituto de Brilhantismo", "Brilliance Institute"))
    st.caption(
        t("Construção separada. Desbloqueada no Castle B2. 15 níveis, 745 DE total. "
          "Uma vez no nível 15, todas as pesquisas de Soldado XI estarão disponíveis.",
          "Separate building. Unlocked at Castle B2. 15 levels, 745 DE total. "
          "Once at level 15, all Soldier XI research is available.")
    )

    bi_c1, bi_c2 = st.columns(2)
    with bi_c1:
        bi_from = st.number_input(t("BI nível atual (0–15)", "BI current level (0–15)"),
                                   min_value=0, max_value=15, value=0, key="bi_from")
    with bi_c2:
        bi_to = st.number_input(t("BI nível alvo (0–15)", "BI target level (0–15)"),
                                 min_value=0, max_value=15, value=15, key="bi_to")

    bi_total = bi_de_cost(int(bi_from), int(bi_to))
    st.metric(t("DE — Instituto de Brilhantismo", "DE — Brilliance Institute"), f"{bi_total:,}")

    # ── PESQUISAS — DRAGON DUST ────────────────────────────────────────────────────
    st.divider()
    st.subheader("📜 " + t("Pesquisas — Pó de Dragão", "Research — Dragon Dust"))
    st.caption(t(
        "BI e Facção são independentes por facção (League / Horde / Nature) — custo ×3. "
        "Awakening, S2, S3 e S4 são compartilhadas (árvore única).",
        "BI and Faction are independent per faction (League / Horde / Nature) — cost ×3. "
        "Awakening, S2, S3, and S4 are shared (single tree)."
    ))

    # ── helper widgets (defined here so they can use t()) ─────────────────────────
    def _rphdr():
        h1, h2, h3, h4, h5 = st.columns([3, 1, 1, 1, 2])
        h1.caption(t("Pesquisa", "Research"))
        h2.caption(t("Atual", "Current"))
        h3.caption(t("Alvo", "Target"))
        h4.caption("")
        h5.caption(t("Pó", "Dust"))

    def _rrow(item, key, locked=False):
        mx = research_max_levels(item["levels"])
        opts = [str(i) for i in range(mx + 1)]
        # Apply pending max BEFORE widgets are instantiated
        if st.session_state.pop(f"{key}_pmx", False):
            st.session_state[f"{key}_f"] = str(mx)
            st.session_state[f"{key}_t"] = str(mx)
        # Sanitize legacy integer values from old number_input session state
        for _sfx in ("_f", "_t"):
            _sk = f"{key}{_sfx}"
            if _sk in st.session_state and not isinstance(st.session_state[_sk], str):
                st.session_state[_sk] = str(min(int(st.session_state[_sk]), mx))
        # Ensure defaults are in session state so we never pass index= alongside it
        if f"{key}_f" not in st.session_state:
            st.session_state[f"{key}_f"] = "0"
        if f"{key}_t" not in st.session_state:
            st.session_state[f"{key}_t"] = "0" if locked else str(mx)
        c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 2])
        _rname = item.get("name_pt", item["name"]) if lang == "pt" else item["name"]
        c1.markdown(f"{'🔒 ' if locked else ''}{_rname} *(0–{mx})*")
        from_sel = c2.selectbox(
            "f", opts,
            key=f"{key}_f", label_visibility="collapsed", disabled=locked,
        )
        to_sel = c3.selectbox(
            "t", opts,
            key=f"{key}_t", label_visibility="collapsed", disabled=locked,
        )
        if not locked:
            if c4.button("⬆", key=f"{key}_mx", help=t("Setar atual e alvo ao máximo", "Set current and target to max")):
                st.session_state[f"{key}_pmx"] = True
                st.rerun()
        cost = 0 if locked else research_cost(item["levels"], int(from_sel), int(to_sel))
        c5.caption(f"{cost:,}" if cost else "—")
        return cost

    def _reset_tree(prefix: str):
        """Zero all targets for keys matching prefix."""
        for _k in list(st.session_state.keys()):
            if _k.startswith(prefix) and _k.endswith("_t"):
                st.session_state[_k] = "0"
        st.rerun()

    def _max_flat(prefix: str, items: list):
        """Flag all items for max (flat-indexed tree: S2/S3/S4)."""
        for idx in range(len(items)):
            st.session_state[f"{prefix}{idx}_pmx"] = True
        st.rerun()

    def _max_tiered(prefix: str, items: list):
        """Flag all items for max (tier-sliced tree: Awakening)."""
        for slc, _ in RESEARCH_TIER_SLICES:
            for idx in range(len(items[slc])):
                st.session_state[f"{prefix}{slc.start}_{idx}_pmx"] = True
        st.rerun()

    res_tabs = st.tabs([
        "🧪 BI",
        "🧪 BI2",
        "⚔️ " + t("Facção", "Faction"),
        "🐉 Awakening",
        "S2", "S3", "S4",
    ])
    res_totals = {}   # tree_key → dust cost

    # ─── BI ───────────────────────────────────────────────────────────────────────
    with res_tabs[0]:
        st.caption(t(
            "Cada pesquisa requer um nível mínimo do Instituto de Brilhantismo (indicado nos grupos). "
            "O nível alvo do BI é definido na seção acima.",
            "Each research requires a minimum Brilliance Institute level (shown in groups). "
            "Your BI target is set in the section above."
        ))
        bi_phases: dict = {}
        for item in BI_R:
            bi_phases.setdefault(item.get("biReq", 1), []).append(item)

        fac_st_bi = st.tabs([_FAC_NAMES[f] for f in _FACS])
        bi_fac_totals = {}
        for fi, fac in enumerate(_FACS):
            with fac_st_bi[fi]:
                _b1, _b2 = st.columns(2)
                if _b1.button(t("↩ Zerar alvos", "↩ Reset targets"), key=f"rst_bi_{fac}"):
                    for _rlv, _pitems in bi_phases.items():
                        for _idx in range(len(_pitems)):
                            st.session_state[f"r_bi_{fac}_{_rlv}_{_idx}_t"] = "0"
                    st.rerun()
                if _b2.button(t("⬆ Máximo", "⬆ Max"), key=f"max_bi_{fac}"):
                    for _rlv, _pitems in bi_phases.items():
                        for _idx, _item in enumerate(_pitems):
                            st.session_state[f"r_bi_{fac}_{_rlv}_{_idx}_pmx"] = True
                    st.rerun()
                fac_total = 0
                for req_lv, pitems in sorted(bi_phases.items()):
                    locked  = int(bi_to) < req_lv
                    icon    = "🔒" if locked else "✅"
                    n_label = t("pesquisas", "researches")
                    with st.expander(
                        f"{icon} BI ≥ {req_lv}  —  {len(pitems)} {n_label}",
                        expanded=not locked,
                    ):
                        if locked:
                            st.caption(t(
                                f"Requer Instituto de Brilhantismo nível ≥ {req_lv}. "
                                f"Seu alvo atual é BI {int(bi_to)}.",
                                f"Requires Brilliance Institute level ≥ {req_lv}. "
                                f"Your current target is BI {int(bi_to)}."
                            ))
                        else:
                            _rphdr()
                            for idx, item in enumerate(pitems):
                                fac_total += _rrow(item, f"r_bi_{fac}_{req_lv}_{idx}")
                bi_fac_totals[fac] = fac_total
                st.metric(_FAC_NAMES[fac] + " — " + t("Pó BI", "Dust BI"), f"{fac_total:,}")

        bi_res_total = sum(bi_fac_totals.values())
        st.metric(t("Total Pó BI (todas as facções)", "Total Dust BI (all factions)"), f"{bi_res_total:,}")
        res_totals["BI"] = bi_res_total

    # ─── BI2 ──────────────────────────────────────────────────────────────────────
    with res_tabs[1]:
        st.caption(t(
            "⚠️ **BI2 desbloqueia quando BI1 atingir 70% de conclusão (≈ 21 000 Pó).** "
            "Necessário para tropas T12. Total de pó: **23 711** (por facção).",
            "⚠️ **BI2 unlocks when BI1 reaches 70% completion (≈ 21 000 Dust).** "
            "Required for T12 troops. Total dust: **23 711** (per faction).",
        ))
        fac_st_bi2 = st.tabs([_FAC_NAMES[f] for f in _FACS])
        bi2_fac_totals = {}
        for fi, fac in enumerate(_FACS):
            with fac_st_bi2[fi]:
                _b2b1, _b2b2 = st.columns(2)
                if _b2b1.button(t("↩ Zerar alvos", "↩ Reset targets"), key=f"rst_bi2_{fac}"):
                    for _idx in range(len(BI2_R)):
                        st.session_state[f"r_bi2_{fac}_{_idx}_t"] = "0"
                    st.rerun()
                if _b2b2.button(t("⬆ Máximo", "⬆ Max"), key=f"max_bi2_{fac}"):
                    for _idx in range(len(BI2_R)):
                        st.session_state[f"r_bi2_{fac}_{_idx}_pmx"] = True
                    st.rerun()
                fac_total = 0
                n_label = t("pesquisas", "researches")
                with st.expander(f"BI2  —  {len(BI2_R)} {n_label}", expanded=True):
                    _rphdr()
                    for idx, item in enumerate(BI2_R):
                        fac_total += _rrow(item, f"r_bi2_{fac}_{idx}")
                bi2_fac_totals[fac] = fac_total
                st.metric(_FAC_NAMES[fac] + " — " + t("Pó BI2", "Dust BI2"), f"{fac_total:,}")

        bi2_res_total = sum(bi2_fac_totals.values())
        st.metric(t("Total Pó BI2 (todas as facções)", "Total Dust BI2 (all factions)"), f"{bi2_res_total:,}")
        res_totals["BI2"] = bi2_res_total

    # ─── Facção ───────────────────────────────────────────────────────────────────
    with res_tabs[2]:
        fac_st_fac = st.tabs([_FAC_NAMES[f] for f in _FACS])
        fac_fac_totals = {}
        for fi, fac in enumerate(_FACS):
            with fac_st_fac[fi]:
                _ff1, _ff2 = st.columns(2)
                if _ff1.button(t("↩ Zerar alvos", "↩ Reset targets"), key=f"rst_fac_{fac}"):
                    for _slc, _ in RESEARCH_TIER_SLICES:
                        for _idx in range(len(FAC_R[_slc])):
                            st.session_state[f"r_fac_{fac}_{_slc.start}_{_idx}_t"] = "0"
                    st.rerun()
                if _ff2.button(t("⬆ Máximo", "⬆ Max"), key=f"max_fac_{fac}"):
                    for _slc, _ in RESEARCH_TIER_SLICES:
                        for _idx in range(len(FAC_R[_slc])):
                            st.session_state[f"r_fac_{fac}_{_slc.start}_{_idx}_pmx"] = True
                    st.rerun()
                fac_total = 0
                for slc, tlabel in RESEARCH_TIER_SLICES:
                    pitems = FAC_R[slc]
                    n_label = t("pesquisas", "researches")
                    with st.expander(f"🟢 {tlabel}  —  {len(pitems)} {n_label}", expanded=(slc.start == 0)):
                        _rphdr()
                        for idx, item in enumerate(pitems):
                            fac_total += _rrow(item, f"r_fac_{fac}_{slc.start}_{idx}")
                fac_fac_totals[fac] = fac_total
                st.metric(_FAC_NAMES[fac] + " — " + t("Pó Facção", "Dust Faction"), f"{fac_total:,}")

        fac_res_total = sum(fac_fac_totals.values())
        st.metric(t("Total Pó Facção (todas)", "Total Dust Faction (all)"), f"{fac_res_total:,}")
        res_totals[t("Facção", "Faction")] = fac_res_total

    # ─── Awakening ────────────────────────────────────────────────────────────────
    with res_tabs[3]:
        _ac1, _ac2 = st.columns(2)
        if _ac1.button(t("↩ Zerar alvos Awakening", "↩ Reset Awakening targets"), key="rst_awk"):
            _reset_tree("r_awk_")
        if _ac2.button(t("⬆ Máximo Awakening", "⬆ Max Awakening"), key="max_awk"):
            _max_tiered("r_awk_", AWK_R)
        st.caption(t("Árvore única compartilhada por todas as facções.",
                     "Single tree shared across all factions."))
        awk_total = 0
        for slc, tlabel in RESEARCH_TIER_SLICES:
            pitems = AWK_R[slc]
            n_label = t("pesquisas", "researches")
            with st.expander(f"🟢 {tlabel}  —  {len(pitems)} {n_label}", expanded=(slc.start == 0)):
                _rphdr()
                for idx, item in enumerate(pitems):
                    awk_total += _rrow(item, f"r_awk_{slc.start}_{idx}")
        st.metric(t("Total Pó Awakening", "Total Dust Awakening"), f"{awk_total:,}")
        res_totals["Awakening"] = awk_total

    # ─── S2 ───────────────────────────────────────────────────────────────────────
    with res_tabs[4]:
        _s2c1, _s2c2 = st.columns(2)
        if _s2c1.button(t("↩ Zerar alvos S2", "↩ Reset S2 targets"), key="rst_s2"):
            _reset_tree("r_s2_")
        if _s2c2.button(t("⬆ Máximo S2", "⬆ Max S2"), key="max_s2"):
            _max_flat("r_s2_", S2_R)
        st.caption(t(
            "⚠️ Alguns níveis de S2 têm custos desconhecidos (dados incompletos) e são ignorados no cálculo.",
            "⚠️ Some S2 levels have unknown costs (incomplete data) and are excluded from the calculation."
        ))
        s2_total = 0
        n_label = t("pesquisas", "researches")
        with st.expander(f"S2  —  {len(S2_R)} {n_label}", expanded=True):
            _rphdr()
            for idx, item in enumerate(S2_R):
                s2_total += _rrow(item, f"r_s2_{idx}")
        st.metric(t("Total Pó S2", "Total Dust S2"), f"{s2_total:,}")
        res_totals["S2"] = s2_total

    # ─── S3 ───────────────────────────────────────────────────────────────────────
    with res_tabs[5]:
        _s3c1, _s3c2 = st.columns(2)
        if _s3c1.button(t("↩ Zerar alvos S3", "↩ Reset S3 targets"), key="rst_s3"):
            _reset_tree("r_s3_")
        if _s3c2.button(t("⬆ Máximo S3", "⬆ Max S3"), key="max_s3"):
            _max_flat("r_s3_", S3_R)
        s3_total = 0
        n_label = t("pesquisas", "researches")
        with st.expander(f"S3  —  {len(S3_R)} {n_label}", expanded=True):
            _rphdr()
            for idx, item in enumerate(S3_R):
                s3_total += _rrow(item, f"r_s3_{idx}")
        st.metric(t("Total Pó S3", "Total Dust S3"), f"{s3_total:,}")
        res_totals["S3"] = s3_total

    # ─── S4 ───────────────────────────────────────────────────────────────────────
    with res_tabs[6]:
        _s4c1, _s4c2 = st.columns(2)
        if _s4c1.button(t("↩ Zerar alvos S4", "↩ Reset S4 targets"), key="rst_s4"):
            _reset_tree("r_s4_")
        if _s4c2.button(t("⬆ Máximo S4", "⬆ Max S4"), key="max_s4"):
            _max_flat("r_s4_", S4_R)
        s4_total = 0
        n_label = t("pesquisas", "researches")
        with st.expander(f"S4  —  {len(S4_R)} {n_label}", expanded=True):
            _rphdr()
            for idx, item in enumerate(S4_R):
                s4_total += _rrow(item, f"r_s4_{idx}")
        st.metric(t("Total Pó S4", "Total Dust S4"), f"{s4_total:,}")
        res_totals["S4"] = s4_total

    total_dust_research = sum(res_totals.values())

    # ── ROADMAP DE PESQUISAS ───────────────────────────────────────────────────────
    st.divider()
    st.subheader("🗺️ " + t("Roadmap de Pesquisas", "Research Roadmap"))
    st.caption(t(
        "Visão consolidada do custo de pó por árvore de pesquisa.",
        "Consolidated dust cost view per research tree."
    ))

    rdmap_rows = []
    for tree_key, tree_cost in res_totals.items():
        rdmap_rows.append({
            t("Árvore", "Tree"): tree_key,
            t("Pó Necessário", "Dust Needed"): tree_cost,
        })
    rdmap_rows.append({
        t("Árvore", "Tree"): "─── TOTAL ───",
        t("Pó Necessário", "Dust Needed"): total_dust_research,
    })

    df_rdmap = pd.DataFrame(rdmap_rows)
    st.dataframe(
        df_rdmap,
        use_container_width=True,
        hide_index=True,
        column_config={
            t("Pó Necessário", "Dust Needed"): st.column_config.NumberColumn(format="%d"),
        },
    )

    # Progress bars per tree
    for tree_key, tree_cost in list(res_totals.items()):
        if tree_cost > 0 and total_dust_research > 0:
            pct = tree_cost / total_dust_research
            st.caption(f"{tree_key}  {tree_cost:,} pó  ({pct:.0%})")
            st.progress(pct)

    # ── RESUMO GERAL ───────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("📊 " + t("Resumo", "Summary"))

    # --- Inputs de conversão ---
    _cc1, _cc2 = st.columns([1, 2])
    with _cc1:
        conv_rate = st.number_input(
            t("Taxa: 1 DE = X pó", "Rate: 1 DE = X Dust"),
            min_value=0.0, value=0.0, step=0.1, format="%.2f",
            help=t("Se 0, conversão não é considerada.", "If 0, conversion is ignored."),
            key="conv_rate",
        )
    _prio_bld = t("Construções primeiro", "Buildings first")
    _prio_res = t("Pesquisa primeiro",    "Research first")
    with _cc2:
        priority = st.radio(
            t("Prioridade da conversão", "Conversion priority"),
            [_prio_bld, _prio_res],
            horizontal=True,
            key="conv_priority",
            disabled=(conv_rate == 0.0),
        )

    total_de_needed  = castle_total_de + other_de_total + bi_total
    de_balance       = de_eff - total_de_needed
    dust_balance_raw = dust_eff - total_dust_research

    # --- Lógica de conversão ---
    de_for_conv    = 0
    converted_dust = 0

    if conv_rate > 0:
        if priority == _prio_bld:
            # Gasta DE em construções primeiro; converte a sobra
            de_surplus     = max(0, de_balance)
            de_for_conv    = de_surplus
            converted_dust = int(de_surplus * conv_rate)
        else:
            # Pesquisa primeiro: converte só o suficiente para cobrir déficit de pó
            dust_deficit = max(0, -dust_balance_raw)
            if dust_deficit > 0:
                de_for_conv    = math.ceil(dust_deficit / conv_rate)
                converted_dust = int(de_for_conv * conv_rate)

    eff_dust_balance = dust_balance_raw + converted_dust
    eff_de_balance   = (de_balance if priority == _prio_bld
                        else de_eff - total_de_needed - de_for_conv)

    # --- Métricas DE ---
    _h1, _h2 = st.columns([1, 20])
    with _h1:
        _show_de()
    with _h2:
        st.markdown(f"**{t('Essência de Dragão (DE)', 'Dragon Essence (DE)')}**")
    _de1, _de2, _de3 = st.columns(3)
    _de1.metric(t("DE Disponível",  "Available DE"),  f"{de_eff:,}")
    _de2.metric(t("DE Necessário",  "Required DE"),   f"{total_de_needed:,}")
    _de3.metric(
        t("Saldo DE", "DE Balance"), f"{de_balance:,}",
        delta=f"{de_balance:+,}",
        delta_color="normal" if de_balance >= 0 else "inverse",
    )

    # --- Métricas Pó ---
    _h3, _h4 = st.columns([1, 20])
    with _h3:
        _show_dust()
    with _h4:
        st.markdown(f"**{t('Pó de Dragão', 'Dragon Dust')}**")
    _du1, _du2, _du3 = st.columns(3)
    _du1.metric(t("Pó Disponível",  "Available Dust"),  f"{dust_eff:,}")
    _du2.metric(t("Pó Necessário",  "Required Dust"),   f"{total_dust_research:,}")
    _du3.metric(
        t("Saldo Pó", "Dust Balance"), f"{dust_balance_raw:,}",
        delta=f"{dust_balance_raw:+,}",
        delta_color="normal" if dust_balance_raw >= 0 else "inverse",
    )

    # --- Seção de Conversão ---
    if conv_rate > 0:
        st.markdown("---")
        st.markdown(f"**🔄 {t('Projeção com Conversão DE → Pó', 'Projection with DE → Dust Conversion')}**")
        _cv1, _cv2, _cv3 = st.columns(3)
        _cv1.metric(t("DE convertido", "DE converted"), f"{de_for_conv:,}")
        _cv2.metric(t("Pó obtido",     "Dust gained"),  f"{converted_dust:,}")
        _cv3.metric(
            t("Saldo Pó efetivo", "Effective Dust Balance"), f"{eff_dust_balance:,}",
            delta=f"{eff_dust_balance:+,}",
            delta_color="normal" if eff_dust_balance >= 0 else "inverse",
        )
        if priority == _prio_res and de_for_conv > 0:
            _cvd1, _cvd2 = st.columns(2)
            _cvd1.metric(
                t("DE para construções (após conv.)", "DE for buildings (after conv.)"),
                f"{de_eff - de_for_conv:,}",
            )
            _cvd2.metric(
                t("Saldo DE efetivo", "Effective DE Balance"), f"{eff_de_balance:,}",
                delta=f"{eff_de_balance:+,}",
                delta_color="normal" if eff_de_balance >= 0 else "inverse",
            )

    # --- Breakdowns ---
    with st.expander(t("Detalhes do custo DE", "DE cost breakdown")):
        de_detail = [
            {t("Origem", "Source"): t("Castelo + Pré-requisitos", "Castle + Prerequisites"),
             "DE": f"{castle_total_de:,}"},
            {t("Origem", "Source"): t("Outras Construções", "Other Buildings"),
             "DE": f"{other_de_total:,}"},
            {t("Origem", "Source"): t("Instituto de Brilhantismo", "Brilliance Institute"),
             "DE": f"{bi_total:,}"},
            {t("Origem", "Source"): "TOTAL",
             "DE": f"{total_de_needed:,}"},
        ]
        st.dataframe(pd.DataFrame(de_detail), use_container_width=True, hide_index=True)

    with st.expander(t("Detalhes do custo Pó", "Dust cost breakdown")):
        dust_detail = [
            {t("Árvore", "Tree"): k, t("Pó", "Dust"): f"{v:,}"}
            for k, v in res_totals.items()
        ]
        dust_detail.append({t("Árvore", "Tree"): "TOTAL", t("Pó", "Dust"): f"{total_dust_research:,}"})
        st.dataframe(pd.DataFrame(dust_detail), use_container_width=True, hide_index=True)

    # --- Alertas ---
    if de_balance < 0:
        st.error(
            t(f"❌ Faltam **{abs(de_balance):,} DE** para completar todas as construções selecionadas.",
              f"❌ You need **{abs(de_balance):,} more DE** to complete all selected buildings.")
        )
    elif total_de_needed > 0:
        st.success(
            t(f"✅ DE suficiente. Saldo: **{de_balance:,} DE**.",
              f"✅ Enough DE. Balance: **{de_balance:,} DE**.")
        )

    _eff_dust = eff_dust_balance if conv_rate > 0 else dust_balance_raw
    if _eff_dust < 0:
        if conv_rate > 0:
            st.error(
                t(f"❌ Mesmo com conversão, faltam **{abs(_eff_dust):,} pó** para todas as pesquisas.",
                  f"❌ Even with conversion, you need **{abs(_eff_dust):,} more Dust** for all research.")
            )
        else:
            st.error(
                t(f"❌ Faltam **{abs(_eff_dust):,} pó** para completar todas as pesquisas selecionadas.",
                  f"❌ You need **{abs(_eff_dust):,} more Dust** to complete all selected research.")
            )
    elif total_dust_research > 0:
        if conv_rate > 0 and converted_dust > 0:
            st.success(
                t(f"✅ Pó suficiente (com conversão). Saldo efetivo: **{_eff_dust:,} pó**.",
                  f"✅ Enough Dust (with conversion). Effective balance: **{_eff_dust:,} Dust**.")
            )
        else:
            st.success(
                t(f"✅ Pó suficiente. Saldo: **{_eff_dust:,} pó**.",
                  f"✅ Enough Dust. Balance: **{_eff_dust:,} Dust**.")
            )

    if conv_rate > 0 and priority == _prio_res and eff_de_balance < 0:
        st.warning(
            t(f"⚠️ Priorizando pesquisa, faltam **{abs(eff_de_balance):,} DE** para construções.",
              f"⚠️ Prioritizing research leaves **{abs(eff_de_balance):,} DE** short for buildings.")
        )

with tab_help:
    _hi1, _hi2 = st.tabs([
        "📖 " + t("Como usar", "How to use"),
        "📊 " + t("Referência de dados", "Data reference"),
    ])

    with _hi1:
        st.markdown(t(
            """
### Planejador DE & Pó — Como usar

**Recursos**
- **Essência de Dragão (DE)**: recurso primário para construções
- **Pó de Dragão**: recurso necessário para pesquisa
- **Conversão DE→Pó**: 1:1 — use para completar pesquisa com excesso de DE (irreversível)

**1. Inventário de Recursos**
Informe quanto de DE e Pó você tem disponível.

**2. Construções (Buildings)**
Selecione para cada construção o nível atual (**de**) e o nível alvo (**para**).
O custo em DE é calculado automaticamente.

**3. Pesquisa**
Configure os níveis atuais e alvos para:
- **BI (Batalha Instância)**: pesquisa de batalha por facção
- **Facção**: árvore de pesquisa por facção
- **Despertar (Awakening)**: pesquisa de despertar de heróis
- **S2 / S3 / S4**: pesquisas de servidor de temporada

**4. Resultados**
Os totais de DE e Pó necessários aparecem nas abas de resultado.
Use **"Marcar tudo até o máx."** para selecionar todos os níveis máximos de uma vez.
""",
            """
### DE & Dust Planner — How to use

**Resources**
- **Dragon Essence (DE)**: primary resource for buildings
- **Dragon Dust**: resource needed for research
- **Convert DE→Dust**: 1:1 — use to complete research with excess DE (irreversible)

**1. Resource Inventory**
Enter how much DE and Dust you have available.

**2. Buildings**
Select the current (**from**) and target (**to**) level for each building.
The DE cost is calculated automatically.

**3. Research**
Set current and target levels for:
- **BI (Battle Instance)**: battle research by faction
- **Faction**: faction research tree
- **Awakening**: hero awakening research
- **S2 / S3 / S4**: season server research trees

**4. Results**
Total DE and Dust needed appear in the result tabs.
Use **"Mark all to max"** to select all maximum levels at once.
""",
        ))

    with _hi2:
        st.subheader(t("🏗️ Custo por Nível (Construções)", "🏗️ Building Cost per Level"))
        st.caption(t(
            "Custo em DE para avançar um nível em cada tipo de construção.",
            "DE cost to advance one level for each building type.",
        ))
        _b_rows = []
        for _bk, _bdata in BUILDINGS.items():
            for _lv in range(1, 7):
                _cost = de_cost_bar(_bk, _lv - 1, _lv)
                if _cost > 0:
                    _b_rows.append({
                        t("Construção", "Building"): _bk,
                        t("Nível", "Level"): f"B{_lv-1} → B{_lv}",
                        "DE": f"{_cost:,}",
                    })
        if _b_rows:
            import pandas as _pd2
            st.dataframe(_pd2.DataFrame(_b_rows), use_container_width=True, hide_index=True, height=300)

