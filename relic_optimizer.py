"""
Relic Calculator v2 — Optimization Engine
==========================================
Chain-routing model: each universal relic donates its own specific shards
to a chain that accumulates star levels before reaching the target.

Usage:
    py relic_optimizer.py
    py relic_optimizer.py "path/to/Relic_Calculator_v2.xlsx"

Requires:
    pip install openpyxl
"""

import sys
import copy
from itertools import combinations, permutations
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# ── Star level data ────────────────────────────────────────────────────────────
CUMUL = [
    0, 2, 4, 6, 8, 10, 14, 18, 22, 26, 30, 34, 38, 42, 46, 50, 58, 66,
    74, 82, 90, 98, 106, 114, 122, 130, 142, 154, 166, 178, 190, 202,
    214, 226, 238, 250, 266, 282, 298, 314, 330, 346, 362, 378, 394, 410,
    426, 442, 458, 474, 490, 510, 530, 550, 570, 590, 610, 630, 650, 670,
    690, 716, 742, 768, 794, 820, 848, 876, 904, 932, 960, 988, 1016,
    1044, 1072, 1100, 1128, 1156, 1184, 1212, 1240, 1268, 1296, 1324,
    1352, 1380, 1408, 1436, 1464, 1492, 1520, 1548, 1576, 1604, 1632,
    1660, 1688, 1716, 1744, 1772, 1800,
]

STAR_OPTIONS = [
    "0★",
    "Y★1","Y★2","Y★3","Y★4","Y★5",
    "R★1","R★2","R★3","R★4","R★5",
    "P★1","P★2","P★3","P★4","P★5",
    "B★1","B★2","B★3","B★4","B★5",
]

FULL_LABELS = ["0★ (0/5)"]
for _t in ["Y","R","P","B"]:
    for _s in range(1, 6):
        for _l in range(1, 6):
            FULL_LABELS.append(f"{_t}★{_s} ({_l}/5)")


def star_leg_to_idx(star: str, leg) -> int:
    star = str(star).strip()
    if star in ("0★", "", "—"):
        return 0
    try:
        star_pos = STAR_OPTIONS.index(star)
    except ValueError:
        return 0
    leg_num = int(str(leg).split("/")[0]) if leg and str(leg) not in ("", "—") else 1
    return (star_pos - 1) * 5 + leg_num


def idx_to_star_leg(idx: int) -> tuple:
    if idx <= 0:
        return "0★", "0/5"
    star_num = (idx - 1) // 5
    leg_num  = (idx - 1) % 5 + 1
    return STAR_OPTIONS[star_num + 1], f"{leg_num}/5"


def shards_needed(from_idx: int, to_idx: int) -> int:
    if to_idx <= from_idx:
        return 0
    return CUMUL[to_idx] - CUMUL[from_idx]


def max_level_reachable(current: int, shards: int) -> int:
    best = current
    for lv in range(current + 1, 101):
        if shards_needed(current, lv) <= shards:
            best = lv
        else:
            break
    return best


# ── Relic definitions ──────────────────────────────────────────────────────────
UNIVERSAL_RELICS = [
    "Duke's Signet Ring", "Eternal Wings", "Frost Diadem", "Royalty",
    "War Flag", "Scale of Injustice", "Mighty Gold",
    "Persecution", "Anti-Magic Handcuffs", "Moonstone",
]
PREFERRED_INTER = ["Duke's Signet Ring", "Eternal Wings"]
SETS = {
    "League": ["Petrification Staff", "Soul Guard Orb", "Feather of the Pact"],
    "Horde":  ["Thunder Judgment", "Dragonheart", "Dragonbone Amulet"],
    "Nature": ["Vineborne Bow", "Undefeated Crown", "Sacred Scroll"],
}
ALL_SET_RELICS = [r for relics in SETS.values() for r in relics]
ALL_RELICS     = UNIVERSAL_RELICS + ALL_SET_RELICS

RELIC_NAME_PT = {
    # Universais
    "Duke's Signet Ring":   "Anel Sinete do Duque",
    "Eternal Wings":        "Asas Eternas",
    "Frost Diadem":         "Diadema de Gelo",
    "Royalty":              "Realeza",
    "War Flag":             "Bandeira de Guerra",
    "Scale of Injustice":   "Balança da Injustiça",
    "Mighty Gold":          "Ouro Poderoso",
    "Persecution":          "Perseguição",
    "Anti-Magic Handcuffs": "Algemas Anti-Magia",
    "Moonstone":            "Pedra da Lua",
    # Set — Liga
    "Petrification Staff":  "Cajado de Petrificação",
    "Soul Guard Orb":       "Orbe Guardião da Alma",
    "Feather of the Pact":  "Pena do Pacto",
    # Set — Horda
    "Thunder Judgment":     "Julgamento do Trovão",
    "Dragonheart":          "Coração de Dragão",
    "Dragonbone Amulet":    "Amuleto de Osso de Dragão",
    # Set — Natureza
    "Vineborne Bow":        "Arco da Videira",
    "Undefeated Crown":     "Coroa Invicta",
    "Sacred Scroll":        "Pergaminho Sagrado",
}


# ── Read inventory ─────────────────────────────────────────────────────────────
def read_inventory(filepath: str) -> dict:
    wb      = openpyxl.load_workbook(filepath, data_only=True)
    ws_inv  = wb["📦 Inventory"]
    ws_calc = wb["⚜️ Relic Calculator"]

    universal_shards = int(ws_inv["B3"].value or 0)

    relics = {}
    for row in ws_inv.iter_rows(min_row=7, values_only=True):
        raw_name = str(row[1] or "").strip().lstrip("⭐").strip()
        if raw_name not in ALL_RELICS:
            continue
        star    = str(row[3] or "0★").strip()
        leg_raw = row[4]
        leg_str = str(leg_raw or "—").strip()
        idx     = star_leg_to_idx(star, leg_str)
        spec    = int(row[5] or 0)
        can_use = str(row[6] or "No").strip() == "Yes"
        relics[raw_name] = {
            "star_idx":        idx,
            "specific_shards": spec,
            "can_use":         can_use,
        }

    target_set   = str(ws_calc["C2"].value or "Horde").strip()
    target_relic = str(ws_calc["C3"].value or "").strip()
    priority     = [
        str(ws_calc["E5"].value or "").strip(),
        str(ws_calc["F5"].value or "").strip(),
        str(ws_calc["G5"].value or "").strip(),
    ]
    inter1        = str(ws_calc["C6"].value or PREFERRED_INTER[0]).strip()
    inter2        = str(ws_calc["F6"].value or "").strip()
    tgt_star      = str(ws_calc["C8"].value or "P★5").strip()
    tgt_leg       = str(ws_calc["E8"].value or "5/5").strip()
    target_level  = star_leg_to_idx(tgt_star, tgt_leg)
    hammers_avail = int(ws_calc["C9"].value or 0)

    return {
        "universal_shards": universal_shards,
        "relics":           relics,
        "config": {
            "target_set":    target_set,
            "target_relic":  target_relic,
            "priority":      priority,
            "inter1":        inter1,
            "inter2":        inter2,
            "target_level":  target_level,
            "hammers_avail": hammers_avail,
        },
    }


# ── Chain development functions ────────────────────────────────────────────────

def chain_develop(from_level: int, specific_shards: int, universal_avail: int) -> tuple:
    """
    Relay relic development.  Add the minimum universals needed so that ALL
    specific_shards are consumed before the next hammer swap.

    Finds the first level boundary whose shard cost >= specific_shards, then
    tops up with universals.  Falls back to best-effort if universals are short.

    Returns (achieved_level, sp_used, u_used).
    """
    if specific_shards <= 0 or from_level >= 100:
        return from_level, 0, 0

    from_cumul = CUMUL[from_level]

    for lv in range(from_level + 1, 101):
        cost = CUMUL[lv] - from_cumul
        if cost >= specific_shards:
            u_needed = cost - specific_shards
            if u_needed <= universal_avail:
                return lv, specific_shards, u_needed
            break  # cannot afford even this first boundary → best-effort

    # Best-effort: spend all specific + available universals
    total = specific_shards + universal_avail
    best  = from_level
    for lv in range(from_level + 1, 101):
        if CUMUL[lv] - from_cumul <= total:
            best = lv
        else:
            break
    if best == from_level:
        return from_level, 0, 0
    cost_best = CUMUL[best] - from_cumul
    sp_used   = min(specific_shards, cost_best)
    u_used    = cost_best - sp_used
    return best, sp_used, u_used


def develop_final(from_level: int, specific_shards: int, universal_budget: int,
                  cap: int = 100) -> tuple:
    """
    Target development: spend specific_shards then universals up to `cap` level.
    Capping at the target goal saves universals for other targets in the chain.

    Returns (achieved_level, sp_used, u_used).
    """
    if from_level >= cap or from_level >= 100:
        return from_level, 0, 0
    total      = specific_shards + universal_budget
    if total <= 0:
        return from_level, 0, 0
    best       = from_level
    from_cumul = CUMUL[from_level]
    for lv in range(from_level + 1, min(cap, 100) + 1):
        if CUMUL[lv] - from_cumul <= total:
            best = lv
        else:
            break
    if best == from_level:
        return from_level, 0, 0
    cost    = CUMUL[best] - from_cumul
    sp_used = min(specific_shards, cost)
    u_used  = cost - sp_used
    return best, sp_used, u_used


# ── Chain simulation ───────────────────────────────────────────────────────────

def simulate_chain(
    seed_name: str, seed_level: int,
    relay_specs: list,          # [(name, orig_level, specific_shards), ...]
    target_name: str, target_orig_level: int, target_specific: int,
    universal_pool: int,
    target_goal: int = 100,
) -> tuple:
    """
    Simulate: seed -> relay_specs[0] -> ... -> relay_specs[-1] -> target.

    Each arrow is a Miracle Hammer swap (1 hammer each).
    After every swap the receiving relic develops:
      - relays  : chain_develop  (exhaust specific shards, min universals)
      - target  : develop_final  (use all remaining universals)

    Returns (final_target_level, u_total_used, steps_list).
    """
    current_level   = seed_level
    current_carrier = seed_name
    remaining_u     = universal_pool
    steps           = []

    for (name, orig_level, specific) in relay_specs:
        # Hammer swap
        steps.append({
            "type":     "swap",
            "relic_a":  current_carrier, "a_from": current_level,  "a_to": orig_level,
            "relic_b":  name,            "b_from": orig_level,     "b_to": current_level,
        })
        incoming        = current_level
        current_carrier = name

        # Relay develops (exhaust specific shards)
        achieved, sp_used, u_used = chain_develop(incoming, specific, remaining_u)
        steps.append({
            "type":    "develop",
            "relic":   name,
            "from":    incoming, "to":      achieved,
            "sp_used": sp_used,  "u_used":  u_used,
        })
        remaining_u   -= u_used
        current_level  = achieved

    # Final hammer swap to target
    steps.append({
        "type":    "swap",
        "relic_a": current_carrier, "a_from": current_level,       "a_to": target_orig_level,
        "relic_b": target_name,     "b_from": target_orig_level,   "b_to": current_level,
    })
    incoming_target = current_level

    # Target develops up to target_goal (saves excess universals for other chains)
    achieved, sp_used, u_used = develop_final(incoming_target, target_specific, remaining_u,
                                               cap=target_goal)
    steps.append({
        "type":    "develop",
        "relic":   target_name,
        "from":    incoming_target, "to":      achieved,
        "sp_used": sp_used,         "u_used":  u_used,
    })
    remaining_u -= u_used

    return achieved, universal_pool - remaining_u, steps


# ── Per-target chain optimizer ─────────────────────────────────────────────────

def best_chain_for_target(
    seed_name: str, seed_level: int,
    mandatory_relay,        # (name, orig_level, specific) or None
    other_relays: list,     # [(name, orig_level, specific), ...]
    n_relays: int,          # relay slots = hammers - 1
    target_name: str, target_orig_level: int, target_specific: int,
    universal_pool: int,
    target_goal: int = 100,
) -> tuple:
    """
    Try all permutations of (mandatory + best optional) relays.
    Returns (best_level, best_u_used, best_relay_order, best_steps).
    """
    best_lv    = -1
    best_u     = float("inf")
    best_order = None
    best_steps = None

    n_mandatory = 1 if mandatory_relay else 0
    n_optional  = max(0, min(n_relays - n_mandatory, len(other_relays)))

    def evaluate(relay_order):
        nonlocal best_lv, best_u, best_order, best_steps
        lv, u, steps = simulate_chain(
            seed_name, seed_level, relay_order,
            target_name, target_orig_level, target_specific,
            universal_pool, target_goal,
        )
        if lv > best_lv or (lv == best_lv and u < best_u):
            best_lv, best_u, best_order, best_steps = lv, u, list(relay_order), steps

    # n_relays == 0: seed swaps directly with target (no relay development)
    if n_relays == 0:
        evaluate([])
        return best_lv, best_u, best_order, best_steps

    for opt_combo in combinations(other_relays, n_optional):
        relays = ([mandatory_relay] if mandatory_relay else []) + list(opt_combo)
        for perm in permutations(relays):
            evaluate(list(perm))

    # Fallback: try fewer optionals if nothing worked
    if best_lv < 0:
        for fewer in range(n_optional - 1, -1, -1):
            for opt_combo in combinations(other_relays, fewer):
                relays = ([mandatory_relay] if mandatory_relay else []) + list(opt_combo)
                for perm in permutations(relays):
                    evaluate(list(perm))
            if best_lv >= 0:
                break

    return best_lv, best_u, best_order, best_steps


# ── Route scoring ──────────────────────────────────────────────────────────────

def score_route(final_levels: dict, targets: list, target_goal: int) -> int:
    """
    Higher score = better route.
    Each target contributes min(level, target_goal) × priority_weight.
    Capping at target_goal means over-developing one relic (past goal) gives
    no advantage over using those universals for a lower-priority target.
    """
    score = 0
    n = len(targets)
    for i, t in enumerate(targets):
        lv = min(final_levels.get(t, 0), target_goal)
        w  = (n - i)
        score += w * lv
    return score


# ── Main route computation ─────────────────────────────────────────────────────

def _gen_all_splits(total: int, n: int):
    """All non-negative integer tuples of length n that sum to total."""
    if n == 1:
        yield (total,)
        return
    for h in range(0, total + 1):
        for rest in _gen_all_splits(total - h, n - 1):
            yield (h,) + rest


def _mandatory_assignments(mandatory_names: list, split: tuple):
    """
    Yield every injective mapping  {target_idx: mandatory_name}
    where mandatory_names are distributed across DIFFERENT chains
    and every assigned chain has split[idx] >= 2.

    Mandatory relics may land in ANY chain — inter1/inter2 are NOT
    forced to target[0]/target[1].  The optimizer finds the best fit.
    """
    n_mand     = len(mandatory_names)
    eligible   = [i for i, h in enumerate(split) if h >= 2]
    if len(eligible) < n_mand:
        return  # not enough chains with room for mandatory relays
    for perm in permutations(eligible, n_mand):
        yield dict(zip(perm, mandatory_names))


def compute_route(inv: dict) -> dict:
    cfg           = inv["config"]
    target_goal   = cfg["target_level"]
    hammers_avail = cfg["hammers_avail"]

    levels_init    = {r: inv["relics"].get(r, {}).get("star_idx",        0) for r in ALL_RELICS}
    specific_init  = {r: inv["relics"].get(r, {}).get("specific_shards", 0) for r in ALL_RELICS}
    can_use_init   = {r: inv["relics"].get(r, {}).get("can_use", True)      for r in ALL_RELICS}
    universal_init = inv["universal_shards"]

    # Mandatory relay names from user config
    inter1 = cfg["inter1"] if cfg["inter1"] in UNIVERSAL_RELICS else PREFERRED_INTER[0]
    inter2 = cfg["inter2"] if cfg["inter2"] in UNIVERSAL_RELICS else ""
    mandatory_names = [i for i in [inter1, inter2] if i and i in UNIVERSAL_RELICS]

    # Ordered targets (skip those already at goal)
    if cfg["target_set"] in SETS:
        set_relics = SETS[cfg["target_set"]]
        ordered    = [p for p in cfg["priority"] if p in set_relics]
        ordered   += [r for r in set_relics if r not in ordered]
        targets    = [r for r in ordered if levels_init.get(r, 0) < target_goal]
    elif cfg["target_relic"] and cfg["target_relic"] in ALL_RELICS:
        targets = ([cfg["target_relic"]]
                   if levels_init.get(cfg["target_relic"], 0) < target_goal else [])
    else:
        targets = []

    all_targets = targets

    if not targets:
        return {
            "steps": [], "final_levels": dict(levels_init),
            "final_specific": dict(specific_init),
            "hammers_used": 0, "universal_used": 0, "targets": all_targets,
            "suboptimal_note": "",
        }

    # Seeds: prefer high level + few specific shards (level donated, shards unused in seed role)
    # can_use=False relics are still eligible as seeds (they just donate level, no shards used).
    def seed_score(r):
        prefer = 1 if can_use_init.get(r, True) else 0
        return prefer * 1000 + levels_init.get(r, 0) * 10 - specific_init.get(r, 0)

    seed_pool  = sorted([r for r in UNIVERSAL_RELICS if r not in targets],
                        key=seed_score, reverse=True)

    # Relay pool: can_use=True relics first, can_use=False last (avoid but don't exclude).
    relay_pool = sorted(
        [r for r in UNIVERSAL_RELICS
         if specific_init.get(r, 0) > 0 and r not in targets],
        key=lambda r: (0 if can_use_init.get(r, True) else 1),
    )

    # User's explicit assignment: inter1 → target[0], inter2 → target[1]
    user_assignment = {i: mandatory_names[i]
                       for i in range(min(len(mandatory_names), len(targets)))}

    best_score        = -1
    best_result       = None
    user_assign_score = None   # score when using exactly the user's assignment

    def _evaluate_config(split, assignment):
        """
        Run chains for one (split, assignment) combination.
        assignment: {target_idx: mandatory_relay_name}
        Returns (score, result_dict) or (None, None) if invalid.
        """
        levels    = dict(levels_init)
        specific  = dict(specific_init)
        universal = universal_init
        all_steps = []
        used      = set()
        total_h   = 0
        total_u   = 0

        for t_idx, (target, h) in enumerate(zip(targets, split)):
            if h == 0:
                continue

            target_orig = levels[target]
            target_sp   = specific[target]

            # Which mandatory relay (if any) goes into this chain?
            mandatory_name = assignment.get(t_idx)
            mandatory_spec = None
            if mandatory_name and mandatory_name not in used:
                mandatory_spec = (mandatory_name,
                                  levels[mandatory_name],
                                  specific[mandatory_name])

            # Seed: highest-value available relic not already committed
            seed_name = None
            seed_lv   = 0
            for sc in seed_pool:
                if sc not in used and sc != target and sc != mandatory_name:
                    seed_name = sc
                    seed_lv   = levels[sc]
                    break
            if seed_name is None:
                return None, None

            # Exclude ALL mandatory relics from optional pool — each mandatory
            # must appear only in its own assigned chain, not as a free optional elsewhere.
            all_assigned_mandatories = set(assignment.values())
            other_relays = [
                (r, levels[r], specific[r])
                for r in relay_pool
                if (r not in used and r != seed_name
                    and r != target
                    and r not in all_assigned_mandatories
                    and specific.get(r, 0) > 0)
            ]

            lv, u, relay_order, steps = best_chain_for_target(
                seed_name, seed_lv,
                mandatory_spec,
                other_relays,
                h - 1,           # relay slots
                target, target_orig, target_sp,
                universal, target_goal,
            )
            if steps is None:
                return None, None

            all_steps += steps
            total_h   += h
            total_u   += u
            universal -= u
            used.add(seed_name)
            if mandatory_spec:
                used.add(mandatory_name)
            for (name, _, _) in (relay_order or []):
                used.add(name)

            for step in steps:
                if step["type"] == "swap":
                    levels[step["relic_a"]] = step["a_to"]
                    levels[step["relic_b"]] = step["b_to"]
                elif step["type"] == "develop":
                    levels[step["relic"]] = step["to"]
                    if step["relic"] in specific:
                        specific[step["relic"]] = max(
                            0, specific[step["relic"]] - step["sp_used"])

        sc = score_route(levels, targets, target_goal)
        result = {
            "steps":          all_steps,
            "final_levels":   levels,
            "final_specific": specific,
            "hammers_used":   total_h,
            "universal_used": total_u,
            "targets":        all_targets,
            "assignment":     dict(assignment),   # which mandatory → which chain
            "suboptimal_note": "",
        }
        return sc, result

    for split in _gen_all_splits(hammers_avail, len(targets)):
        for assignment in _mandatory_assignments(mandatory_names, split):
            sc, result = _evaluate_config(split, assignment)
            if result is None:
                continue

            # Track user's explicit assignment score
            if assignment == user_assignment:
                # Find the split that satisfies the user's inter1→target[0], inter2→target[1]
                user_assign_score = sc

            if sc > best_score or (sc == best_score and result["universal_used"] < best_result["universal_used"]):
                best_score  = sc
                best_result = result

    if best_result is None:
        return {
            "steps": [], "final_levels": dict(levels_init),
            "final_specific": dict(specific_init),
            "hammers_used": 0, "universal_used": 0, "targets": all_targets,
            "suboptimal_note": "",
        }

    # ── Post-process: spend ALL remaining resources (no hammer needed) ────────
    # 1. Spend remaining specific shards on every relic that still has some.
    # 2. Spend remaining universal shards on undeveloped targets (in priority order).
    # This ensures nothing is left on the table after the hammer chain.
    fl = best_result["final_levels"]
    fs = best_result["final_specific"]
    remaining_univ = universal_init - best_result["universal_used"]

    # Pass 1 — specific shards for all relics
    for relic in ALL_RELICS:
        sp = fs.get(relic, 0)
        if sp <= 0:
            continue
        cur = fl.get(relic, 0)
        if cur >= 100:
            continue
        new_lv = max_level_reachable(cur, sp)
        if new_lv > cur:
            sp_used = shards_needed(cur, new_lv)
            best_result["steps"].append({
                "type": "develop", "relic": relic,
                "from": cur, "to": new_lv,
                "sp_used": sp_used, "u_used": 0,
            })
            fl[relic] = new_lv
            fs[relic] = sp - sp_used

    # Pass 2 — universal shards on targets that haven't reached goal (in order)
    for relic in all_targets:
        if remaining_univ <= 0:
            break
        cur = fl.get(relic, 0)
        if cur >= target_goal:
            continue
        sp  = fs.get(relic, 0)
        cap = target_goal
        new_lv = max_level_reachable(cur, sp + remaining_univ)
        new_lv = min(new_lv, cap)
        if new_lv > cur:
            total_cost = shards_needed(cur, new_lv)
            sp_used  = min(sp, total_cost)
            u_used   = total_cost - sp_used
            best_result["steps"].append({
                "type": "develop", "relic": relic,
                "from": cur, "to": new_lv,
                "sp_used": sp_used, "u_used": u_used,
            })
            fl[relic]  = new_lv
            fs[relic]  = sp - sp_used
            remaining_univ -= u_used
            best_result["universal_used"] += u_used

    # Check if user's specified inter1/inter2 assignment was suboptimal
    if (user_assign_score is not None
            and user_assign_score < best_score
            and best_result["assignment"] != user_assignment):
        opt_lines = []
        for t_idx, name in best_result["assignment"].items():
            if t_idx < len(targets):
                opt_lines.append(f"  {name}  ->  chain for {targets[t_idx]}")
        best_result["suboptimal_note"] = (
            "NOTE: The inter1/inter2 assignment you specified is NOT the most efficient.\n"
            "Optimal assignment:\n" + "\n".join(opt_lines)
        )

    return best_result


# ── Write results back to xlsx ─────────────────────────────────────────────────

def write_results(filepath: str, route: dict, inv: dict):
    wb      = openpyxl.load_workbook(filepath)
    ws_calc = wb["⚜️ Relic Calculator"]

    thin  = Side(style="thin",   color="CCCCCC")
    med   = Side(style="medium", color="888888")
    def brd():   return Border(left=thin, right=thin, top=thin,  bottom=thin)
    def brd_m(): return Border(left=med,  right=med,  top=med,   bottom=med)
    def fl(h):   return PatternFill("solid", start_color=h, fgColor=h)
    def ca():    return Alignment(horizontal="center", vertical="center", wrap_text=True)
    def la():    return Alignment(horizontal="left",   vertical="center", wrap_text=True)

    target_level = inv["config"]["target_level"]

    def tier_dark(idx):
        if idx == 0:    return "0D1B2A"
        if idx <= 25:   return "B7950B"
        if idx <= 50:   return "922B21"
        if idx <= 75:   return "1A5276"
        return                 "212F3C"

    def tier_light(idx):
        if idx == 0:    return "EFEFEF"
        if idx <= 25:   return "FEF9E7"
        if idx <= 50:   return "FDEDEC"
        if idx <= 75:   return "EBF5FB"
        return                 "EAECEE"

    # ── State table ───────────────────────────────────────────────────────────
    for row in ws_calc.iter_rows(min_row=14, values_only=False):
        raw = str(row[1].value or "").strip().lstrip("⭐").strip()
        if raw not in ALL_RELICS:
            continue
        r         = row[0].row
        final_idx = route["final_levels"].get(raw, 0)
        final_sp  = route["final_specific"].get(raw, 0)
        orig_sp   = inv["relics"].get(raw, {}).get("specific_shards", 0)
        sp_used   = orig_sp - final_sp
        dark      = tier_dark(final_idx)
        light     = tier_light(final_idx)
        star, leg = idx_to_star_leg(final_idx)
        is_target = raw in route["targets"]
        is_inter  = raw in [inv["config"]["inter1"], inv["config"]["inter2"]]
        reached   = final_idx >= target_level

        for ci, val, extra_font, extra_fill in [
            (6, star,
             Font(name="Arial", color=dark, bold=True, size=9),
             fl(light)),
            (7, leg if final_idx > 0 else "—",
             Font(name="Arial", color=dark, size=9),
             fl(light)),
            (8, sp_used if sp_used > 0 else "—",
             Font(name="Arial", color="1A6B2A" if sp_used > 0 else "AAAAAA", size=9),
             fl(light)),
        ]:
            c = ws_calc.cell(r, ci)
            c.value = val; c.font = extra_font
            c.fill  = extra_fill; c.alignment = ca(); c.border = brd()

        c9 = ws_calc.cell(r, 9)
        if is_target and not reached:
            missing = shards_needed(final_idx, target_level)
            c9.value = f"-{missing}"
            c9.font  = Font(name="Arial", color="AA0000", bold=True, size=9)
        else:
            c9.value = "—"
            c9.font  = Font(name="Arial", color="AAAAAA", size=9)
        c9.fill = fl(light); c9.alignment = ca(); c9.border = brd()

        note = ""
        if is_target:
            note = "Target reached" if reached else "Target not reached"
        elif is_inter:
            note = "Used as chain relay"
        c10 = ws_calc.cell(r, 10)
        c10.value = note
        c10.font  = Font(name="Arial", size=8,
                         color="1A6B2A" if reached else "884400")
        c10.fill  = fl(light); c10.alignment = la(); c10.border = brd()

    # ── Route steps ───────────────────────────────────────────────────────────
    route_row = None
    for row in ws_calc.iter_rows(min_row=30, values_only=False):
        if str(row[0].value or "") == "Step":
            route_row = row[0].row + 1
            break

    if route_row:
        # Clear stale rows
        for clear_r in range(route_row, route_row + 200):
            row_empty = True
            for ci in range(1, 11):
                c = ws_calc.cell(clear_r, ci)
                if c.value is not None:
                    c.value = None
                    row_empty = False
            if clear_r > route_row + 10 and row_empty:
                break

        step_num = 1
        r        = route_row

        for step in route["steps"]:
            ws_calc.row_dimensions[r].height = 18

            if step["type"] == "swap":
                a_s, a_l = idx_to_star_leg(step["a_from"])
                b_s, b_l = idx_to_star_leg(step["b_to"])   # what relic_b becomes
                vals = [
                    "Hammer",
                    "Miracle Hammer SWAP",
                    f"{step['relic_a']}  <->  {step['relic_b']}",
                    f"{step['relic_a']}: {a_s}", a_l,
                    f"{step['relic_b']}: {b_s}", b_l,
                    "—", "—",
                    (f"{step['relic_b']} rises to {b_s} {b_l}"
                     f" | {step['relic_a']} drops to "
                     + " ".join(idx_to_star_leg(step["a_to"]))),
                ]
                bg_use = "FFF3E0"
                bold   = True
                color  = "8B4513"

            else:  # develop
                from_s, from_l = idx_to_star_leg(step["from"])
                to_s,   to_l   = idx_to_star_leg(step["to"])
                vals = [
                    step_num,
                    f"Develop  ->  {to_s} {to_l}",
                    step["relic"],
                    from_s, from_l,
                    to_s,   to_l,
                    step["sp_used"] if step["sp_used"] else "—",
                    step["u_used"]  if step["u_used"]  else "—",
                    "",
                ]
                step_num += 1
                bg_use = "F5F8FF" if step_num % 2 == 0 else "FFFFFF"
                bold   = False
                color  = "000000"

            for ci, val in enumerate(vals, 1):
                c = ws_calc.cell(r, ci)
                c.value     = val
                c.font      = Font(name="Arial", size=8, bold=bold, color=color)
                c.fill      = PatternFill("solid", start_color=bg_use, fgColor=bg_use)
                c.alignment = la() if ci in (2, 3, 10) else ca()
                c.border    = brd()
            r += 1

    # ── Summary ───────────────────────────────────────────────────────────────
    for row in ws_calc.iter_rows(min_row=50, values_only=False):
        if str(row[0].value or "").startswith("📊"):
            sr = row[0].row + 1
            for col, val in [
                (2, route["hammers_used"]),
                (4, route["universal_used"]),
                (6, route["hammers_used"]),
                (8, inv["config"]["hammers_avail"] - route["hammers_used"]),
            ]:
                c = ws_calc.cell(sr, col)
                c.value     = val
                c.font      = Font(name="Arial", color="1A6B2A", bold=True, size=11)
                c.fill      = PatternFill("solid", start_color="E6F4EA", fgColor="E6F4EA")
                c.alignment = ca()
                c.border    = brd_m()
            break

    wb.save(filepath)

    print(f"Route written to: {filepath}")
    print(f"  Targets:          {', '.join(route['targets'])}")
    develop_steps = [s for s in route["steps"] if s["type"] == "develop"]
    swap_steps    = [s for s in route["steps"] if s["type"] == "swap"]
    print(f"  Swaps (hammers):  {len(swap_steps)}")
    print(f"  Develop steps:    {len(develop_steps)}")
    print(f"  Hammers used:     {route['hammers_used']} / {inv['config']['hammers_avail']}")
    print(f"  Universal shards: {route['universal_used']} / {inv['universal_shards']}")
    if route.get("assignment"):
        targets_list = route["targets"]
        for t_idx, mname in sorted(route["assignment"].items()):
            if t_idx < len(targets_list):
                print(f"  {mname}  ->  {targets_list[t_idx]}")


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    filepath = sys.argv[1] if len(sys.argv) > 1 else "Relic_Calculator_v2.xlsx"

    print(f"Reading:  {filepath}")
    inv = read_inventory(filepath)
    cfg = inv["config"]
    tgt_s, tgt_l = idx_to_star_leg(cfg["target_level"])

    print(f"Target:   {cfg['target_set']}  ->  {tgt_s} {tgt_l}")
    print(f"Mandatory relays: {cfg['inter1']}"
          + (f"  +  {cfg['inter2']}" if cfg["inter2"] else ""))
    print(f"Hammers:  {cfg['hammers_avail']}")
    print(f"Universal shards: {inv['universal_shards']}")
    print()

    route = compute_route(inv)

    print("Per-target results:")
    for t in route["targets"]:
        orig  = inv["relics"].get(t, {}).get("star_idx", 0)
        final = route["final_levels"].get(t, orig)
        os_, ol = idx_to_star_leg(orig)
        fs,  fl = idx_to_star_leg(final)
        goal    = "GOAL REACHED" if final >= cfg["target_level"] else ""
        print(f"  {t}: {os_} {ol}  ->  {fs} {fl}  {goal}")
    print()

    if route.get("suboptimal_note"):
        print()
        print(route["suboptimal_note"])

    write_results(filepath, route, inv)

    import os
    os.startfile(os.path.abspath(filepath))
