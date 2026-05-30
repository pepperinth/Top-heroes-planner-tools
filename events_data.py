"""
events_data.py
==============
Central data source for the GameEvents Tracker module.
Contains all event definitions and pure calculation functions.
No Streamlit dependency — can be imported anywhere.
"""

# ══════════════════════════════════════════════════════════════════════════════
# EVENT DATA
# ══════════════════════════════════════════════════════════════════════════════
# Each task dict:
#   description    : str   — exact game text (EN)
#   description_pt : str   — Portuguese translation
#   pts_label      : str   — display label (x1, x15, x30…)
#   factor         : float — multiplier applied to raw quantity
#   divisor        : float — divisor applied to raw quantity (mutually exclusive with factor)
#   is_speedup     : bool  — True = Days/Hours/Minutes input; False = raw quantity
#
# Points formula:
#   is_speedup=False → points = quantity * factor   OR   quantity / divisor
#   is_speedup=True  → total_minutes = days*1440 + hours*60 + minutes
#                      points = total_minutes * factor

EVENTS = [
    {
        "name":    "Pet Ranking",
        "name_pt": "Ranking de Pets",
        "sheet":   "Pet_Ranking",
        "milestones": [500, 1000, 2500, 5000, 15000, 40000, 80000, 130000],
        "tasks": [
            {
                "description":    "Consume 10 Skill Book(s)",
                "description_pt": "Consumir 10 Livro(s) de Habilidade",
                "pts_label": "x1",
                "factor": 0.1,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Consume Pet Essence x1",
                "description_pt": "Consumir Essência de Pet x1",
                "pts_label": "x15",
                "factor": 15,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Consume 100 Pet Food",
                "description_pt": "Consumir 100 Comida de Pet",
                "pts_label": "x30",
                "factor": 0.3,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Use a Common pet for EXP or as promotion material",
                "description_pt": "Usar um pet Comum como EXP ou material de promoção",
                "pts_label": "x150",
                "factor": 150,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Use a Rare pet for EXP or as promotion material",
                "description_pt": "Usar um pet Raro como EXP ou material de promoção",
                "pts_label": "x900",
                "factor": 900,
                "divisor": None,
                "is_speedup": False,
            },
        ],
    },
    {
        "name":    "Relic Race",
        "name_pt": "Corrida de Relíquias",
        "sheet":   "Relic_Race",
        "milestones": [200, 500, 1000, 2000, 5000, 15000, 30000, 48000],
        "tasks": [
            {
                "description":    "Consume any 400 Magicite",
                "description_pt": "Consumir 400 Magicite (qualquer)",
                "pts_label": "x1",
                "factor": 0.0025,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Consume 2 Magic Core(s)",
                "description_pt": "Consumir 2 Núcleo(s) Mágico(s)",
                "pts_label": "x1",
                "factor": 0.5,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Consume 1 Scroll Seal(s)",
                "description_pt": "Consumir 1 Selo(s) de Pergaminho",
                "pts_label": "x30",
                "factor": 30,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Consume 1 Rare-rarity Relic Shard(s)",
                "description_pt": "Consumir 1 Fragmento(s) de Relíquia Raro",
                "pts_label": "x5",
                "factor": 5,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Consume 1 Epic-rarity Relic Shard(s)",
                "description_pt": "Consumir 1 Fragmento(s) de Relíquia Épico",
                "pts_label": "x25",
                "factor": 25,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Consume 1 Legendary-rarity Relic Shard(s)",
                "description_pt": "Consumir 1 Fragmento(s) de Relíquia Lendário",
                "pts_label": "x120",
                "factor": 120,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Consume 1 Arcane Crystal(s)",
                "description_pt": "Consumir 1 Cristal(is) Arcano(s)",
                "pts_label": "x12",
                "factor": 12,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Consume 2000 Magic Stone(s)",
                "description_pt": "Consumir 2000 Pedra(s) Mágica(s)",
                "pts_label": "x6",
                "factor": 0.003,
                "divisor": None,
                "is_speedup": False,
            },
        ],
    },
    {
        "name":    "Lord Gear Trial",
        "name_pt": "Desafio de Equipamento do Lorde",
        "sheet":   "Lord_Gear_Trial",
        "milestones": [200, 400, 1000, 2000, 6000, 16000, 32000, 50000],
        "tasks": [
            {
                "description":    "Use 100 Refined Metal",
                "description_pt": "Usar 100 Metal Refinado",
                "pts_label": "x10",
                "factor": 0.1,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Use 1 Magic Thread",
                "description_pt": "Usar 1 Fio Mágico",
                "pts_label": "x10",
                "factor": 10,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Use 1 Orichalcum",
                "description_pt": "Usar 1 Oricalco",
                "pts_label": "x15",
                "factor": 15,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Consume 1 Dragon Blood",
                "description_pt": "Consumir 1 Sangue de Dragão",
                "pts_label": "x60",
                "factor": 60,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Consume 1 Rare Troop Skin",
                "description_pt": "Consumir 1 Skin de Tropa Rara",
                "pts_label": "x30",
                "factor": 30,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Consume 1 Epic Troop Skin",
                "description_pt": "Consumir 1 Skin de Tropa Épica",
                "pts_label": "x300",
                "factor": 300,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Consume 1 Legendary Troop Skin",
                "description_pt": "Consumir 1 Skin de Tropa Lendária",
                "pts_label": "x3000",
                "factor": 3000,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Minimum 200 medals required per attempt",
                "description_pt": "Mínimo de 200 medalhas por tentativa",
                "pts_label": "x1",
                "factor": None,
                "divisor": 200,
                "is_speedup": False,
            },
            {
                "description":    "Complete 1 Bounty Quests",
                "description_pt": "Completar 1 Missão de Recompensa",
                "pts_label": "x50",
                "factor": 50,
                "divisor": None,
                "is_speedup": False,
            },
        ],
    },
    {
        "name":    "Construction of Territory",
        "name_pt": "Construção de Território",
        "sheet":   "Construction_Territory",
        "milestones": [1000, 2000, 5000, 10000, 30000, 80000, 160000, 250000],
        "tasks": [
            {
                "description":    "Use 1 Dragon Crystal Dust",
                "description_pt": "Usar 1 Pó de Cristal de Dragão",
                "pts_label": "x100",
                "factor": 100,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Use 1 Dragon Essence",
                "description_pt": "Usar 1 Essência de Dragão",
                "pts_label": "x100",
                "factor": 100,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Use 16000 Timber",
                "description_pt": "Usar 16000 Madeira",
                "pts_label": "x1",
                "factor": None,
                "divisor": 16000,
                "is_speedup": False,
            },
            {
                "description":    "Use 16000 Stones",
                "description_pt": "Usar 16000 Pedras",
                "pts_label": "x1",
                "factor": None,
                "divisor": 16000,
                "is_speedup": False,
            },
            {
                "description":    "Use 8000 Rubies",
                "description_pt": "Usar 8000 Rubis",
                "pts_label": "x1",
                "factor": None,
                "divisor": 8000,
                "is_speedup": False,
            },
            {
                "description":    "Use 1 min Construction Speed-up",
                "description_pt": "Usar 1 min de Aceleração de Construção",
                "pts_label": "x1",
                "factor": 1,
                "divisor": None,
                "is_speedup": True,
            },
            {
                "description":    "Use 1 min Research Speed-up",
                "description_pt": "Usar 1 min de Aceleração de Pesquisa",
                "pts_label": "x1",
                "factor": 1,
                "divisor": None,
                "is_speedup": True,
            },
            {
                "description":    "Complete 1 Bounty Quests",
                "description_pt": "Completar 1 Missão de Recompensa",
                "pts_label": "x50",
                "factor": 50,
                "divisor": None,
                "is_speedup": False,
            },
        ],
    },
    {
        "name":    "Hero Development",
        "name_pt": "Desenvolvimento de Heróis",
        "sheet":   "Hero_Development",
        "milestones": [1000, 2000, 5000, 10000, 30000, 80000, 160000, 250000],
        "tasks": [
            {
                "description":    "Consume any Legendary Hero Shard x1",
                "description_pt": "Consumir 1 Fragmento de Herói Lendário (qualquer)",
                "pts_label": "x100",
                "factor": 100,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Consume any Epic Hero Shard x1",
                "description_pt": "Consumir 1 Fragmento de Herói Épico (qualquer)",
                "pts_label": "x10",
                "factor": 10,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Use 1 Exclusive Gear Shard",
                "description_pt": "Usar 1 Fragmento de Equipamento Exclusivo",
                "pts_label": "x100",
                "factor": 100,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Use 1 Universal Exclusive Gear Shard",
                "description_pt": "Usar 1 Fragmento de Equipamento Exclusivo Universal",
                "pts_label": "x100",
                "factor": 100,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Consume 1 Soul Stone(s)",
                "description_pt": "Consumir 1 Pedra(s) de Alma",
                "pts_label": "x1500",
                "factor": 1500,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Consume 10 Skill Book(s)",
                "description_pt": "Consumir 10 Livro(s) de Habilidade",
                "pts_label": "x1",
                "factor": 0.1,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Cost 1 Meteoric Iron Core",
                "description_pt": "Gastar 1 Núcleo de Ferro Meteórico",
                "pts_label": "x100",
                "factor": 100,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Consume any 400 Magicite",
                "description_pt": "Consumir 400 Magicite (qualquer)",
                "pts_label": "x6",
                "factor": 0.015,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Consume 2 Magic Core(s)",
                "description_pt": "Consumir 2 Núcleo(s) Mágico(s)",
                "pts_label": "x6",
                "factor": 3,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Consume 1 Scroll Seal(s)",
                "description_pt": "Consumir 1 Selo(s) de Pergaminho",
                "pts_label": "x180",
                "factor": 180,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Consume any Mythic Hero Shard x1",
                "description_pt": "Consumir 1 Fragmento de Herói Mítico (qualquer)",
                "pts_label": "x100",
                "factor": 100,
                "divisor": None,
                "is_speedup": False,
            },
        ],
    },
    {
        "name":       "Decor Upgrade",
        "name_pt":    "Atualização de Decoração",
        "sheet":      "Decor_Upgrade",
        "milestones": [50, 100, 300, 500, 1500, 4000, 8000, 13000],
        "info_note": (
            "Decoration rarity rating bonus — "
            "Rare: +6 | Epic: +25 | Legendary: +100 | Mythic: +150. "
            "Each rating point = x3 event pts."
        ),
        "info_note_pt": (
            "Bônus de rating por raridade de decoração — "
            "Rara: +6 | Épica: +25 | Lendária: +100 | Mítica: +150. "
            "Cada ponto de rating = x3 pts de evento."
        ),
        "tasks": [
            {
                "description":    "Consumes 1 Castle Blueprint",
                "description_pt": "Consumir 1 Planta do Castelo",
                "pts_label": "x30",
                "factor": 30,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Consumes 1 Advanced Castle Badge",
                "description_pt": "Consumir 1 Emblema Avançado do Castelo",
                "pts_label": "x120",
                "factor": 120,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Consume 1 Heroic Spirit Shards",
                "description_pt": "Consumir 1 Fragmento de Espírito Heróico",
                "pts_label": "x10",
                "factor": 10,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Decor rating - Rare decoration (+6 rating each)",
                "description_pt": "Rating de Decoração - Rara (+6 rating cada)",
                "pts_label": "x18",
                "factor": 18,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Decor rating - Epic decoration (+25 rating each)",
                "description_pt": "Rating de Decoração - Épica (+25 rating cada)",
                "pts_label": "x75",
                "factor": 75,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Decor rating - Legendary decoration (+100 rating each)",
                "description_pt": "Rating de Decoração - Lendária (+100 rating cada)",
                "pts_label": "x300",
                "factor": 300,
                "divisor": None,
                "is_speedup": False,
            },
            {
                "description":    "Decor rating - Mythic decoration (+150 rating each)",
                "description_pt": "Rating de Decoração - Mítica (+150 rating cada)",
                "pts_label": "x450",
                "factor": 450,
                "divisor": None,
                "is_speedup": False,
            },
        ],
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# CALCULATION FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def calc_task_points(task: dict, quantity: float = 0,
                     days: int = 0, hours: int = 0, minutes: int = 0) -> float:
    if task["is_speedup"]:
        total_minutes = days * 1440 + hours * 60 + minutes
        return total_minutes * (task["factor"] or 1)
    else:
        if task["divisor"]:
            return quantity / task["divisor"]
        return quantity * (task["factor"] or 0)


def calc_event_total(event: dict, inputs: list) -> float:
    total = 0.0
    for task, inp in zip(event["tasks"], inputs):
        if task["is_speedup"]:
            total += calc_task_points(
                task,
                days=inp.get("days", 0),
                hours=inp.get("hours", 0),
                minutes=inp.get("minutes", 0),
            )
        else:
            total += calc_task_points(task, quantity=inp.get("quantity", 0))
    return total


def get_milestone_status(milestones: list, current_pts: float) -> list:
    result = []
    for ms in milestones:
        reached = current_pts >= ms
        needed  = max(0.0, ms - current_pts)
        result.append({"value": ms, "reached": reached, "needed": needed})
    return result


def get_event_by_name(name: str):
    for ev in EVENTS:
        if ev["name"] == name:
            return ev
    return None


def event_names() -> list:
    return [ev["name"] for ev in EVENTS]
