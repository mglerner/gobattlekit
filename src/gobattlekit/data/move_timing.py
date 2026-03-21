#!/usr/bin/env python

import math

def counters_to_charge(fast_move: dict, charge_move: dict) -> int:
    """
    How many fast moves to fully charge a charge move?
    energyDelta on fast moves is positive (energy gained).
    energy on charge moves is negative (energy cost) in pvpoke data.
    """
    energy_per_fast = fast_move["energyDelta"]
    energy_needed = abs(charge_move["energy"])
    return math.ceil(energy_needed / energy_per_fast)
