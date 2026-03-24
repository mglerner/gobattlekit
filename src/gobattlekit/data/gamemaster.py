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
