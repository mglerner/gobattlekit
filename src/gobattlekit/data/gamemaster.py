#!/usr/bin/env python

import math
from .fetcher import load_gamemaster, load_rankings

def get_moves():
    """Parse fast and charged moves from the gamemaster."""
    gm = load_gamemaster()
    fastmoves = {
        i['moveId']: i
        for i in gm['moves']
        if i['energyGain'] != 0
    }
    chargedmoves = {
        i['moveId']: i
        for i in gm['moves']
        if i['energyGain'] == 0
    }
    return fastmoves, chargedmoves

def get_rankings(league):
    """
    Get top 100 ranked Pokemon for a league, sorted best first.
    league is one of: 'great', 'ultra', 'master'
    """
    rankings = load_rankings(league)
    rankings.sort(key=lambda x: x['rating'], reverse=True)
    return rankings[:100]


def counters_to_charge(fast_move, charged_move, fastmoves, chargedmoves):
    """
    How many fast moves to fully charge a charged move?
    Returns an int, or the string 'more' if it would take more than 10.
    """
    if fast_move not in fastmoves:
        raise KeyError(f"Fast move not found: {fast_move}")
    if charged_move not in chargedmoves:
        raise KeyError(f"Charged move not found: {charged_move}")
    energy_per_fast = fastmoves[fast_move]['energyGain']
    energy_needed = chargedmoves[charged_move]['energy']
    result = int(math.ceil(energy_needed / energy_per_fast))
    return result if result <= 20 else 'more'

def charge_sequence(fast_move, charged_move, fastmoves, chargedmoves, num_charges=4):
    """
    Compute how many fast moves it takes to reach each of the first num_charges
    charge moves, accounting for energy carry-over.
    Returns a list of ints, e.g. [5, 4, 5, 4]
    """
    energy_per_fast = fastmoves[fast_move]['energyGain']
    energy_needed = chargedmoves[charged_move]['energy']
    
    sequence = []
    leftover = 0
    for _ in range(num_charges):
        needed = energy_needed - leftover
        count = int(math.ceil(needed / energy_per_fast))
        leftover = (count * energy_per_fast + leftover) - energy_needed
        sequence.append(count)
    return sequence

# ------------------------------------------------------------------
# Timing info
# ------------------------------------------------------------------


# Optimal timing lookup: (your_fast_turns, their_fast_turns) -> (start, step) or None
# None means timing doesn't matter
OPTIMAL_TIMING = {
    (1, 1): None,
    (1, 2): (1, 2),
    (1, 3): (2, 3),
    (1, 4): (3, 4),
    (1, 5): (4, 5),
    (2, 1): None,
    (2, 2): None,
    (2, 3): (1, 3),
    (2, 4): (1, 2),
    (2, 5): (2, 5),
    (3, 1): None,
    (3, 2): (1, 2),
    (3, 3): None,
    (3, 4): (1, 4),
    (3, 5): (3, 5),
    (4, 1): None,
    (4, 2): None,
    (4, 3): (2, 3),
    (4, 4): None,
    (4, 5): (1, 5),
    (5, 1): None,
    (5, 2): (1, 2),
    (5, 3): (1, 3),
    (5, 4): (3, None),
    (5, 5): None,
}

# All distinct patterns for use as wrong answers
ALL_TIMING_PATTERNS = [
    (1, 2),      # 1, 3, 5, 7, ...
    (1, 3),      # 1, 4, 7, 10, ...
    (1, 4),      # 1, 5, 9, 13, ...
    (1, 5),      # 1, 6, ...
    (2, 3),      # 2, 5, 8, ...
    (2, 5),      # 2, 7, 12, ...
    (3, 4),      # 3, 7, 11, ...
    (4, 5),      # 4, 9, 14, ...
    (3, None),   # 3, ...
    None,        # timing doesn't matter
]


def format_timing_pattern(pattern, num_terms=4):
    """Format a (start, step) timing pattern as a display string."""
    if pattern is None:
        return "Timing doesn't matter"
    start, step = pattern
    if step is None:
        return f"{start}, ..."
    terms = [start + i * step for i in range(num_terms)]
    return ", ".join(str(t) for t in terms) + ", ..."


def get_fast_moves_for_ranked_mons(rankings_by_league):
    """Return set of fast move IDs that appear on ranked mons across all leagues."""
    move_ids = set()
    for mons in rankings_by_league:
        for mon in mons:
            if mon.get('moveset'):
                move_ids.add(mon['moveset'][0])
    return move_ids
