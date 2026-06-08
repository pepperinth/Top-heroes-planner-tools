import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from relic_optimizer import compute_route, idx_to_star_leg, star_leg_to_idx, shards_needed

inv = {
    'universal_shards': 487,
    'relics': {
        "Duke's Signet Ring":   {'star_idx': star_leg_to_idx('R2','3/5'), 'specific_shards': 108, 'can_use': True},
        'Eternal Wings':        {'star_idx': star_leg_to_idx('R2','3/5'), 'specific_shards': 92,  'can_use': True},
        'Frost Diadem':         {'star_idx': star_leg_to_idx('Y4','3/5'), 'specific_shards': 48,  'can_use': True},
        'Royalty':              {'star_idx': star_leg_to_idx('Y5','3/5'), 'specific_shards': 75,  'can_use': True},
        'War Flag':             {'star_idx': star_leg_to_idx('Y5','5/5'), 'specific_shards': 102, 'can_use': True},
        'Scale of Injustice':   {'star_idx': star_leg_to_idx('P2','5/5'), 'specific_shards': 68,  'can_use': True},
        'Mighty Gold':          {'star_idx': star_leg_to_idx('Y5','5/5'), 'specific_shards': 123, 'can_use': True},
        'Persecution':          {'star_idx': star_leg_to_idx('P2','5/5'), 'specific_shards': 56,  'can_use': True},
        'Anti-Magic Handcuffs': {'star_idx': 0, 'specific_shards': 0, 'can_use': True},
        'Moonstone':            {'star_idx': 0, 'specific_shards': 0, 'can_use': True},
        'Thunder Judgment':     {'star_idx': 0, 'specific_shards': 42, 'can_use': True},
        'Dragonheart':          {'star_idx': star_leg_to_idx('R5','4/5'), 'specific_shards': 39, 'can_use': True},
        'Dragonbone Amulet':    {'star_idx': 0, 'specific_shards': 105, 'can_use': True},
        'Petrification Staff':  {'star_idx': 0, 'specific_shards': 0, 'can_use': True},
        'Soul Guard Orb':       {'star_idx': 0, 'specific_shards': 0, 'can_use': True},
        'Feather of the Pact':  {'star_idx': 0, 'specific_shards': 0, 'can_use': True},
        'Vineborne Bow':        {'star_idx': 0, 'specific_shards': 0, 'can_use': True},
        'Undefeated Crown':     {'star_idx': 0, 'specific_shards': 0, 'can_use': True},
        'Sacred Scroll':        {'star_idx': 0, 'specific_shards': 0, 'can_use': True},
    },
    'config': {
        'target_set': 'Horde', 'target_relic': '',
        'priority': ['Thunder Judgment','Dragonheart','Dragonbone Amulet'],
        'inter1': 'Persecution', 'inter2': 'Scale of Injustice',
        'target_level': star_leg_to_idx('P5','5/5'), 'hammers_avail': 7,
    }
}
