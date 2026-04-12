"""Tests for gobattlekit.data.gamemaster — energy calculations, charge sequences, timing."""
import math
import pytest

from gobattlekit.data.gamemaster import (
    get_moves,
    counters_to_charge,
    charge_sequence,
    format_timing_pattern,
    OPTIMAL_TIMING,
    ALL_TIMING_PATTERNS,
)


# ── get_moves ─────────────────────────────────────────────────────


class TestGetMoves:
    def test_separates_fast_and_charged(self):
        fast, charged = get_moves()
        # Fast moves have energyGain != 0
        for m in fast.values():
            assert m['energyGain'] != 0
        # Charged moves have energyGain == 0
        for m in charged.values():
            assert m['energyGain'] == 0

    def test_no_overlap(self):
        fast, charged = get_moves()
        assert set(fast.keys()).isdisjoint(set(charged.keys()))

    def test_known_fast_move(self):
        fast, _ = get_moves()
        assert 'BUBBLE' in fast
        assert fast['BUBBLE']['energyGain'] == 11

    def test_known_charged_move(self):
        _, charged = get_moves()
        assert 'ICE_BEAM' in charged
        assert charged['ICE_BEAM']['energy'] == 55


# ── counters_to_charge ────────────────────────────────────────────


class TestCountersToCharge:
    def test_bubble_ice_beam(self):
        fast, charged = get_moves()
        # Ice Beam costs 55 energy, Bubble gives 11 per use → ceil(55/11) = 5
        result = counters_to_charge('BUBBLE', 'ICE_BEAM', fast, charged)
        assert result == 5

    def test_lock_on_focus_blast(self):
        fast, charged = get_moves()
        # Focus Blast costs 75, Lock-On gives 5 → ceil(75/5) = 15
        result = counters_to_charge('LOCK_ON', 'FOCUS_BLAST', fast, charged)
        assert result == 15

    def test_returns_more_when_over_20(self):
        fast, charged = get_moves()
        # Zap Cannon costs 80, Lock-On gives 5 → ceil(80/5) = 16, still ≤ 20
        result = counters_to_charge('LOCK_ON', 'ZAP_CANNON', fast, charged)
        assert result == 16  # exactly 16, not 'more'

    def test_returns_more_for_very_expensive(self):
        """Synthesize a scenario where result > 20."""
        fast = {'SLOW': {'energyGain': 3}}
        charged = {'EXPENSIVE': {'energy': 100}}
        result = counters_to_charge('SLOW', 'EXPENSIVE', fast, charged)
        assert result == 'more'  # ceil(100/3) = 34 > 20

    def test_unknown_fast_move_raises(self):
        fast, charged = get_moves()
        with pytest.raises(KeyError, match="Fast move not found"):
            counters_to_charge('NONEXISTENT', 'ICE_BEAM', fast, charged)

    def test_unknown_charged_move_raises(self):
        fast, charged = get_moves()
        with pytest.raises(KeyError, match="Charged move not found"):
            counters_to_charge('BUBBLE', 'NONEXISTENT', fast, charged)

    def test_exact_division(self):
        """When energy divides evenly, no rounding needed."""
        fast = {'EXACT': {'energyGain': 10}}
        charged = {'EVEN': {'energy': 50}}
        assert counters_to_charge('EXACT', 'EVEN', fast, charged) == 5


# ── charge_sequence ───────────────────────────────────────────────


class TestChargeSequence:
    def test_bubble_ice_beam_sequence(self):
        fast, charged = get_moves()
        seq = charge_sequence('BUBBLE', 'ICE_BEAM', fast, charged, num_charges=4)
        assert len(seq) == 4
        assert all(isinstance(n, int) for n in seq)
        # First charge should be 5 (ceil(55/11))
        assert seq[0] == 5

    def test_energy_carryover(self):
        """With carryover, later charges may need fewer fast moves."""
        fast, charged = get_moves()
        seq = charge_sequence('BUBBLE', 'ICE_BEAM', fast, charged, num_charges=4)
        # 5 Bubbles = 55 energy, Ice Beam costs 55 → 0 leftover
        # So every charge needs 5 (no carryover in this case)
        assert seq == [5, 5, 5, 5]

    def test_carryover_with_remainder(self):
        """When energy doesn't divide evenly, carryover should reduce later counts."""
        fast, charged = get_moves()
        # Play Rough costs 60, Bubble gives 11
        # ceil(60/11)=6, 6*11=66, leftover=6
        # ceil((60-6)/11)=ceil(54/11)=5, 5*11=55, leftover=55+6-60=1
        # ceil((60-1)/11)=ceil(59/11)=6, 6*11=66, leftover=66+1-60=7
        # ceil((60-7)/11)=ceil(53/11)=5, 5*11=55, leftover=55+7-60=2
        seq = charge_sequence('BUBBLE', 'PLAY_ROUGH', fast, charged, num_charges=4)
        assert seq == [6, 5, 6, 5]

    def test_total_energy_correct(self):
        """Total fast moves × energy_per_fast should cover num_charges × energy_needed."""
        fast, charged = get_moves()
        seq = charge_sequence('MUD_SHOT', 'ICE_BEAM', fast, charged, num_charges=6)
        total_fast = sum(seq)
        total_energy_generated = total_fast * 9  # Mud Shot gives 9
        total_energy_needed = 6 * 55  # 6 Ice Beams at 55 each
        assert total_energy_generated >= total_energy_needed
        # Shouldn't overshoot by more than one fast move worth of energy
        assert total_energy_generated - total_energy_needed < 9

    def test_single_charge(self):
        fast, charged = get_moves()
        seq = charge_sequence('BUBBLE', 'ICE_BEAM', fast, charged, num_charges=1)
        assert seq == [5]

    def test_unknown_fast_move_raises(self):
        fast, charged = get_moves()
        with pytest.raises(KeyError, match="Fast move not found"):
            charge_sequence('NONEXISTENT', 'ICE_BEAM', fast, charged)

    def test_unknown_charged_move_raises(self):
        fast, charged = get_moves()
        with pytest.raises(KeyError, match="Charged move not found"):
            charge_sequence('BUBBLE', 'NONEXISTENT', fast, charged)


# ── format_timing_pattern ─────────────────────────────────────────


class TestFormatTimingPattern:
    def test_none_pattern(self):
        assert format_timing_pattern(None) == "Timing doesn't matter"

    def test_simple_pattern(self):
        result = format_timing_pattern((1, 2), num_terms=4)
        assert result == "1, 3, 5, 7, ..."

    def test_different_num_terms(self):
        result = format_timing_pattern((2, 3), num_terms=3)
        assert result == "2, 5, 8, ..."

    def test_all_patterns_format(self):
        """Every pattern in ALL_TIMING_PATTERNS should format without error."""
        for pattern in ALL_TIMING_PATTERNS:
            result = format_timing_pattern(pattern)
            assert isinstance(result, str)
            assert len(result) > 0


# ── OPTIMAL_TIMING table ─────────────────────────────────────────


class TestOptimalTiming:
    def test_covers_all_1_to_5_pairs(self):
        for a in range(1, 6):
            for b in range(1, 6):
                assert (a, b) in OPTIMAL_TIMING

    def test_same_turn_count_is_none(self):
        """When both have the same fast move turns, timing doesn't matter."""
        for n in range(1, 6):
            assert OPTIMAL_TIMING[(n, n)] is None

    def test_all_values_in_patterns_list(self):
        """Every value in OPTIMAL_TIMING should appear in ALL_TIMING_PATTERNS."""
        for val in OPTIMAL_TIMING.values():
            assert val in ALL_TIMING_PATTERNS

    def test_all_patterns_referenced(self):
        """Every pattern in ALL_TIMING_PATTERNS should appear in OPTIMAL_TIMING."""
        used = set()
        for val in OPTIMAL_TIMING.values():
            if val is None:
                used.add(None)
            else:
                used.add(val)
        for pattern in ALL_TIMING_PATTERNS:
            assert pattern in used, f"Pattern {pattern} never used in OPTIMAL_TIMING"
